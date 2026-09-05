from __future__ import annotations

import json
import csv
import io
import random
import threading
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from providers import PROVIDER

ROOT = Path(__file__).parent
STATE_FILE = ROOT / "recovery_state.json"

POLICY = {
    "max_retries": 2,
    "max_amount_inr": 100000,
    "max_nudges_per_customer": 1,
    "hard_stop_codes": {"fraud_suspected", "account_closed", "chargeback"},
}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def seed_transactions():
    return [
        {"id": "pay_1001", "customer": "Aarav Mehta", "amount": 24990, "currency": "INR", "failure": "timeout", "retries": 0, "days": 0, "email": "aarav@example.com"},
        {"id": "pay_1002", "customer": "Maya Shah", "amount": 79900, "currency": "INR", "failure": "insufficient_funds", "retries": 1, "days": 1, "email": "maya@example.com"},
        {"id": "pay_1003", "customer": "Kabir Rao", "amount": 159900, "currency": "INR", "failure": "timeout", "retries": 2, "days": 0, "email": "kabir@example.com"},
        {"id": "pay_1004", "customer": "Ira Nair", "amount": 12900, "currency": "INR", "failure": "authentication_required", "retries": 0, "days": 2, "email": "ira@example.com"},
        {"id": "pay_1005", "customer": "Rohan Das", "amount": 49900, "currency": "INR", "failure": "fraud_suspected", "retries": 0, "days": 0, "email": "rohan@example.com"},
        {"id": "pay_1006", "customer": "Zoya Khan", "amount": 34900, "currency": "INR", "failure": "network_error", "retries": 0, "days": 0, "email": "zoya@example.com"},
        {"id": "pay_1007", "customer": "Dev Iyer", "amount": 89900, "currency": "INR", "failure": "insufficient_funds", "retries": 0, "days": 4, "email": "dev@example.com"},
        {"id": "pay_1008", "customer": "Sara Joseph", "amount": 19900, "currency": "INR", "failure": "chargeback", "retries": 0, "days": 1, "email": "sara@example.com"},
    ]


def diagnose(t):
    profiles = {
        "timeout": ("Transient infrastructure failure", "RETRY", 0.82, "Payment gateway timed out; a single delayed retry is economical."),
        "network_error": ("Transient network failure", "RETRY", 0.78, "Network error is usually recoverable with a bounded retry."),
        "insufficient_funds": ("Likely cash-flow constraint", "NUDGE", 0.48, "Ask the customer to update funding before attempting again."),
        "authentication_required": ("Customer authentication needed", "NUDGE", 0.62, "A secure payment link can prompt 3DS or card re-authentication."),
        "fraud_suspected": ("Risk signal requires investigation", "ESCALATE", 0.05, "Do not contact or retry until risk review is complete."),
        "chargeback": ("Dispute in progress", "ESCALATE", 0.02, "Stop automated recovery while a chargeback is active."),
        "account_closed": ("Account unavailable", "ESCALATE", 0.01, "Account closure is a hard stop."),
    }
    label, action, likelihood, why = profiles.get(t["failure"], ("Unknown failure", "WAIT", 0.15, "Insufficient signal; wait for more context."))
    expected = round(t["amount"] * likelihood)
    return {"diagnosis": label, "proposed_action": action, "likelihood": likelihood, "expected_value": expected, "why": why}


def validate(t, d, nudges):
    reasons = []
    if t["failure"] in POLICY["hard_stop_codes"]:
        reasons.append("hard-stop failure code")
    if t["amount"] > POLICY["max_amount_inr"]:
        reasons.append("amount exceeds automated limit")
    if d["proposed_action"] == "RETRY" and t["retries"] >= POLICY["max_retries"]:
        reasons.append("retry limit reached")
    if d["proposed_action"] == "NUDGE" and nudges.get(t["customer"], 0) >= POLICY["max_nudges_per_customer"]:
        reasons.append("customer contact limit reached")
    if reasons:
        return "BLOCKED", "ESCALATE", "; ".join(reasons)
    return "ALLOWED", d["proposed_action"], "Policy checks passed"


