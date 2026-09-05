# RecoveryIQ

> An explainable revenue-recovery control plane that decides which failed payments to pursue, how to intervene, and when to stop.

RecoveryIQ is an explainable revenue-recovery decision agent for failed payments.
It scores revenue at risk, recommends a bounded intervention, validates that recommendation against policy, simulates the outcome, and records an audit trail.

## Run locally

```powershell
python app.py
```

Then open <http://localhost:8000>.

## Import your own failed-payment data

The API accepts a CSV export using these required columns: `id`, `customer`, `amount`, and `failure`. Optional columns are `currency`, `retries`, `days`, and `email`.

```powershell
Invoke-WebRequest -Uri http://localhost:8000/api/import -Method Post -InFile .\data\sample_failed_payments.csv -ContentType text/csv
```

The latest evaluated batch is saved to `recovery_state.json` locally. Do not upload personally identifiable information to an environment that is not approved for it; use a de-identified export during development.

## Outcome and review APIs

Record what actually happened after an intervention:

```powershell
Invoke-RestMethod http://localhost:8000/api/outcome -Method Post -ContentType application/json -Body '{"payment_id":"pay_demo_2001","outcome":"RECOVERED"}'
```

Valid outcomes are `RECOVERED`, `FAILED`, and `NOT_ATTEMPTED`. Blocked decisions can be routed to a review queue without bypassing policy:

```powershell
Invoke-RestMethod http://localhost:8000/api/approval -Method Post -ContentType application/json -Body '{"payment_id":"pay_demo_2004","reason":"Risk analyst review requested"}'
```

These endpoints are pilot contracts, not production security controls yet. Before deployment, add authentication, authorization, request signing, rate limiting, encrypted storage, a real database, provider idempotency keys, and structured observability.

## Safe execution endpoint

The pilot exposes a local provider boundary with `simulation` and `sandbox` modes. It never moves money. Execution is allowed only when the policy engine returns `ALLOWED`, and every request requires an idempotency key:

```powershell
Invoke-RestMethod http://localhost:8000/api/execute -Method Post -ContentType application/json -Body '{"payment_id":"pay_demo_2002","mode":"sandbox","idempotency_key":"demo-pay-demo-2002-v1"}'
```

Repeating the same request returns the same provider result and marks it as a duplicate, demonstrating idempotent behavior. Blocked payments return `409` and cannot bypass the policy layer.

The MVP is intentionally dependency-free. It uses a synthetic batch and simulated payment outcomes so the demo is safe to run without production credentials.

## Agent loop

1. Assess each failed payment's recovery likelihood and expected recovery value.
2. Diagnose the failure and propose `RETRY`, `NUDGE`, `WAIT`, or `ESCALATE`.
3. Let the policy engine approve, block, or route the proposal for review.
4. Execute only approved bounded actions.
5. Compare RecoveryIQ with a naive retry-everything baseline and persist an audit event.

## Safety boundary

The model/decision layer never authorizes money movement by itself. The policy engine enforces retry limits, amount limits, customer-contact limits, and hard-stop failure codes. Replace `simulate_execution` with a payment-provider adapter only after adding authentication, idempotency, approval controls, and production observability.
