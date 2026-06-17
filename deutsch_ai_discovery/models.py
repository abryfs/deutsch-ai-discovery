from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


Outcome = str


@dataclass(frozen=True, order=True)
class WorldCase:
    """A queryable situation in the hidden world."""

    turn: int
    realm: str
    distance: str
    moon: str
    wind: str

    def public_key(self) -> str:
        return (
            f"turn={self.turn}, realm={self.realm}, distance={self.distance}, "
            f"moon={self.moon}, wind={self.wind}"
        )

    def opaque_key(self) -> str:
        realm = {"north": "r0", "south": "r1"}[self.realm]
        distance = {"near": "d0", "far": "d1"}[self.distance]
        moon = {"dark": "m0", "bright": "m1"}[self.moon]
        wind = {"still": "w0", "restless": "w1"}[self.wind]
        return f"step={self.turn}, a={realm}, b={distance}, c={moon}, e={wind}"


@dataclass(frozen=True)
class Observation:
    case: WorldCase
    outcome: Outcome
    myth: str


@dataclass(frozen=True)
class Explanation:
    agent: str
    title: str
    causal_terms: tuple[str, ...]
    text: str
    falsifier: str
    arbitrary_clauses: int
    decisive_tests: tuple[WorldCase, ...] = field(default_factory=tuple)

    def hard_to_vary_proxy(self) -> float:
        if not self.causal_terms:
            return 0.0
        parsimony = max(0.0, 1.0 - (self.arbitrary_clauses * 0.12))
        specificity = min(1.0, len(self.causal_terms) / 3)
        return round((specificity + parsimony) / 2, 3)


@dataclass(frozen=True)
class AgentRun:
    agent: str
    initial: Explanation
    final: Explanation
    acquired_observations: tuple[Observation, ...]
    critiques: tuple[str, ...]
    predictions: dict[WorldCase, Outcome]


@dataclass(frozen=True)
class ScoreCard:
    agent: str
    prediction_accuracy: float
    hard_to_vary: float
    reach: float
    criticizability: float
    error_correction: float
    explanation_score: float
    total: float

    def as_rows(self) -> list[tuple[str, str]]:
        return [
            ("prediction_accuracy", f"{self.prediction_accuracy:.3f}"),
            ("reach", f"{self.reach:.3f}"),
            ("truth_total", f"{self.total:.3f}"),
            ("hard_to_vary", f"{self.hard_to_vary:.3f}"),
            ("criticizability", f"{self.criticizability:.3f}"),
            ("error_correction", f"{self.error_correction:.3f}"),
            ("explanation_score", f"{self.explanation_score:.3f}"),
        ]


def observations_as_table(observations: Iterable[Observation], opaque: bool = False) -> str:
    lines = ["case | outcome | myth", "--- | --- | ---"]
    for observation in observations:
        case_key = observation.case.opaque_key() if opaque else observation.case.public_key()
        lines.append(
            f"{case_key} | {observation.outcome} | {observation.myth}"
        )
    return "\n".join(lines)
