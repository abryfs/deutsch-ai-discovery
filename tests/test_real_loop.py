from __future__ import annotations

import json
import unittest

from deutsch_ai_discovery.openrouter import OpenRouterClient, OpenRouterConfig
from deutsch_ai_discovery.real_loop import _annotate_deltas, _trajectory_summary, run_real_loop_experiment


class FakeLoopClient(OpenRouterClient):
    def __init__(self) -> None:
        super().__init__(
            OpenRouterConfig(
                api_key="test-key",
                model="test/model",
                base_url="https://example.invalid/api/v1",
            )
        )
        self.calls: list[list[dict[str, str]]] = []

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.2) -> str:
        self.calls.append(messages)
        prompt = messages[-1]["content"]
        if "Experimentable cases:" in prompt:
            requested = _first_case_after(prompt, "Experimentable cases:")
            return json.dumps(
                {
                    "title": "test hypothesis",
                    "causal_terms": ["factor_a"],
                    "explanation": "Requesting the first allowed case.",
                    "requested_test_case": requested,
                    "test_rationale": "It is allowed and risky enough for this fake client.",
                }
            )
        holdout_cases = _cases_between(prompt, "Holdout cases:", "Transfer cases:")
        transfer_cases = _cases_between(prompt, "Transfer cases:", "Return JSON")
        return json.dumps(
            {
                "title": "final fake hypothesis",
                "causal_terms": ["factor_a"],
                "explanation": "Predict sleep everywhere.",
                "falsifier": "Any non-sleep case.",
                "arbitrary_clauses": 1,
                "holdout_predictions": {case: "sleep" for case in holdout_cases},
                "transfer_predictions": {case: "sleep" for case in transfer_cases},
            }
        )


class RealLoopTests(unittest.TestCase):
    def test_real_loop_acquires_only_experiment_observations(self) -> None:
        client = FakeLoopClient()
        result = run_real_loop_experiment(
            client=client,
            seed=17,
            public_count=6,
            holdout_count=4,
            rounds=2,
            opaque_public=True,
        )

        scored = set(result["holdout_truth"]) | set(result["transfer_truth"])
        acquired = {observation.case for observation in result["acquired_observations"]}

        self.assertEqual(len(result["loop_steps"]), 2)
        self.assertEqual(len(result["trajectory"]), 3)
        self.assertEqual(result["trajectory"][0]["label"], "initial")
        self.assertEqual([item["observation_count"] for item in result["trajectory"]], [6, 7, 8])
        self.assertIn("total_delta", result["trajectory_summary"])
        self.assertFalse(scored & acquired)
        self.assertGreaterEqual(result["truth_score"], 0.0)
        self.assertLessEqual(result["truth_score"], 1.0)
        self.assertEqual(result["truth_score"], result["trajectory_summary"]["final_score"])
        self.assertEqual(result["holdout_predictions"], result["trajectory"][-1]["holdout_predictions"])
        self.assertEqual(result["transfer_predictions"], result["trajectory"][-1]["transfer_predictions"])

        prediction_prompts = [call[-1]["content"] for call in client.calls if "Holdout cases:" in call[-1]["content"]]
        test_prompts = [call[-1]["content"] for call in client.calls if "Experimentable cases:" in call[-1]["content"]]
        self.assertEqual(len(prediction_prompts), 3)
        self.assertEqual(len(test_prompts), 2)
        for prompt in test_prompts:
            self.assertNotIn("Holdout cases:", prompt)
            self.assertNotIn("Transfer cases:", prompt)
            self.assertNotIn("truth score", prompt.lower())
            self.assertNotIn("delta", prompt.lower())
            self.assertNotIn("Freyja", prompt)
            self.assertNotIn("fjord", prompt)
            self.assertNotIn("necklace", prompt)
        for prompt in prediction_prompts:
            self.assertIn("Holdout cases:", prompt)
            self.assertIn("Transfer cases:", prompt)
            self.assertNotIn("Experimentable cases:", prompt)
            self.assertNotIn("Freyja", prompt)
            self.assertNotIn("fjord", prompt)
            self.assertNotIn("necklace", prompt)

    def test_trajectory_summary_semantics(self) -> None:
        trajectory = [
            {"truth_score": 0.20},
            {"truth_score": 0.35},
            {"truth_score": 0.40},
            {"truth_score": 0.30},
            {"truth_score": 0.45},
        ]
        _annotate_deltas(trajectory)

        summary = _trajectory_summary(trajectory)

        self.assertEqual(summary["initial_score"], 0.20)
        self.assertEqual(summary["final_score"], 0.45)
        self.assertEqual(summary["best_score"], 0.45)
        self.assertAlmostEqual(summary["total_delta"], 0.25)
        self.assertTrue(summary["improved_over_initial"])
        self.assertEqual(summary["sustained_improvement_count"], 3)
        self.assertEqual(summary["max_consecutive_positive_deltas"], 2)
        self.assertEqual(summary["regression_count"], 1)
        self.assertFalse(summary["monotonic_non_decreasing"])


def _first_case_after(prompt: str, marker: str) -> str:
    return _cases_between(prompt, marker, "Return JSON")[0]


def _cases_between(prompt: str, start: str, end: str) -> list[str]:
    section = prompt.split(start, 1)[1].split(end, 1)[0]
    return [line.strip() for line in section.splitlines() if line.strip()]


if __name__ == "__main__":
    unittest.main()
