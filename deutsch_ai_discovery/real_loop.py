from __future__ import annotations

import argparse
import json
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any, Union

from .gemini import GeminiClient, GeminiConfig
from .models import Explanation, Observation, WorldCase, observations_as_table
from .openrouter import OpenRouterClient, OpenRouterConfig
from .real_model import _coerce_int, _predictions_from_response, parse_model_response
from .scoring import accuracy
from .world import HiddenWorld, OUTCOMES


ModelClient = Union[OpenRouterClient, GeminiClient]


def run_real_loop_experiment(
    client: ModelClient,
    seed: int,
    public_count: int,
    holdout_count: int,
    rounds: int,
    opaque_public: bool,
) -> dict[str, object]:
    world = HiddenWorld.generate(seed)
    public_cases, holdout_cases, transfer_cases, experiment_cases = world.partition_cases(
        public_count=public_count,
        holdout_count=holdout_count,
        transfer_count=holdout_count,
        seed=seed + 1,
    )
    transfer_world = world.transfer_world()
    observations = [world.observe(case) for case in public_cases]
    available_tests = list(experiment_cases)
    loop_steps: list[dict[str, object]] = []

    for round_index in range(1, rounds + 1):
        messages = _test_request_messages(
            observations=observations,
            available_tests=available_tests,
            round_index=round_index,
            opaque_public=opaque_public,
        )
        raw_response = client.chat(messages)
        parsed = parse_model_response(raw_response)
        requested_case = _case_from_key(
            str(parsed.get("requested_test_case", "")),
            available_tests,
            opaque_public=opaque_public,
        )
        oracle_observation: Observation | None = None
        if requested_case is not None:
            oracle_observation = world.observe(requested_case)
            observations.append(oracle_observation)
            available_tests = [case for case in available_tests if case != requested_case]

        loop_steps.append(
            {
                "round": round_index,
                "messages": messages,
                "raw_response": raw_response,
                "parsed_response": parsed,
                "requested_test_case": requested_case,
                "oracle_observation": oracle_observation,
            }
        )

    final_messages = _final_prediction_messages(
        observations=observations,
        holdout_cases=holdout_cases,
        transfer_cases=transfer_cases,
        opaque_public=opaque_public,
    )
    raw_final = client.chat(final_messages)
    parsed_final = parse_model_response(raw_final)
    holdout_truth = {case: world.outcome(case) for case in holdout_cases}
    transfer_truth = {case: transfer_world.outcome(case) for case in transfer_cases}
    holdout_predictions = _predictions_from_response(
        parsed_final.get("holdout_predictions", {}),
        holdout_cases,
        opaque_only=opaque_public,
    )
    transfer_predictions = _predictions_from_response(
        parsed_final.get("transfer_predictions", {}),
        transfer_cases,
        opaque_only=opaque_public,
    )
    explanation = Explanation(
        agent=client.config.model,
        title=str(parsed_final.get("title", "model explanation")),
        causal_terms=tuple(str(term) for term in parsed_final.get("causal_terms", [])),
        text=str(parsed_final.get("explanation", "")),
        falsifier=str(parsed_final.get("falsifier", "")),
        arbitrary_clauses=_coerce_int(parsed_final.get("arbitrary_clauses", 0)),
    )
    holdout_accuracy = accuracy(holdout_predictions, holdout_truth)
    transfer_reach = accuracy(transfer_predictions, transfer_truth)

    return {
        "seed": seed,
        "model": client.config.model,
        "base_url": client.config.base_url,
        "rounds": rounds,
        "public_count": public_count,
        "holdout_count": holdout_count,
        "public_observations": [world.observe(case) for case in public_cases],
        "acquired_observations": observations[public_count:],
        "holdout_truth": holdout_truth,
        "transfer_truth": transfer_truth,
        "holdout_predictions": holdout_predictions,
        "transfer_predictions": transfer_predictions,
        "holdout_accuracy": holdout_accuracy,
        "transfer_reach": transfer_reach,
        "truth_score": holdout_accuracy * 0.65 + transfer_reach * 0.35,
        "explanation": explanation,
        "loop_steps": loop_steps,
        "final_messages": final_messages,
        "raw_final_response": raw_final,
        "parsed_final_response": parsed_final,
        "hidden_config": world.reveal_config(),
    }


