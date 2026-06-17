from __future__ import annotations

import unittest

from deutsch_ai_discovery.openrouter import OpenRouterClient, OpenRouterConfig
from deutsch_ai_discovery.real_model import parse_model_response, run_real_model_experiment


class FakeOpenRouterClient(OpenRouterClient):
    def __init__(self) -> None:
        super().__init__(
            OpenRouterConfig(
                api_key="test-key",
                model="test/model",
                base_url="https://example.invalid/api/v1",
            )
        )
        self.last_messages: list[dict[str, str]] = []

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.2) -> str:
        self.last_messages = messages
        user_prompt = messages[-1]["content"]
        holdout_cases = _extract_cases(user_prompt, "Holdout cases:", "Transfer cases:")
        transfer_cases = _extract_cases(user_prompt, "Transfer cases:", "Return JSON")
        return (
            "{"
            '"title":"fake explanation",'
            '"causal_terms":["factor_a"],'
            '"explanation":"A fake model response for tests.",'
            '"falsifier":"A failed prediction.",'
            '"arbitrary_clauses":1,'
            f'"holdout_predictions":{_prediction_json(holdout_cases)},'
            f'"transfer_predictions":{_prediction_json(transfer_cases)}'
            "}"
        )


class RealModelTests(unittest.TestCase):
    def test_parse_model_response_accepts_json_object(self) -> None:
        parsed = parse_model_response('{"title":"x","holdout_predictions":{}}')

        self.assertEqual(parsed["title"], "x")

    def test_real_model_experiment_scores_fake_client(self) -> None:
        client = FakeOpenRouterClient()

        result = run_real_model_experiment(
            client=client,
            seed=17,
            public_count=6,
            holdout_count=4,
            opaque_public=True,
        )

        self.assertEqual(result["model"], "test/model")
        self.assertIn("Public observations", client.last_messages[-1]["content"])
        self.assertGreaterEqual(result["truth_score"], 0.0)
        self.assertLessEqual(result["truth_score"], 1.0)


def _extract_cases(prompt: str, start: str, end: str) -> list[str]:
    section = prompt.split(start, 1)[1].split(end, 1)[0]
    return [line.strip() for line in section.splitlines() if line.strip()]


def _prediction_json(cases: list[str]) -> str:
    entries = ",".join(f"{case!r}:\"sleep\"" for case in cases)
    return "{" + entries.replace("'", '"') + "}"


if __name__ == "__main__":
    unittest.main()
