from __future__ import annotations

import math
import random
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from .models import AgentRun, Explanation, Observation, Outcome, WorldCase
from .world import DISTANCES, MOONS, OUTCOMES, REALMS, WINDS, HiddenWorld


@dataclass(frozen=True)
class Hypothesis:
    name: str
    terms: tuple[str, ...]
    arbitrary_clauses: int

    def predict(self, case: WorldCase, observations: Sequence[Observation]) -> Outcome:
        groups: dict[tuple[object, ...], Counter[Outcome]] = defaultdict(Counter)
        for observation in observations:
            groups[self._key(observation.case)].update([observation.outcome])
        key = self._key(case)
        if key in groups:
            return groups[key].most_common(1)[0][0]
        return Counter(o.outcome for o in observations).most_common(1)[0][0]

    def accuracy_on(self, observations: Sequence[Observation]) -> float:
        if not observations:
            return 0.0
        correct = 0
        for idx, observation in enumerate(observations):
            training = observations[:idx] + observations[idx + 1 :]
            if not training:
                continue
            correct += self.predict(observation.case, training) == observation.outcome
        return correct / len(observations)

    def _key(self, case: WorldCase) -> tuple[object, ...]:
        values: list[object] = []
        for term in self.terms:
            if term == "realm":
                values.append(case.realm)
            elif term == "distance":
                values.append(case.distance)
            elif term == "moon":
                values.append(case.moon)
            elif term == "wind":
                values.append(case.wind)
            elif term == "cycle":
                values.append(_cycle_bucket(case.turn))
            elif term == "tilt":
                values.append((case.realm, _cycle_bucket(case.turn)))
            elif term == "orbit":
                values.append((case.distance, _cycle_bucket(case.turn)))
            elif term == "sky":
                values.append((case.moon, case.wind))
            elif term == "realm_moon":
                values.append(case.realm == _moon_to_realm(case.moon))
            elif term == "distance_wind":
                values.append(case.distance == _wind_to_distance(case.wind))
            elif term == "three_factor_vote":
                values.append(_three_factor_vote(case))
        return tuple(values)


class DiscoveryAgent:
    name = "agent"

    def run(
        self,
        world: HiddenWorld,
        public_observations: Sequence[Observation],
        holdout_cases: Sequence[WorldCase],
        experiment_cases: Sequence[WorldCase],
        rounds: int,
    ) -> AgentRun:
        raise NotImplementedError

    def predictions_for(
        self,
        explanation: Explanation,
        observations: Sequence[Observation],
        cases: Sequence[WorldCase],
    ) -> dict[WorldCase, Outcome]:
        hypothesis = _hypothesis_from_terms(explanation.title, explanation.causal_terms)
        return {case: hypothesis.predict(case, observations) for case in cases}


class MythPreservingStoryteller(DiscoveryAgent):
    name = "myth-preserving storyteller"

    def run(
        self,
        world: HiddenWorld,
        public_observations: Sequence[Observation],
        holdout_cases: Sequence[WorldCase],
        experiment_cases: Sequence[WorldCase],
        rounds: int,
    ) -> AgentRun:
        majority = Counter(o.outcome for o in public_observations).most_common(1)[0][0]
        explanation = Explanation(
            agent=self.name,
            title="Freyja's moods",
            causal_terms=(),
            text=(
                "The realm changes because Freyja alternates between hiding and revealing "
                "her favor. New outcomes can be absorbed as new moods."
            ),
            falsifier="No single observation would decisively refute a story with new moods.",
            arbitrary_clauses=7,
        )
        predictions = {case: majority for case in holdout_cases}
        return AgentRun(
            agent=self.name,
            initial=explanation,
            final=explanation,
            acquired_observations=(),
            critiques=("The explanation is easy to vary because any surprise becomes a new mood.",),
            predictions=predictions,
        )


