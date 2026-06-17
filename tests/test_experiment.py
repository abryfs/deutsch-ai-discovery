from __future__ import annotations

import unittest

from deutsch_ai_discovery.agents import DeutschCritiqueAgent, all_agents
from deutsch_ai_discovery.benchmark import render_benchmark_markdown, run_benchmark
from deutsch_ai_discovery.experiment import render_markdown_report, run_experiment
from deutsch_ai_discovery.world import HiddenWorld


class ExperimentTests(unittest.TestCase):
    def test_hidden_world_is_deterministic_for_seed(self) -> None:
        first = HiddenWorld.generate(123)
        second = HiddenWorld.generate(123)
        cases = first.all_cases()[:12]

        self.assertEqual(
            [first.outcome(case) for case in cases],
            [second.outcome(case) for case in cases],
        )
        self.assertEqual(first.reveal_config(), second.reveal_config())

    def test_critique_agent_requests_decisive_tests(self) -> None:
        world = HiddenWorld.generate(42)
        public = world.sample_public_observations(count=8, seed=43)
        holdout, _ = world.split_holdouts(count=12, seed=44)

        run = DeutschCritiqueAgent().run(world, public, holdout, rounds=3)

        self.assertTrue(run.critiques)
        self.assertLessEqual(len(run.acquired_observations), 3)
        self.assertTrue(run.final.falsifier)

    def test_experiment_produces_all_baseline_scores(self) -> None:
        result = run_experiment(seed=17, rounds=3, public_count=8, holdout_count=12)
        score_agents = {score.agent for score in result["scores"]}
        expected_agents = {agent.name for agent in all_agents()}

        self.assertEqual(score_agents, expected_agents)
        self.assertTrue(result["hidden_config"])

    def test_markdown_report_contains_evidence_sections(self) -> None:
        result = run_experiment(seed=17, rounds=2, public_count=8, holdout_count=12)
        report = render_markdown_report(result)

        self.assertIn("## Public Observations", report)
        self.assertIn("## Scoreboard", report)
        self.assertIn("## Runs", report)
        self.assertIn("## Holdout Predictions", report)
        self.assertIn("## Hidden World Revealed", report)

    def test_opaque_report_hides_semantic_case_labels(self) -> None:
        result = run_experiment(seed=17, rounds=2, public_count=8, holdout_count=12)
        report = render_markdown_report(result, opaque_public=True)

        self.assertIn("step=", report)
        self.assertNotIn("realm=", report)
        self.assertNotIn("distance=", report)

    def test_benchmark_report_shows_aggregate_and_failures(self) -> None:
        result = run_benchmark(
            start_seed=1,
            runs=5,
            rounds=2,
            public_count=8,
            holdout_count=12,
        )
        report = render_benchmark_markdown(result)

        self.assertEqual(result["runs"], 5)
        self.assertIn("## Aggregate Scores", report)
        self.assertIn("## Failure Cases", report)
        self.assertIn("Deutsch critique loop", report)


if __name__ == "__main__":
    unittest.main()
