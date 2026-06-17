from __future__ import annotations

import argparse
import json
from dataclasses import fields, is_dataclass
from pathlib import Path

from .agents import all_agents
from .models import AgentRun, Observation, ScoreCard, WorldCase, observations_as_table
from .scoring import rubric_card
from .world import HiddenWorld


def run_experiment(seed: int, rounds: int, public_count: int, holdout_count: int) -> dict[str, object]:
    world = HiddenWorld.generate(seed)
    public_observations = world.sample_public_observations(public_count, seed + 1)
    holdout_cases, transfer_cases = world.split_holdouts(holdout_count, seed + 2)
    transfer_world = world.transfer_world()

    holdout_truth = {case: world.outcome(case) for case in holdout_cases}
    transfer_truth = {case: transfer_world.outcome(case) for case in transfer_cases}

    runs: list[AgentRun] = []
    scores: list[ScoreCard] = []
    for agent in all_agents():
        run = agent.run(world, public_observations, holdout_cases, rounds)
        transfer_predictions = agent.predictions_for(
            run.final,
            tuple(public_observations) + run.acquired_observations,
            transfer_cases,
        )
        initial_predictions = agent.predictions_for(run.initial, public_observations, holdout_cases)
        scores.append(
            rubric_card(
                run=run,
                holdout_truth=holdout_truth,
                transfer_truth=transfer_truth,
                transfer_predictions=transfer_predictions,
                initial_predictions=initial_predictions,
            )
        )
        runs.append(run)

    return {
        "seed": seed,
        "rounds": rounds,
        "public_observations": public_observations,
        "holdout_truth": holdout_truth,
        "transfer_truth": transfer_truth,
        "runs": runs,
        "scores": sorted(scores, key=lambda score: score.total, reverse=True),
        "hidden_config": world.reveal_config(),
    }


def write_report(result: dict[str, object], output_dir: Path, opaque_public: bool = False) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    seed = result["seed"]
    markdown_path = output_dir / f"report_seed_{seed}.md"
    json_path = output_dir / f"transcript_seed_{seed}.json"

    markdown_path.write_text(render_markdown_report(result, opaque_public=opaque_public), encoding="utf-8")
    json_path.write_text(json.dumps(_jsonable(result), indent=2), encoding="utf-8")
    return markdown_path, json_path


def render_markdown_report(result: dict[str, object], opaque_public: bool = False) -> str:
    public_observations = result["public_observations"]
    scores = result["scores"]
    runs = result["runs"]

    lines = [
        "# Deutsch-Style AI Discovery Report",
        "",
        f"Seed: `{result['seed']}`",
        f"Rounds: `{result['rounds']}`",
        "",
        "## Public Observations",
        "",
        observations_as_table(public_observations, opaque=opaque_public),
        "",
        "## Scoreboard",
        "",
        "agent | truth score | prediction | transfer reach | explanation score | hard-to-vary | criticizability | error-correction",
        "--- | ---: | ---: | ---: | ---: | ---: | ---: | ---:",
    ]
    for score in scores:
        lines.append(
            f"{score.agent} | {score.total:.3f} | {score.prediction_accuracy:.3f} | "
            f"{score.reach:.3f} | {score.explanation_score:.3f} | "
            f"{score.hard_to_vary:.3f} | {score.criticizability:.3f} | "
            f"{score.error_correction:.3f}"
        )

    lines.extend(["", "## Runs", ""])
    for run in runs:
        initial_title = _public_text(run.initial.title, opaque_public)
        final_title = _public_text(run.final.title, opaque_public)
        lines.extend(
            [
                f"### {run.agent}",
                "",
                f"Initial explanation: **{initial_title}**",
                "",
                _public_text(run.initial.text, opaque_public),
                "",
                f"Final explanation: **{final_title}**",
                "",
                _public_text(run.final.text, opaque_public),
                "",
                f"Falsifier: {_public_text(run.final.falsifier, opaque_public)}",
                "",
                "Critiques:",
            ]
        )
        if run.critiques:
            lines.extend(f"- {_public_text(critique, opaque_public)}" for critique in run.critiques)
        else:
            lines.append("- None")
        lines.append("")
        lines.append("Acquired observations:")
        if run.acquired_observations:
            lines.extend(
                f"- {_case_key(obs.case, opaque_public)} -> {obs.outcome}; {obs.myth}"
                for obs in run.acquired_observations
            )
        else:
            lines.append("- None")
        lines.append("")

    lines.extend(["## Holdout Predictions", ""])
    holdout_truth = result["holdout_truth"]
    for run in runs:
        lines.extend([f"### {run.agent}", "", "case | prediction | truth", "--- | --- | ---"])
        for idx, (case, truth) in enumerate(holdout_truth.items()):
            if idx >= 8:
                break
            lines.append(f"{_case_key(case, opaque_public)} | {run.predictions.get(case, 'missing')} | {truth}")
        lines.append("")

    lines.extend(
        [
            "## Hidden World Revealed",
            "",
            "The hidden configuration is revealed only after scoring, so it cannot guide the agents during the run.",
            "",
            f"`{_public_text(result['hidden_config'], opaque_public)}`",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Deutsch-style AI discovery experiment.")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--rounds", type=int, default=4)
    parser.add_argument("--public-count", type=int, default=10)
    parser.add_argument("--holdout-count", type=int, default=20)
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--opaque-public", action="store_true", help="Use non-semantic case labels in the report.")
    args = parser.parse_args(argv)

    result = run_experiment(
        seed=args.seed,
        rounds=args.rounds,
        public_count=args.public_count,
        holdout_count=args.holdout_count,
    )
    markdown_path, json_path = write_report(result, args.output_dir, opaque_public=args.opaque_public)
    print(render_console_summary(result, markdown_path, json_path))
    return 0


def render_console_summary(result: dict[str, object], markdown_path: Path, json_path: Path) -> str:
    scores = result["scores"]
    lines = [
        "Deutsch-style discovery experiment complete.",
        f"Report: {markdown_path}",
        f"Transcript: {json_path}",
        "",
        "Scores:",
    ]
    for score in scores:
        lines.append(
            f"- {score.agent}: truth={score.total:.3f}, prediction={score.prediction_accuracy:.3f}, "
            f"reach={score.reach:.3f}, explanation={score.explanation_score:.3f}"
        )
    return "\n".join(lines)


def _jsonable(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {str(_jsonable(key)): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _case_key(case: WorldCase, opaque_public: bool) -> str:
    return case.opaque_key() if opaque_public else case.public_key()


def _public_text(text: object, opaque_public: bool) -> str:
    value = str(text)
    if not opaque_public:
        return value
    replacements = {
        "realm": "factor_a",
        "north": "a0",
        "south": "a1",
        "distance": "factor_b",
        "near": "b0",
        "far": "b1",
        "moon": "factor_c",
        "dark": "c0",
        "bright": "c1",
        "wind": "factor_e",
        "still": "e0",
        "restless": "e1",
        "axis": "cycle-realm",
        "tilt": "cycle-bias",
        "orbital": "cycle-factor-b",
    }
    for before, after in replacements.items():
        value = value.replace(before, after)
    return value


if __name__ == "__main__":
    raise SystemExit(main())
