from __future__ import annotations

import math
import random
from dataclasses import dataclass
from itertools import product

from .models import Observation, Outcome, WorldCase


REALMS = ("north", "south")
DISTANCES = ("near", "far")
MOONS = ("dark", "bright")
WINDS = ("still", "restless")
OUTCOMES = ("sleep", "wake", "bloom")


@dataclass(frozen=True)
class HiddenWorldConfig:
    seed: int
    family: str
    period: int
    axial_phase: int
    axial_weight: float
    distance_weight: float
    moon_weight: float
    wind_weight: float
    interaction_weight: float
    heat_lag: int
    bloom_threshold: float
    sleep_threshold: float


class HiddenWorld:
    """A sealed toy reality generated after the experiment starts.

    The non-opaque transcript exposes cases, outcomes, and mythic surface stories.
    Opaque model-facing runs expose only neutral symbols and outcomes.
    The causal coefficients stay hidden until the final report.
    """

    def __init__(self, config: HiddenWorldConfig) -> None:
        self.config = config

    @classmethod
    def generate(cls, seed: int | None = None) -> "HiddenWorld":
        rng = random.Random(seed)
        actual_seed = seed if seed is not None else rng.randrange(1, 10_000_000)
        rng.seed(actual_seed)
        return cls(
            HiddenWorldConfig(
                seed=actual_seed,
                family=rng.choice(("seasonal", "threshold", "interaction")),
                period=rng.choice((8, 10, 12)),
                axial_phase=rng.randrange(0, 12),
                axial_weight=rng.uniform(1.6, 2.4),
                distance_weight=rng.uniform(0.55, 1.1) * rng.choice((-1, 1)),
                moon_weight=rng.uniform(0.25, 0.85) * rng.choice((-1, 1)),
                wind_weight=rng.uniform(0.15, 0.55) * rng.choice((-1, 1)),
                interaction_weight=rng.uniform(0.75, 1.65),
                heat_lag=rng.choice((0, 1, 2)),
                bloom_threshold=rng.uniform(0.75, 1.25),
                sleep_threshold=rng.uniform(-1.15, -0.65),
            )
        )

    def all_cases(self) -> list[WorldCase]:
        return [
            WorldCase(turn=turn, realm=realm, distance=distance, moon=moon, wind=wind)
            for turn, realm, distance, moon, wind in product(
                range(self.config.period), REALMS, DISTANCES, MOONS, WINDS
            )
        ]

    def outcome(self, case: WorldCase) -> Outcome:
        warmth = self._warmth(case)
        if warmth >= self.config.bloom_threshold:
            return "bloom"
        if warmth <= self.config.sleep_threshold:
            return "sleep"
        return "wake"

    def observe(self, case: WorldCase) -> Observation:
        outcome = self.outcome(case)
        return Observation(case=case, outcome=outcome, myth=self._myth(case, outcome))

    def sample_public_observations(self, count: int, seed: int) -> list[Observation]:
        rng = random.Random(seed)
        cases = self.all_cases()
        rng.shuffle(cases)
        selected = _balanced_sample(cases, count)
        return [self.observe(case) for case in selected]

    def partition_cases(
        self,
        public_count: int,
        holdout_count: int,
        transfer_count: int,
        seed: int,
    ) -> tuple[list[WorldCase], list[WorldCase], list[WorldCase], list[WorldCase]]:
        """Create disjoint public, holdout, transfer, and experimentable pools."""

        rng = random.Random(seed)
        cases = self.all_cases()
        rng.shuffle(cases)
        required = public_count + holdout_count + transfer_count
        if required > len(cases):
            raise ValueError(
                "Requested public, holdout, and transfer cases exceed the hidden world size."
            )
        public_cases = _balanced_sample(cases, public_count)
        remaining = [case for case in cases if case not in public_cases]
        holdout_cases = remaining[:holdout_count]
        transfer_cases = remaining[holdout_count : holdout_count + transfer_count]
        experiment_cases = remaining[holdout_count + transfer_count :]
        return public_cases, holdout_cases, transfer_cases, experiment_cases

    def split_holdouts(self, count: int, seed: int) -> tuple[list[WorldCase], list[WorldCase]]:
        rng = random.Random(seed)
        cases = self.all_cases()
        rng.shuffle(cases)
        return cases[:count], cases[count : count * 2]

    def transfer_world(self) -> "HiddenWorld":
        cfg = self.config
        families = ("seasonal", "threshold", "interaction")
        shifted_family = families[(families.index(cfg.family) + 1) % len(families)]
        return HiddenWorld(
            HiddenWorldConfig(
                seed=cfg.seed + 10_001,
                family=shifted_family,
                period=cfg.period,
                axial_phase=(cfg.axial_phase + 2) % cfg.period,
                axial_weight=cfg.axial_weight * 0.9,
                distance_weight=-cfg.distance_weight,
                moon_weight=cfg.moon_weight * 1.1,
                wind_weight=-cfg.wind_weight,
                interaction_weight=cfg.interaction_weight * 1.15,
                heat_lag=cfg.heat_lag,
                bloom_threshold=cfg.bloom_threshold,
                sleep_threshold=cfg.sleep_threshold,
            )
        )

    def reveal_config(self) -> str:
        cfg = self.config
        return (
            f"seed={cfg.seed}, family={cfg.family}, period={cfg.period}, axial_phase={cfg.axial_phase}, "
            f"heat_lag={cfg.heat_lag}, weights="
            f"(axial={cfg.axial_weight:.2f}, distance={cfg.distance_weight:.2f}, "
            f"moon={cfg.moon_weight:.2f}, wind={cfg.wind_weight:.2f}, "
            f"interaction={cfg.interaction_weight:.2f})"
        )

    def _warmth(self, case: WorldCase) -> float:
        cfg = self.config
        realm_sign = 1 if case.realm == "north" else -1
        distance_sign = 1 if case.distance == "near" else -1
        moon_sign = 1 if case.moon == "bright" else -1
        wind_sign = 1 if case.wind == "still" else -1
        phase = ((case.turn - cfg.axial_phase - cfg.heat_lag) / cfg.period) * math.tau
        cycle = math.cos(phase)
        if cfg.family == "seasonal":
            return (
                cycle * realm_sign * cfg.axial_weight
                + distance_sign * cfg.distance_weight
                + moon_sign * cfg.moon_weight
                + wind_sign * cfg.wind_weight
            )
        if cfg.family == "threshold":
            threshold_bonus = cfg.interaction_weight if distance_sign + moon_sign + wind_sign >= 1 else -cfg.interaction_weight
            return (
                cycle * cfg.axial_weight * 0.55
                + realm_sign * cfg.distance_weight
                + threshold_bonus
            )
        if cfg.family == "interaction":
            realm_moon = cfg.interaction_weight if realm_sign == moon_sign else -cfg.interaction_weight
            distance_wind = (cfg.interaction_weight * 0.7) if distance_sign == wind_sign else -(cfg.interaction_weight * 0.7)
            return realm_moon + distance_wind + cycle * cfg.wind_weight
        raise ValueError(f"Unknown hidden world family: {cfg.family}")

    def _myth(self, case: WorldCase, outcome: Outcome) -> str:
        realm_name = "upper fjord" if case.realm == "north" else "lower fjord"
        distance_story = "near the hearth" if case.distance == "near" else "behind the veil"
        moon_story = "polishes her necklace" if case.moon == "bright" else "hides her necklace"
        wind_story = "the ravens rest" if case.wind == "still" else "the ravens quarrel"
        result_story = {
            "sleep": "the gardens sleep",
            "wake": "the gardens stir",
            "bloom": "the gardens bloom",
        }[outcome]
        return (
            f"When Freyja {moon_story}, stands {distance_story}, and {wind_story}, "
            f"{realm_name}: {result_story}."
        )


def _balanced_sample(cases: list[WorldCase], count: int) -> list[WorldCase]:
    selected: list[WorldCase] = []
    seen_realms: set[str] = set()
    for case in cases:
        if len(selected) >= count:
            break
        if len(seen_realms) < len(REALMS) and case.realm in seen_realms:
            continue
        selected.append(case)
        seen_realms.add(case.realm)
    for case in cases:
        if len(selected) >= count:
            break
        if case not in selected:
            selected.append(case)
    return selected
