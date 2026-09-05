# RecoveryIQ demo script

## The 90-second story

### 0:00–0:12 — The problem

“Failed payments are not all equal. Retrying everything wastes customer trust and still misses the payments most likely to recover. RecoveryIQ is a decision agent for the revenue between failure and recovery.”

### 0:12–0:28 — The agent's job

“For every failed payment, it diagnoses the failure, estimates recovery likelihood, calculates expected recovery value, and proposes one bounded intervention: retry, nudge, wait, or escalate.”

Point to the decision queue and explain that expected value is amount multiplied by recovery likelihood.

### 0:28–0:45 — AI is not the authority

“The important design choice is that the agent does not get to authorize itself. Its recommendation passes through a separate policy layer.”

Point to the high-value timeout payment: the AI sees a strong recovery signal, but policy blocks automation because the amount and retry limit are outside the configured boundary.

### 0:45–1:02 — Safe execution

“Allowed actions are simulated with deterministic outcomes for this demo. Hard-stop signals—fraud, disputes, and closed accounts—go straight to escalation. Every decision and execution event is written to the audit trail.”

### 1:02–1:18 — Evidence of impact

“The counterfactual compares RecoveryIQ with a naive retry-everything policy. This lets us measure recovered value and uplift rather than claiming that an AI recommendation is useful.”

Point to recovered INR, recovery rate, uplift, and escalations.

### 1:18–1:30 — Why it can become real

“The app accepts a historical failed-payment CSV, persists the evaluated batch, and is designed to learn from actual outcomes. The next production step is a payment-provider sandbox adapter with idempotency and human approval for high-risk actions.”

## Demo setup

1. Start the app with `python app.py`.
2. Import `data/sample_failed_payments.csv` using the documented API command in `README.md`.
3. Refresh the browser and show the decision queue from top to bottom.
4. Spend most of the time on the blocked high-value payment, the counterfactual, and the audit trail.

## Avoid saying

- “The AI automatically recovers money” — execution is simulated in this MVP.
- “This is production-ready” — the current system needs provider integration, authentication, monitoring, consent, and security review.
- “The model is accurate” — accuracy must be measured after importing labeled historical outcomes.
