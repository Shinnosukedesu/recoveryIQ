# Resume-ready project description

## One-line version

Built RecoveryIQ, an explainable revenue-recovery decision agent that prioritizes failed payments by expected recovery value, applies independent financial guardrails, simulates bounded interventions, and logs auditable outcomes.

## Strong bullets

- Designed an end-to-end recovery workflow for failed payments: failure diagnosis → recovery likelihood → expected value → bounded action → policy validation → audit event.
- Implemented a policy layer independent of the AI recommendation layer, enforcing retry limits, amount limits, customer-contact limits, and hard-stop escalation for fraud, disputes, and closed accounts.
- Added a counterfactual evaluation comparing agent-guided recovery against a naive retry-everything baseline, exposing recovered INR, recovery rate, uplift, and safe escalations.
- Built a CSV ingestion and persistence path for historical payment exports, creating a foundation for outcome-based model calibration instead of demo-only prompting.

## Honest technology line

Python, dependency-free HTTP service, HTML/CSS/JavaScript dashboard, CSV ingestion, deterministic evaluation harness, policy engine, audit trail, synthetic/de-identified payment data.
