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
    holdout_truth = {case: world.outcome(case) for case in holdout_cases}
    transfer_truth = {case: transfer_world.outcome(case) for case in transfer_cases}
    loop_steps: list[dict[str, object]] = []
    trajectory: list[dict[str, object]] = [
        _score_snapshot(
            client=client,
            observations=observations,
            holdout_cases=holdout_cases,
            transfer_cases=transfer_cases,
            holdout_truth=holdout_truth,
            transfer_truth=transfer_truth,
            opaque_public=opaque_public,
            round_index=0,
            label="initial",
        )
    ]

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
        # Diagnostic scoring must never feed predictions, scores, or holdout cases
        # back into later oracle-test prompts.
        trajectory.append(
            _score_snapshot(
                client=client,
                observations=observations,
                holdout_cases=holdout_cases,
                transfer_cases=transfer_cases,
                holdout_truth=holdout_truth,
                transfer_truth=transfer_truth,
                opaque_public=opaque_public,
                round_index=round_index,
                label=f"after round {round_index}",
            )
        )

    _annotate_deltas(trajectory)
    final_snapshot = trajectory[-1]
    explanation = final_snapshot["explanation"]

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
        "holdout_predictions": final_snapshot["holdout_predictions"],
        "transfer_predictions": final_snapshot["transfer_predictions"],
        "holdout_accuracy": final_snapshot["holdout_accuracy"],
        "transfer_reach": final_snapshot["transfer_reach"],
        "truth_score": final_snapshot["truth_score"],
        "explanation": explanation,
        "loop_steps": loop_steps,
        "trajectory": trajectory,
        "trajectory_summary": _trajectory_summary(trajectory),
        "final_messages": final_snapshot["messages"],
        "raw_final_response": final_snapshot["raw_response"],
        "parsed_final_response": final_snapshot["parsed_response"],
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
        "## Score Trajectory",
        "",
        "round | label | truth | holdout | transfer | delta",
        "---: | --- | ---: | ---: | ---: | ---:",
    ]
    for item in result["trajectory"]:
        delta = item.get("delta_from_previous")
        delta_text = "" if delta is None else f"{delta:.3f}"
        lines.append(
            f"{item['round']} | {item['label']} | {item['truth_score']:.3f} | "
            f"{item['holdout_accuracy']:.3f} | {item['transfer_reach']:.3f} | {delta_text}"
        )
    summary = result["trajectory_summary"]
    lines.extend(
        [
            "",
            f"Initial to final delta: `{summary['total_delta']:.3f}`",
            f"Best truth score: `{summary['best_score']:.3f}` diagnostic only",
            f"Positive delta steps: `{summary['sustained_improvement_count']}`",
            f"Max consecutive positive deltas: `{summary['max_consecutive_positive_deltas']}`",
            f"Regression steps: `{summary['regression_count']}`",
            "",
            "The headline score is the final row, not the best intermediate row.",
            "",
            "## Oracle Loop",
            "",
        ]
    )
    for step in result["loop_steps"]:
        observation = step["oracle_observation"]
        if observation is None:
            lines.append(f"- Round {step['round']}: invalid or missing requested test; no oracle result.")
        else:
            lines.append(
                f"- Round {step['round']}: {_case_key(observation.case, True)} -> "
                f"{observation.outcome}"
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


def _score_snapshot(
    client: ModelClient,
    observations: list[Observation],
    holdout_cases: list[WorldCase],
    transfer_cases: list[WorldCase],
    holdout_truth: dict[WorldCase, str],
    transfer_truth: dict[WorldCase, str],
    opaque_public: bool,
    round_index: int,
    label: str,
) -> dict[str, object]:
    messages = _final_prediction_messages(
        observations=observations,
        holdout_cases=holdout_cases,
        transfer_cases=transfer_cases,
        opaque_public=opaque_public,
    )
    raw_response = client.chat(messages)
    parsed = parse_model_response(raw_response)
    holdout_predictions = _predictions_from_response(
        parsed.get("holdout_predictions", {}),
        holdout_cases,
        opaque_only=opaque_public,
    )
    transfer_predictions = _predictions_from_response(
        parsed.get("transfer_predictions", {}),
        transfer_cases,
        opaque_only=opaque_public,
    )
    holdout_accuracy = accuracy(holdout_predictions, holdout_truth)
    transfer_reach = accuracy(transfer_predictions, transfer_truth)
    explanation = Explanation(
        agent=client.config.model,
        title=str(parsed.get("title", "model explanation")),
        causal_terms=tuple(str(term) for term in parsed.get("causal_terms", [])),
        text=str(parsed.get("explanation", "")),
        falsifier=str(parsed.get("falsifier", "")),
        arbitrary_clauses=_coerce_int(parsed.get("arbitrary_clauses", 0)),
    )
    return {
        "round": round_index,
        "label": label,
        "observation_count": len(observations),
        "holdout_predictions": holdout_predictions,
        "transfer_predictions": transfer_predictions,
        "holdout_accuracy": holdout_accuracy,
        "transfer_reach": transfer_reach,
        "truth_score": holdout_accuracy * 0.65 + transfer_reach * 0.35,
        "explanation": explanation,
        "messages": messages,
        "raw_response": raw_response,
        "parsed_response": parsed,
    }


def _annotate_deltas(trajectory: list[dict[str, object]]) -> None:
    previous: float | None = None
    for item in trajectory:
        score = float(item["truth_score"])
        item["delta_from_previous"] = None if previous is None else score - previous
        previous = score


def _trajectory_summary(trajectory: list[dict[str, object]]) -> dict[str, object]:
    scores = [float(item["truth_score"]) for item in trajectory]
    deltas = [
        float(item["delta_from_previous"])
        for item in trajectory[1:]
        if item.get("delta_from_previous") is not None
    ]
    return {
        "initial_score": scores[0],
        "final_score": scores[-1],
        "best_score": max(scores),
        "total_delta": scores[-1] - scores[0],
        "improved_over_initial": scores[-1] > scores[0],
        "sustained_improvement_count": sum(1 for delta in deltas if delta > 0),
        "max_consecutive_positive_deltas": _max_consecutive_positive_deltas(deltas),
        "regression_count": sum(1 for delta in deltas if delta < 0),
        "monotonic_non_decreasing": all(delta >= 0 for delta in deltas),
        "deltas": deltas,
    }


def _max_consecutive_positive_deltas(deltas: list[float]) -> int:
    best = 0
    current = 0
    for delta in deltas:
        if delta > 0:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


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
    summary = result["trajectory_summary"]
    print(
        "Real loop run complete: "
        f"truth={result['truth_score']:.3f}, "
        f"delta={summary['total_delta']:.3f}, "
        f"regressions={summary['regression_count']}"
    )
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
