"""Safe payment-provider boundary for the RecoveryIQ pilot.

The sandbox adapter is intentionally local and deterministic. A real provider
adapter can implement the same interface later without changing policy logic.
"""


class SandboxPaymentProvider:
    def __init__(self):
        self._idempotent_results = {}

    def execute(self, payment, action, idempotency_key, mode="sandbox"):
        if idempotency_key in self._idempotent_results:
            result = dict(self._idempotent_results[idempotency_key])
            result["duplicate"] = True
            return result
        result = {
            "provider": "recoveryiq-sandbox",
            "mode": mode,
            "payment_id": payment["id"],
            "action": action,
            "idempotency_key": idempotency_key,
            "status": "ACCEPTED",
            "message": "Action accepted by the local sandbox adapter; no money moved.",
            "duplicate": False,
        }
        self._idempotent_results[idempotency_key] = result
        return result


PROVIDER = SandboxPaymentProvider()