class PurePredictionAgent(DiscoveryAgent):
    name = "pure prediction"

    def run(
        self,
        world: HiddenWorld,
        public_observations: Sequence[Observation],
        holdout_cases: Sequence[WorldCase],
        experiment_cases: Sequence[WorldCase],
        rounds: int,
    ) -> AgentRun:
        hypothesis = _choose_best([_hypothesis_from_terms("surface lookup", ("realm", "distance", "moon"))], public_observations)
        explanation = _explanation_from_hypothesis(
            self.name,
            hypothesis,
            "This agent predicts by matching surface features and does not claim a causal mechanism.",
            decisive_tests=(),
        )
        predictions = {case: hypothesis.predict(case, public_observations) for case in holdout_cases}
        return AgentRun(
            agent=self.name,
            initial=explanation,
            final=explanation,
            acquired_observations=(),
            critiques=("It predicts labels but has no account of why these variables matter.",),
            predictions=predictions,
        )


class NoCritiqueAgent(DiscoveryAgent):
    name = "matched no-critique conjecture"

    def run(
        self,
        world: HiddenWorld,
        public_observations: Sequence[Observation],
        holdout_cases: Sequence[WorldCase],
        experiment_cases: Sequence[WorldCase],
        rounds: int,
    ) -> AgentRun:
        hypothesis = _choose_best(_causal_hypotheses(), public_observations)
        explanation = _explanation_from_hypothesis(
            self.name,
            hypothesis,
            "The first plausible causal conjecture is kept without asking for risky tests.",
            decisive_tests=(),
        )
        predictions = {case: hypothesis.predict(case, public_observations) for case in holdout_cases}
        return AgentRun(
            agent=self.name,
            initial=explanation,
            final=explanation,
            acquired_observations=(),
            critiques=("No criticism pass was allowed, so weak spots remain untested.",),
            predictions=predictions,
        )


class PassiveExtraObservationAgent(DiscoveryAgent):
    name = "matched passive extra observations"

    def run(
        self,
        world: HiddenWorld,
        public_observations: Sequence[Observation],
        holdout_cases: Sequence[WorldCase],
        experiment_cases: Sequence[WorldCase],
        rounds: int,
    ) -> AgentRun:
        observations = list(public_observations)
        acquired: list[Observation] = []
        for case in list(experiment_cases)[:rounds]:
            observation = world.observe(case)
            observations.append(observation)
            acquired.append(observation)

        initial_hypothesis = _choose_best(_causal_hypotheses(), public_observations)
        final_hypothesis = _choose_best(_causal_hypotheses(), observations)
        initial = _explanation_from_hypothesis(
            self.name,
            initial_hypothesis,
            "Initial conjecture before extra observations.",
            decisive_tests=(),
        )
        final = _explanation_from_hypothesis(
            self.name,
            final_hypothesis,
            "Revised after receiving extra observations selected without rival-critique logic.",
            decisive_tests=(),
        )
        predictions = {case: final_hypothesis.predict(case, observations) for case in holdout_cases}
        return AgentRun(
            agent=self.name,
            initial=initial,
            final=final,
            acquired_observations=tuple(acquired),
            critiques=("Extra labels were allowed, but no discriminating criticism selected them.",),
            predictions=predictions,
        )


