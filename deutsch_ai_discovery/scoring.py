from __future__ import annotations

from collections.abc import Mapping, Sequence

from .models import AgentRun, Observation, Outcome, ScoreCard, WorldCase


def accuracy(predictions: Mapping[WorldCase, Outcome], truth: Mapping[WorldCase, Outcome]) -> float:
    if not truth:
        return 0.0
    correct = sum(1 for case, outcome in truth.items() if predictions.get(case) == outcome)
    return correct / len(truth)


def rubric_card(
    run: AgentRun,
    holdout_truth: Mapping[WorldCase, Outcome],
    transfer_truth: Mapping[WorldCase, Outcome],
    transfer_predictions: Mapping[WorldCase, Outcome],
    initial_predictions: Mapping[WorldCase, Outcome],
) -> ScoreCard:
    """Translate Deutsch-style explanation criteria into auditable proxies.

    The score is not a claim that explanation quality is fully quantified.
    It is a pressure test: a good run should make better hidden predictions,
    expose better opportunities for criticism, and improve after failed tests.
    """

    final_accuracy = accuracy(run.predictions, holdout_truth)
    initial_accuracy = accuracy(initial_predictions, holdout_truth)
    hard_to_vary = run.final.hard_to_vary_proxy()
    reach = accuracy(transfer_predictions, transfer_truth)
    criticizability = _criticizability(run.critiques, run.final.decisive_tests)
    error_correction = max(0.0, final_accuracy - initial_accuracy)
    explanation_score = (
        hard_to_vary * 0.40
        + criticizability * 0.35
        + error_correction * 0.25
    )
    total = (final_accuracy * 0.65) + (reach * 0.35)
    return ScoreCard(
        agent=run.agent,
        prediction_accuracy=final_accuracy,
        hard_to_vary=hard_to_vary,
        reach=reach,
        criticizability=criticizability,
        error_correction=error_correction,
        explanation_score=explanation_score,
        total=total,
    )


def _criticizability(critiques: Sequence[str], tests: Sequence[WorldCase]) -> float:
    critique_score = min(1.0, len([c for c in critiques if c.strip()]) / 3)
    test_score = min(1.0, len(tests) / 4)
    return round((critique_score + test_score) / 2, 3)


def truth_map(observations: Sequence[Observation]) -> dict[WorldCase, Outcome]:
    return {observation.case: observation.outcome for observation in observations}