def write_real_loop_report(result: dict[str, object], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_model = str(result["model"]).replace("/", "_").replace(":", "_")
    stem = f"real_loop_seed_{result['seed']}_{safe_model}"
    markdown_path = output_dir / f"{stem}.md"
    json_path = output_dir / f"{stem}.json"
    markdown_path.write_text(render_real_loop_markdown(result), encoding="utf-8")
    json_path.write_text(json.dumps(_jsonable(result), indent=2), encoding="utf-8")
    return markdown_path, json_path


def render_real_loop_markdown(result: dict[str, object]) -> str:
    lines = [
        "# Multi-Round Real Model Discovery Run",
        "",
        f"Model: `{result['model']}`",
        f"Seed: `{result['seed']}`",
        f"Rounds: `{result['rounds']}`",
        f"Truth score: `{result['truth_score']:.3f}`",
        f"Holdout accuracy: `{result['holdout_accuracy']:.3f}`",
        f"Transfer reach: `{result['transfer_reach']:.3f}`",
        "",
        "## Oracle Loop",
        "",
    ]
    for step in result["loop_steps"]:
        observation = step["oracle_observation"]
        if observation is None:
            lines.append(f"- Round {step['round']}: invalid or missing requested test; no oracle result.")
        else:
            lines.append(
                f"- Round {step['round']}: {_case_key(observation.case, True)} -> "
                f"{observation.outcome}; {observation.myth}"
            )

    explanation = result["explanation"]
    lines.extend(
        [
            "",
            "## Final Explanation",
            "",
            f"Title: **{explanation.title}**",
            "",
            explanation.text or "(empty)",
            "",
            f"Falsifier: {explanation.falsifier or '(empty)'}",
            "",
            "## Hidden World Revealed",
            "",
            f"`{result['hidden_config']}`",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a multi-round real model discovery loop.")
    parser.add_argument("--provider", choices=("openrouter", "gemini"), default="openrouter")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--public-count", type=int, default=10)
    parser.add_argument("--holdout-count", type=int, default=40)
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--opaque-public", action="store_true")
    args = parser.parse_args(argv)

    client = _client_from_provider(args.provider)
    result = run_real_loop_experiment(
        client=client,
        seed=args.seed,
        public_count=args.public_count,
        holdout_count=args.holdout_count,
        rounds=args.rounds,
        opaque_public=args.opaque_public,
    )
    markdown_path, json_path = write_real_loop_report(result, args.output_dir)
    print(f"Real loop run complete: truth={result['truth_score']:.3f}")
    print(f"Report: {markdown_path}")
    print(f"Transcript: {json_path}")
    return 0


def _client_from_provider(provider: str) -> ModelClient:
    if provider == "gemini":
        return GeminiClient(GeminiConfig.from_env())
    return OpenRouterClient(OpenRouterConfig.from_env())


def _test_request_messages(
    observations: list[Observation],
    available_tests: list[WorldCase],
    round_index: int,
    opaque_public: bool,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are running a sealed Deutsch-style discovery loop. "
                "Conjecture an explanation, then choose one risky test from the allowed list. "
                "Return only valid JSON."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Round {round_index}.\n\n"
                "Known observations:\n"
                f"{observations_as_table(observations, opaque=opaque_public)}\n\n"
                "Allowed outcomes: "
                f"{', '.join(OUTCOMES)}.\n\n"
                "Choose exactly one risky test case from this experimentable pool. "
                "Copy the full case string exactly as written. "
                "Do not ask for holdout or transfer cases.\n\n"
                "Experimentable cases:\n"
                f"{_case_lines(available_tests, opaque_public)}\n\n"
                "Return JSON with keys: title, causal_terms, explanation, requested_test_case, test_rationale."
            ),
        },
    ]


def _final_prediction_messages(
    observations: list[Observation],
    holdout_cases: list[WorldCase],
    transfer_cases: list[WorldCase],
    opaque_public: bool,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are completing a sealed discovery benchmark. "
                "Use the observations to give final predictions. Return only valid JSON."
            ),
        },
        {
            "role": "user",
            "content": (
                "All observations now known:\n"
                f"{observations_as_table(observations, opaque=opaque_public)}\n\n"
                "Allowed outcomes: "
                f"{', '.join(OUTCOMES)}.\n\n"
                "Predict each holdout and transfer case. Use exact case strings as keys.\n\n"
                "Holdout cases:\n"
                f"{_case_lines(holdout_cases, opaque_public)}\n\n"
                "Transfer cases:\n"
                f"{_case_lines(transfer_cases, opaque_public)}\n\n"
                "Return JSON with keys: title, causal_terms, explanation, falsifier, "
                "arbitrary_clauses, holdout_predictions, transfer_predictions."
            ),
        },
    ]


def _case_lines(cases: list[WorldCase], opaque_public: bool) -> str:
    return "\n".join(_case_key(case, opaque_public) for case in cases)


def _case_key(case: WorldCase, opaque_public: bool) -> str:
    return case.opaque_key() if opaque_public else case.public_key()


def _case_from_key(raw_key: str, cases: list[WorldCase], opaque_public: bool) -> WorldCase | None:
    for case in cases:
        allowed_key = case.opaque_key() if opaque_public else case.public_key()
        if raw_key == allowed_key:
            return case
    return None


def _jsonable(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {str(_jsonable(key)): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
