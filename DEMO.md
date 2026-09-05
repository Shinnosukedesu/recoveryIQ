# RecoveryIQ demo runbook

## Start

~~~powershell
python -m uvicorn app:app --reload
~~~

Open http://localhost:8000. API documentation is available at http://localhost:8000/docs.

## Reset the story

Use Reset demo before recording. This restores the deterministic seed batch.

## Five-minute flow

1. Start on the RecoveryIQ cockpit and frame the problem: failed payments are not one retry problem.
2. Point to the recovery ladder: Diagnose, Prioritize, Intervene, Verify.
3. Select a high-value allowed payment and explain its expected recovery value.
4. Open the decision cockpit and show the policy gate.
5. Execute the bounded action in simulation.
6. Record the outcome as recovered and show the metric and audit update.
7. Select a blocked case with a hard-stop or amount-limit reason.
8. Show that the AI recommendation cannot bypass policy.
9. Request human review and show the escalation event.
10. Finish with the measurable result: evaluated batch, recovered value, potentially recoverable value, safe blocks, and auditability.

## Positioning

RecoveryIQ is a revenue recovery system for failed payments. It uses failure-based scoring to recommend an action, then applies deterministic rules before any simulated execution. It does not move real money.
