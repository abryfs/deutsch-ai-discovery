from __future__ import annotations

import argparse
import json
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any

from .gemini import GeminiClient, GeminiConfig
from .models import Explanation, WorldCase, observations_as_table
from .openrouter import OpenRouterClient, OpenRouterConfig
from .scoring import accuracy
from .world import HiddenWorld, OUTCOMES


def run_real_model_experiment(
    client: OpenRouterClient | GeminiClient,
    seed: int,
    public_count: int,
    holdout_count: int,
    opaque_public: bool,
) -> dict[str, object]:
    world = HiddenWorld.generate(seed)
    public_cases, holdout_cases, transfer_cases, _experiment_cases = world.partition_cases(
        public_count=public_count,
        holdout_count=holdout_count,
        transfer_count=holdout_count,
        seed=seed + 1,
    )
    public_observations = [world.observe(case) for case in public_cases]
    transfer_world = world.transfer_world()

    holdout_truth = {case: world.outcome(case) for case in holdout_cases}
    transfer_truth = {case: transfer_world.outcome(case) for case in transfer_cases}
    messages = _build_messages(
        public_table=observations_as_table(public_observations, opaque=opaque_public),
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
    explanation = Explanation(
        agent=client.config.model,
        title=str(parsed.get("title", "model explanation")),
        causal_terms=tuple(str(term) for term in parsed.get("causal_terms", [])),
        text=str(parsed.get("explanation", "")),
        falsifier=str(parsed.get("falsifier", "")),
        arbitrary_clauses=_coerce_int(parsed.get("arbitrary_clauses", 0)),
    )

    return {
        "seed": seed,
        "model": client.config.model,
        "base_url": client.config.base_url,
        "public_observations": public_observations,
        "holdout_truth": holdout_truth,
        "transfer_truth": transfer_truth,
        "holdout_predictions": holdout_predictions,
        "transfer_predictions": transfer_predictions,
        "holdout_accuracy": accuracy(holdout_predictions, holdout_truth),
        "transfer_reach": accuracy(transfer_predictions, transfer_truth),
        "truth_score": (
            accuracy(holdout_predictions, holdout_truth) * 0.65
            + accuracy(transfer_predictions, transfer_truth) * 0.35
        ),
        "explanation": explanation,
        "messages": messages,
        "raw_response": raw_response,
        "parsed_response": parsed,
        "hidden_config": world.reveal_config(),
    }


def parse_model_response(raw_response: str) -> dict[str, Any]:
    text = raw_response.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Model response was not valid JSON: {raw_response}") from error
    if not isinstance(parsed, dict):
        raise RuntimeError(f"Model response must be a JSON object: {raw_response}")
    return parsed


def write_real_model_report(result: dict[str, object], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_model = str(result["model"]).replace("/", "_").replace(":", "_")
    stem = f"real_model_seed_{result['seed']}_{safe_model}"
    markdown_path = output_dir / f"{stem}.md"
    json_path = output_dir / f"{stem}.json"
    markdown_path.write_text(render_real_model_markdown(result), encoding="utf-8")
    json_path.write_text(json.dumps(_jsonable(result), indent=2), encoding="utf-8")
    return markdown_path, json_path


def render_real_model_markdown(result: dict[str, object]) -> str:
    lines = [
        "# Real Model Discovery Run",
        "",
        f"Model: `{result['model']}`",
        f"Seed: `{result['seed']}`",
        f"Truth score: `{result['truth_score']:.3f}`",
        f"Holdout accuracy: `{result['holdout_accuracy']:.3f}`",
        f"Transfer reach: `{result['transfer_reach']:.3f}`",
        "",
        "## Explanation",
        "",
        f"Title: **{result['explanation'].title}**",
        "",
        result["explanation"].text or "(empty)",
        "",
        f"Falsifier: {result['explanation'].falsifier or '(empty)'}",
        "",
        "## Hidden World Revealed",
        "",
        f"`{result['hidden_config']}`",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a real model on one hidden world.")
    parser.add_argument("--provider", choices=("openrouter", "gemini"), default="openrouter")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--public-count", type=int, default=10)
    parser.add_argument("--holdout-count", type=int, default=40)
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--opaque-public", action="store_true")
    args = parser.parse_args(argv)

    client = _client_from_provider(args.provider)
    result = run_real_model_experiment(
        client=client,
        seed=args.seed,
        public_count=args.public_count,
        holdout_count=args.holdout_count,
        opaque_public=args.opaque_public,
    )
    markdown_path, json_path = write_real_model_report(result, args.output_dir)
    print(f"Real model run complete: truth={result['truth_score']:.3f}")
    print(f"Report: {markdown_path}")
    print(f"Transcript: {json_path}")
    return 0


def _client_from_provider(provider: str) -> OpenRouterClient | GeminiClient:
    if provider == "gemini":
        return GeminiClient(GeminiConfig.from_env())
    return OpenRouterClient(OpenRouterConfig.from_env())


def _build_messages(
    public_table: str,
    holdout_cases: list[WorldCase],
    transfer_cases: list[WorldCase],
    opaque_public: bool,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are participating in a sealed discovery benchmark. "
                "Infer a causal explanation from observations, then predict hidden cases. "
                "Return only valid JSON."
            ),
        },
        {
            "role": "user",
            "content": (
                "Public observations:\n"
                f"{public_table}\n\n"
                "Allowed outcomes: "
                f"{', '.join(OUTCOMES)}.\n\n"
                "Predict each holdout and transfer case. Use the exact case strings as keys.\n\n"
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
    return "\n".join(case.opaque_key() if opaque_public else case.public_key() for case in cases)


def _predictions_from_response(
    raw_predictions: object,
    cases: list[WorldCase],
    opaque_only: bool = False,
) -> dict[WorldCase, str]:
    if not isinstance(raw_predictions, dict):
        return {}
    by_public_key = {case.public_key(): case for case in cases}
    by_opaque_key = {case.opaque_key(): case for case in cases}
    predictions: dict[WorldCase, str] = {}
    for raw_case, raw_outcome in raw_predictions.items():
        case = by_opaque_key.get(str(raw_case))
        if case is None and not opaque_only:
            case = by_public_key.get(str(raw_case))
        outcome = str(raw_outcome)
        if case is not None and outcome in OUTCOMES:
            predictions[case] = outcome
    return predictions


def _coerce_int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


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
