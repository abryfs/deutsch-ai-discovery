from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import fields, is_dataclass
from pathlib import Path

from .experiment import run_experiment
from .models import ScoreCard


def run_benchmark(
    start_seed: int,
    runs: int,
    rounds: int,
    public_count: int,
    holdout_count: int,
) -> dict[str, object]:
    results = [
        run_experiment(
            seed=start_seed + offset,
            rounds=rounds,
            public_count=public_count,
            holdout_count=holdout_count,
        )
        for offset in range(runs)
    ]
    return {
        "start_seed": start_seed,
        "runs": runs,
        "rounds": rounds,
        "public_count": public_count,
        "holdout_count": holdout_count,
        "summaries": [_summarize_result(result) for result in results],
        "agents": _agent_stats(results),
        "failure_cases": _failure_cases(results),
    }


def write_benchmark_report(result: dict[str, object], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    start_seed = result["start_seed"]
    runs = result["runs"]
    markdown_path = output_dir / f"benchmark_{start_seed}_{runs}.md"
    json_path = output_dir / f"benchmark_{start_seed}_{runs}.json"
    markdown_path.write_text(render_benchmark_markdown(result), encoding="utf-8")
    json_path.write_text(json.dumps(_jsonable(result), indent=2), encoding="utf-8")
    return markdown_path, json_path


def render_benchmark_markdown(result: dict[str, object]) -> str:
    lines = [
        "# Deutsch-Style AI Discovery Benchmark",
        "",
        f"Seeds: `{result['start_seed']}` through `{result['start_seed'] + result['runs'] - 1}`",
        f"Runs: `{result['runs']}`",
        f"Rounds per run: `{result['rounds']}`",
        "",
        "## Protocol Notes",
        "",
        "- Treat results as paired by seed; worlds, not cases, are the replication unit.",
        "- The primary contrast is the final Deutsch critique loop score versus matched controls.",
        "- Random and passive controls share the same hypothesis library and oracle label budget.",
        "- Explanation proxy scores are diagnostics, not evidence of Deutschian good explanations.",
        "",
        "## Aggregate Scores",
        "",
        "agent | wins | avg truth | stdev truth | avg prediction | avg transfer reach | avg explanation | avg criticizability",
        "--- | ---: | ---: | ---: | ---: | ---: | ---: | ---:",
    ]
    agents = sorted(result["agents"], key=lambda row: row["avg_total"], reverse=True)
    for row in agents:
        lines.append(
            f"{row['agent']} | {row['wins']} | {row['avg_total']:.3f} | "
            f"{row['stdev_total']:.3f} | {row['avg_prediction']:.3f} | "
            f"{row['avg_reach']:.3f} | {row['avg_explanation']:.3f} | "
            f"{row['avg_criticizability']:.3f}"
        )

    lines.extend(
        [
            "",
            "## Failure Cases",
            "",
            "A failure case is any seed where the Deutsch critique loop does not rank first.",
            "",
        ]
    )
    failures = result["failure_cases"]
    if failures:
        lines.extend(["seed | winner | Deutsch rank | Deutsch truth | winning truth", "--- | --- | ---: | ---: | ---:"])
        for failure in failures:
            lines.append(
                f"{failure['seed']} | {failure['winner']} | {failure['deutsch_rank']} | "
                f"{failure['deutsch_total']:.3f} | {failure['winning_total']:.3f}"
            )
    else:
        lines.append("No failure cases in this benchmark window.")

    lines.extend(["", "## Per-Seed Winners", "", "seed | winner | winning truth score", "--- | --- | ---:"])
    for summary in result["summaries"]:
        lines.append(f"{summary['seed']} | {summary['winner']} | {summary['winning_total']:.3f}")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run many Deutsch-style discovery experiments.")
    parser.add_argument("--start-seed", type=int, default=1)
    parser.add_argument("--runs", type=int, default=50)
    parser.add_argument("--rounds", type=int, default=4)
    parser.add_argument("--public-count", type=int, default=10)
    parser.add_argument("--holdout-count", type=int, default=40)
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    args = parser.parse_args(argv)

    result = run_benchmark(
        start_seed=args.start_seed,
        runs=args.runs,
        rounds=args.rounds,
        public_count=args.public_count,
        holdout_count=args.holdout_count,
    )
    markdown_path, json_path = write_benchmark_report(result, args.output_dir)
    print(render_console_summary(result, markdown_path, json_path))
    return 0


def render_console_summary(result: dict[str, object], markdown_path: Path, json_path: Path) -> str:
    leader = max(result["agents"], key=lambda row: row["avg_total"])
    return "\n".join(
        [
            "Deutsch-style benchmark complete.",
            f"Report: {markdown_path}",
            f"Data: {json_path}",
            f"Leader: {leader['agent']} avg_truth={leader['avg_total']:.3f} wins={leader['wins']}",
            f"Failure cases: {len(result['failure_cases'])}",
        ]
    )


def _summarize_result(result: dict[str, object]) -> dict[str, object]:
    scores = result["scores"]
    winner = scores[0]
    deutsch_rank = next(
        index + 1 for index, score in enumerate(scores) if score.agent == "Deutsch critique loop"
    )
    deutsch_total = next(score.total for score in scores if score.agent == "Deutsch critique loop")
    return {
        "seed": result["seed"],
        "winner": winner.agent,
        "winning_total": winner.total,
        "deutsch_rank": deutsch_rank,
        "deutsch_total": deutsch_total,
        "scores": scores,
    }


def _agent_stats(results: list[dict[str, object]]) -> list[dict[str, object]]:
    by_agent: dict[str, list[ScoreCard]] = {}
    wins: dict[str, int] = {}
    for result in results:
        scores = result["scores"]
        wins[scores[0].agent] = wins.get(scores[0].agent, 0) + 1
        for score in scores:
            by_agent.setdefault(score.agent, []).append(score)

    rows: list[dict[str, object]] = []
    for agent, cards in by_agent.items():
        totals = [card.total for card in cards]
        rows.append(
            {
                "agent": agent,
                "wins": wins.get(agent, 0),
                "avg_total": statistics.fmean(totals),
                "stdev_total": statistics.stdev(totals) if len(totals) > 1 else 0.0,
                "avg_prediction": statistics.fmean(card.prediction_accuracy for card in cards),
                "avg_reach": statistics.fmean(card.reach for card in cards),
                "avg_explanation": statistics.fmean(card.explanation_score for card in cards),
                "avg_criticizability": statistics.fmean(card.criticizability for card in cards),
            }
        )
    return rows


def _failure_cases(results: list[dict[str, object]]) -> list[dict[str, object]]:
    failures: list[dict[str, object]] = []
    for result in results:
        summary = _summarize_result(result)
        if summary["winner"] != "Deutsch critique loop":
            failures.append(
                {
                    "seed": summary["seed"],
                    "winner": summary["winner"],
                    "deutsch_rank": summary["deutsch_rank"],
                    "deutsch_total": summary["deutsch_total"],
                    "winning_total": summary["winning_total"],
                }
            )
    return failures


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