def evaluate(transactions):
    rng = random.Random(42)
    nudges = {}
    audit = []
    rows = []
    recovered = 0
    baseline = 0
    for t in transactions:
        d = diagnose(t)
        status, action, policy_reason = validate(t, d, nudges)
        outcome = "NOT_ATTEMPTED"
        if status == "ALLOWED":
            probability = {"RETRY": d["likelihood"], "NUDGE": d["likelihood"] * 0.82, "WAIT": 0.1}.get(action, 0)
            outcome = "RECOVERED" if rng.random() < probability else "FAILED"
            if outcome == "RECOVERED":
                recovered += t["amount"]
            if action == "NUDGE":
                nudges[t["customer"]] = nudges.get(t["customer"], 0) + 1
        # Counterfactual: one retry for every payment, with hard stops excluded.
        if t["failure"] not in POLICY["hard_stop_codes"] and t["retries"] < POLICY["max_retries"]:
            # Expected value of a naive retry-everything policy: lower efficacy,
            # but no diagnosis, prioritization, or bounded intervention choice.
            baseline += round(d["expected_value"] * 0.55)
        row = {**t, **d, "policy": status, "action": action, "policy_reason": policy_reason, "outcome": outcome, "execution_status": "NOT_EXECUTED"}
        rows.append(row)
        audit.append({"timestamp": now(), "payment_id": t["id"], "event": "DECISION", "action": action, "policy": status, "reason": f"{d['why']} {policy_reason}."})
        if outcome != "NOT_ATTEMPTED":
            audit.append({"timestamp": now(), "payment_id": t["id"], "event": "EXECUTION", "action": action, "policy": status, "reason": outcome})
    at_risk = sum(t["amount"] for t in transactions)
    return {"transactions": rows, "audit": audit, "metrics": {"at_risk": at_risk, "recovered": recovered, "baseline": baseline, "recovery_rate": round(recovered / at_risk * 100, 1), "allowed": sum(r["policy"] == "ALLOWED" for r in rows), "escalated": sum(r["action"] == "ESCALATE" for r in rows)}}


def refresh_metrics(state):
    rows = state["transactions"]
    at_risk = sum(r["amount"] for r in rows)
    recovered = sum(r["amount"] for r in rows if r["outcome"] == "RECOVERED")
    state["metrics"].update({"at_risk": at_risk, "recovered": recovered, "recovery_rate": round(recovered / at_risk * 100, 1) if at_risk else 0, "allowed": sum(r["policy"] == "ALLOWED" for r in rows), "escalated": sum(r["action"] == "ESCALATE" for r in rows)})
    return state


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return evaluate(seed_transactions())


DATA = load_state()


