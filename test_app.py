import unittest

from app import POLICY, evaluate, refresh_metrics, seed_transactions


class RecoveryIQTests(unittest.TestCase):
    def setUp(self):
        self.state = evaluate(seed_transactions())

    def test_hard_stop_codes_are_never_automated(self):
        rows = {row["failure"]: row for row in self.state["transactions"]}
        self.assertEqual(rows["fraud_suspected"]["policy"], "BLOCKED")
        self.assertEqual(rows["chargeback"]["policy"], "BLOCKED")
        self.assertEqual(rows["fraud_suspected"]["action"], "ESCALATE")

    def test_retry_limit_and_amount_limit_are_enforced(self):
        rows = {row["id"]: row for row in self.state["transactions"]}
        self.assertIn("retry limit reached", rows["pay_1003"]["policy_reason"])
        self.assertIn("amount exceeds automated limit", rows["pay_1003"]["policy_reason"])
        self.assertEqual(rows["pay_1003"]["policy"], "BLOCKED")

    def test_metrics_include_action_mix_and_recoverable_value(self):
        metrics = self.state["metrics"]
        self.assertEqual(metrics["at_risk"], sum(row["amount"] for row in self.state["transactions"]))
        self.assertIn("potentially_recoverable", metrics)
        self.assertEqual(sum(metrics["action_counts"].values()), len(self.state["transactions"]))

    def test_outcome_feedback_refreshes_recovered_value(self):
        row = self.state["transactions"][0]
        row["outcome"] = "RECOVERED"
        refreshed = refresh_metrics(self.state)
        expected = sum(item["amount"] for item in self.state["transactions"] if item["outcome"] == "RECOVERED")
        self.assertEqual(refreshed["metrics"]["recovered"], expected)

    def test_policy_constants_are_explicit(self):
        self.assertEqual(POLICY["max_retries"], 2)
        self.assertIn("chargeback", POLICY["hard_stop_codes"])


if __name__ == "__main__":
    unittest.main()