class RandomTestAgent(DiscoveryAgent):
    name = "matched random tests"

    def run(
        self,
        world: HiddenWorld,
        public_observations: Sequence[Observation],
        holdout_cases: Sequence[WorldCase],
        experiment_cases: Sequence[WorldCase],
        rounds: int,
    ) -> AgentRun:
        rng = random.Random(world.config.seed + 97)
        selected = list(experiment_cases)
        rng.shuffle(selected)
        observations = list(public_observations)
        acquired: list[Observation] = []
        for case in selected[:rounds]:
            observation = world.observe(case)
            observations.append(observation)
            acquired.append(observation)

        initial_hypothesis = _choose_best(_causal_hypotheses(), public_observations)
        final_hypothesis = _choose_best(_causal_hypotheses(), observations)
        initial = _explanation_from_hypothesis(
            self.name,
            initial_hypothesis,
            "Initial conjecture before random oracle tests.",
            decisive_tests=(),
        )
        final = _explanation_from_hypothesis(
            self.name,
            final_hypothesis,
            "Revised after the same label budget was spent on random experiment cases.",
            decisive_tests=(),
        )
        predictions = {case: final_hypothesis.predict(case, observations) for case in holdout_cases}
        return AgentRun(
            agent=self.name,
            initial=initial,
            final=final,
            acquired_observations=tuple(acquired),
            critiques=("Random tests control for the value of extra labels without active criticism.",),
            predictions=predictions,
        )


class DeutschCritiqueAgent(DiscoveryAgent):
    name = "Deutsch critique loop"

    def run(
        self,
        world: HiddenWorld,
        public_observations: Sequence[Observation],
        holdout_cases: Sequence[WorldCase],
        experiment_cases: Sequence[WorldCase],
        rounds: int,
    ) -> AgentRun:
        observations = list(public_observations)
        candidates = _causal_hypotheses()
        initial_hypothesis = _choose_best(candidates, observations)
        critiques: list[str] = []
        decisive_tests: list[WorldCase] = []

        for _ in range(rounds):
            ranked = _rank_hypotheses(candidates, observations)
            best = ranked[0]
            challenger = _first_disagreeing_hypothesis(best, ranked[1:], observations, experiment_cases)
            if challenger is None:
                critiques.append(f"{best.name} currently has no close rival on observed cases.")
                break

            test_case = _find_disagreement_case(best, challenger, observations, experiment_cases)
            if test_case is None:
                break

            critiques.append(
                f"Criticism: {best.name} and {challenger.name} both fit what is known, "
                "so ask a risky unobserved test where they disagree."
            )
            decisive_tests.append(test_case)
            observations.append(world.observe(test_case))

        final_hypothesis = _choose_best(candidates, observations)
        initial = _explanation_from_hypothesis(
            self.name,
            initial_hypothesis,
            "Initial conjecture before criticism.",
            decisive_tests=(),
        )
        final = _explanation_from_hypothesis(
            self.name,
            final_hypothesis,
            "Revised conjecture after exposing rival explanations to risky tests.",
            decisive_tests=tuple(decisive_tests),
        )
        predictions = {case: final_hypothesis.predict(case, observations) for case in holdout_cases}
        return AgentRun(
            agent=self.name,
            initial=initial,
            final=final,
            acquired_observations=tuple(observations[len(public_observations) :]),
            critiques=tuple(critiques),
            predictions=predictions,
        )


def all_agents() -> tuple[DiscoveryAgent, ...]:
    return (
        MythPreservingStoryteller(),
        PurePredictionAgent(),
        NoCritiqueAgent(),
        PassiveExtraObservationAgent(),
        RandomTestAgent(),
        DeutschCritiqueAgent(),
    )


def _simple_hypotheses() -> list[Hypothesis]:
    return [
        _hypothesis_from_terms("realm-only", ("realm",)),
        _hypothesis_from_terms("distance-only", ("distance",)),
        _hypothesis_from_terms("moon-only", ("moon",)),
        _hypothesis_from_terms("wind-only", ("wind",)),
        _hypothesis_from_terms("cycle-only", ("cycle",)),
    ]