class Handler(BaseHTTPRequestHandler):
    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/state":
            body = json.dumps(DATA).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        if path == "/recoveryiq-mark.png":
            body = (ROOT / "recoveryiq-mark.png").read_bytes()
            self.send_response(200); self.send_header("Content-Type", "image/png"); self.send_header("Cache-Control", "no-cache"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        page = page.replace("Batch intelligence · 08 payments", f"Batch intelligence · {len(DATA['transactions']):02d} payments")
        body = page.encode("utf-8")
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_POST(self):
        global DATA
        path = urlparse(self.path).path
        if path == "/api/execute":
            try:
                size = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(size).decode("utf-8"))
                payment_id = payload.get("payment_id")
                mode = payload.get("mode", "sandbox")
                idempotency_key = payload.get("idempotency_key")
                if mode not in {"simulation", "sandbox"}:
                    self.send_json({"error": "Only simulation and sandbox modes are enabled"}, 400); return
                if not idempotency_key:
                    self.send_json({"error": "idempotency_key is required"}, 400); return
                row = next((r for r in DATA["transactions"] if r["id"] == payment_id), None)
                if not row:
                    self.send_json({"error": "Payment not found"}, 404); return
                if row["policy"] != "ALLOWED":
                    self.send_json({"error": "Policy blocked this action; route it to human review", "policy": row["policy"], "reason": row["policy_reason"]}, 409); return
                result = PROVIDER.execute(row, row["action"], idempotency_key, mode)
                row["execution_status"] = result["status"]
                DATA["audit"].append({"timestamp": now(), "payment_id": payment_id, "event": "SANDBOX_EXECUTION", "action": row["action"], "policy": row["policy"], "reason": result["message"]})
                save_state(DATA); self.send_json({"ok": True, "result": result})
            except (ValueError, json.JSONDecodeError) as exc:
                self.send_json({"error": f"Invalid execution payload: {exc}"}, 400)
            return
        if path == "/api/outcome":
            try:
                size = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(size).decode("utf-8"))
                payment_id, outcome = payload.get("payment_id"), payload.get("outcome")
                if outcome not in {"RECOVERED", "FAILED", "NOT_ATTEMPTED"}:
                    self.send_json({"error": "Outcome must be RECOVERED, FAILED, or NOT_ATTEMPTED"}, 400); return
                row = next((r for r in DATA["transactions"] if r["id"] == payment_id), None)
                if not row:
                    self.send_json({"error": "Payment not found"}, 404); return
                row["outcome"] = outcome
                DATA["audit"].append({"timestamp": now(), "payment_id": payment_id, "event": "OUTCOME_FEEDBACK", "action": row["action"], "policy": row["policy"], "reason": f"Outcome recorded: {outcome}"})
                save_state(refresh_metrics(DATA)); self.send_json({"ok": True, "payment_id": payment_id, "metrics": DATA["metrics"]})
            except (ValueError, json.JSONDecodeError) as exc:
                self.send_json({"error": f"Invalid outcome payload: {exc}"}, 400)
            return
        if path == "/api/approval":
            try:
                size = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(size).decode("utf-8"))
                payment_id = payload.get("payment_id")
                row = next((r for r in DATA["transactions"] if r["id"] == payment_id), None)
                if not row:
                    self.send_json({"error": "Payment not found"}, 404); return
                if row["policy"] != "BLOCKED":
                    self.send_json({"error": "Only blocked decisions can enter human review"}, 409); return
                row["review_status"] = "PENDING_HUMAN_REVIEW"
                DATA["audit"].append({"timestamp": now(), "payment_id": payment_id, "event": "HUMAN_REVIEW_REQUESTED", "action": row["action"], "policy": row["policy"], "reason": payload.get("reason", "Blocked decision requires review")})
                save_state(DATA); self.send_json({"ok": True, "payment_id": payment_id, "review_status": row["review_status"]})
            except (ValueError, json.JSONDecodeError) as exc:
                self.send_json({"error": f"Invalid approval payload: {exc}"}, 400)
            return
        if path != "/api/import":
            self.send_json({"error": "Not found"}, 404); return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(size).decode("utf-8-sig")
            records = list(csv.DictReader(io.StringIO(raw)))
            required = {"id", "customer", "amount", "failure"}
            missing = sorted(required - set(records[0].keys() if records else []))
            if missing:
                self.send_json({"error": "Missing required columns: " + ", ".join(missing)}, 400); return
            transactions = []
            for n, row in enumerate(records, 1):
                transactions.append({"id": row["id"].strip(), "customer": row["customer"].strip(), "amount": int(float(row["amount"])), "currency": row.get("currency", "INR").strip() or "INR", "failure": row["failure"].strip().lower(), "retries": int(row.get("retries", 0) or 0), "days": int(row.get("days", 0) or 0), "email": row.get("email", "").strip()})
            if not transactions:
                self.send_json({"error": "CSV contains no payment rows"}, 400); return
            DATA = evaluate(transactions)
            save_state(DATA)
            self.send_json({"ok": True, "rows": len(transactions), "metrics": DATA["metrics"]})
        except (ValueError, KeyError) as exc:
            self.send_json({"error": f"Invalid CSV value: {exc}"}, 400)
        except OSError as exc:
            self.send_json({"error": f"Could not save imported batch: {exc}"}, 500)
    def log_message(self, *_):
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("localhost", 8000), Handler)
    print("RecoveryIQ running at http://localhost:8000")
    threading.Timer(0.5, lambda: webbrowser.open("http://localhost:8000")).start()
    server.serve_forever()
