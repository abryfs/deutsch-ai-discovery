from __future__ import annotations

import json
import unittest

from deutsch_ai_discovery.openrouter import OpenRouterClient, OpenRouterConfig
from deutsch_ai_discovery.real_loop import run_real_loop_experiment


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
        result = run_real_loop_experiment(
            client=FakeLoopClient(),
            seed=17,
            public_count=6,
            holdout_count=4,
            rounds=2,
            opaque_public=True,
        )

        scored = set(result["holdout_truth"]) | set(result["transfer_truth"])
        acquired = {observation.case for observation in result["acquired_observations"]}

        self.assertEqual(len(result["loop_steps"]), 2)
        self.assertFalse(scored & acquired)
        self.assertGreaterEqual(result["truth_score"], 0.0)
        self.assertLessEqual(result["truth_score"], 1.0)


def _first_case_after(prompt: str, marker: str) -> str:
    return _cases_between(prompt, marker, "Return JSON")[0]


def _cases_between(prompt: str, start: str, end: str) -> list[str]:
    section = prompt.split(start, 1)[1].split(end, 1)[0]
    return [line.strip() for line in section.splitlines() if line.strip()]


if __name__ == "__main__":
    unittest.main()