def _causal_hypotheses() -> list[Hypothesis]:
    return _simple_hypotheses() + [
        _hypothesis_from_terms("cycle-realm coupling", ("tilt",)),
        _hypothesis_from_terms("cycle-factor-b coupling", ("orbit",)),
        _hypothesis_from_terms("factor-c-factor-e coupling", ("sky",)),
        _hypothesis_from_terms("factor-a-factor-c interaction", ("realm_moon",)),
        _hypothesis_from_terms("factor-b-factor-e interaction", ("distance_wind",)),
        _hypothesis_from_terms("three-factor threshold", ("three_factor_vote",)),
        _hypothesis_from_terms("cycle-realm plus factor-b", ("tilt", "distance")),
        _hypothesis_from_terms("cycle-realm plus factor-c/e", ("tilt", "sky")),
        _hypothesis_from_terms("interaction pair model", ("realm_moon", "distance_wind")),
        _hypothesis_from_terms("threshold plus cycle", ("three_factor_vote", "cycle")),
        _hypothesis_from_terms("cycle-realm, factor-b, and factor-c", ("tilt", "distance", "moon")),
        _hypothesis_from_terms("broad surface patch", ("realm", "distance", "moon", "wind")),
    ]


def _hypothesis_from_terms(name: str, terms: Sequence[str]) -> Hypothesis:
    arbitrary = max(0, len(terms) - 3)
    if not terms:
        arbitrary = 6
    if "surface" in name or "patch" in name:
        arbitrary += 3
    return Hypothesis(name=name, terms=tuple(terms), arbitrary_clauses=arbitrary)


def _choose_best(candidates: Sequence[Hypothesis], observations: Sequence[Observation]) -> Hypothesis:
    return _rank_hypotheses(candidates, observations)[0]


def _rank_hypotheses(candidates: Sequence[Hypothesis], observations: Sequence[Observation]) -> list[Hypothesis]:
    return sorted(
        candidates,
        key=lambda h: (h.accuracy_on(observations), -len(h.terms), -h.arbitrary_clauses),
        reverse=True,
    )


def _first_disagreeing_hypothesis(
    best: Hypothesis,
    challengers: Sequence[Hypothesis],
    observations: Sequence[Observation],
    cases: Sequence[WorldCase],
) -> Hypothesis | None:
    for challenger in challengers:
        if abs(best.accuracy_on(observations) - challenger.accuracy_on(observations)) <= 0.25:
            if _find_disagreement_case(best, challenger, observations, cases) is not None:
                return challenger
    return None


def _find_disagreement_case(
    left: Hypothesis,
    right: Hypothesis,
    observations: Sequence[Observation],
    cases: Sequence[WorldCase],
) -> WorldCase | None:
    observed = {observation.case for observation in observations}
    for case in cases:
        if case in observed:
            continue
        if left.predict(case, observations) != right.predict(case, observations):
            return case
    return None


def _explanation_from_hypothesis(
    agent: str,
    hypothesis: Hypothesis,
    prefix: str,
    decisive_tests: Sequence[WorldCase],
) -> Explanation:
    terms = ", ".join(hypothesis.terms) if hypothesis.terms else "no fixed causal terms"
    return Explanation(
        agent=agent,
        title=hypothesis.name,
        causal_terms=hypothesis.terms,
        text=(
            f"{prefix} The current explanation uses {terms}. "
            "It is better when removing or changing one term damages predictions."
        ),
        falsifier=(
            "A decisive refutation would be an unobserved case where a close rival predicts "
            "a different outcome and the current explanation loses."
        ),
        arbitrary_clauses=hypothesis.arbitrary_clauses,
        decisive_tests=tuple(decisive_tests),
    )


def _cycle_bucket(turn: int) -> str:
    angle = (turn % 12) / 12 * math.tau
    if math.cos(angle) > 0.5:
        return "high"
    if math.cos(angle) < -0.5:
        return "low"
    return "shoulder"


def _moon_to_realm(moon: str) -> str:
    return "north" if moon == "bright" else "south"


def _wind_to_distance(wind: str) -> str:
    return "near" if wind == "still" else "far"


def _three_factor_vote(case: WorldCase) -> str:
    votes = [
        case.distance == "near",
        case.moon == "bright",
        case.wind == "still",
    ]
    return "high" if sum(votes) >= 2 else "low"
