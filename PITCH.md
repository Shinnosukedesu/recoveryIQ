# RecoveryIQ — 5-minute buildathon pitch

This is written to sound conversational. Do not memorize every line; use it as a spine and speak naturally.

## 0:00–0:35 — Start with the problem

“I want to start with a very normal business problem: a payment fails.

Most systems treat that as one generic event. They either retry everything, or send everyone the same reminder. But a timeout, insufficient funds, fraud suspicion, and an active chargeback are obviously not the same situation.

That is money at risk, but it is also customer trust and operational risk. So I built RecoveryIQ.”

## 0:35–1:15 — Explain the product simply

“RecoveryIQ is a revenue-recovery decision agent. Its job is not just to send messages. Its job is to decide which failed payments are worth pursuing, what intervention makes sense, and when the system should stop.

For every payment, it diagnoses the failure, estimates recovery likelihood, calculates expected recovery value, and recommends one of four actions: retry, nudge, wait, or escalate.”

Show the dashboard and point to the decision queue.

## 1:15–2:05 — Show the agent making decisions

“Here is a temporary timeout for ₹29,900. The system estimates an 82% recovery likelihood, so the expected value is about ₹24,500. It recommends a retry, and the policy allows it.

Now compare that with this ₹2.5 lakh payment. The failure signal is also good, but the amount is above the automated limit. The agent recommends recovery, but the policy layer blocks execution and routes it for review.

That separation is the point: the AI can suggest, but it is not the authority.”

## 2:05–2:55 — Show safety and action

“The policy layer also stops fraud signals, chargebacks, closed accounts, repeated retries, and excessive customer contact.

For an allowed action, RecoveryIQ sends the request through a sandbox provider adapter. It requires an idempotency key, so repeating the same request does not accidentally create a second action. For a blocked action, the API returns a rejection and the payment enters human review instead.

This is intentionally safe: the sandbox adapter moves no real money.”

If showing the API, run the documented `/api/execute` example and repeat it once to show `duplicate: true`.

## 2:55–3:45 — Prove impact instead of claiming it

“I did not want this to be an AI demo where the only proof is a generated explanation. So RecoveryIQ compares itself with a naive retry-everything baseline.

In this batch, it shows revenue at risk, recovered value, recovery rate, uplift versus baseline, and safe escalations. Every decision, execution, review request, and outcome is recorded in the audit trail.

That gives a merchant the metrics that actually matter: how much revenue was recovered, what risk was prevented, and whether the strategy beats the obvious baseline.”

Point to the counterfactual and audit trail.

## 3:45–4:30 — Explain what is real and what comes next

“The current version accepts a failed-payment CSV, evaluates the batch, persists the state, accepts outcome feedback, and exposes a sandbox execution boundary.

The payment outcomes are simulated because I am not going to pretend a demo app should move live customer money. The next production step is connecting this adapter to an approved provider test account, adding authentication and role-based approvals, and calibrating the recovery model from real historical outcomes.”

## 4:30–5:00 — Close with the thesis

“So RecoveryIQ is not a generic payment reminder bot. It is a controlled revenue-recovery system.

It combines decision intelligence with business policy, bounded automation, human oversight, and measurable outcomes.

The core question it answers is simple: which failed payments should we pursue, how should we pursue them, and when should we stop?”

## One-line version if interrupted

“RecoveryIQ is an explainable revenue-recovery agent that prioritizes failed payments by expected value, applies independent safety rules, executes only bounded actions, and measures the result against a naive retry baseline.”
