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
        public_cases, holdout, _transfer, experiment_cases = world.partition_cases(
            public_count=8,
            holdout_count=12,
            transfer_count=12,
            seed=43,
        )
        public = [world.observe(case) for case in public_cases]

        run = DeutschCritiqueAgent().run(world, public, holdout, experiment_cases, rounds=3)

        self.assertTrue(run.critiques)
        self.assertLessEqual(len(run.acquired_observations), 3)
        self.assertTrue(run.final.falsifier)

    def test_case_partitions_are_disjoint(self) -> None:
        world = HiddenWorld.generate(42)
        public, holdout, transfer, experiment = world.partition_cases(
            public_count=8,
            holdout_count=12,
            transfer_count=12,
            seed=43,
        )

        self.assertFalse(set(public) & set(holdout))
        self.assertFalse(set(public) & set(transfer))
        self.assertFalse(set(public) & set(experiment))
        self.assertFalse(set(holdout) & set(transfer))
        self.assertFalse(set(holdout) & set(experiment))
        self.assertFalse(set(transfer) & set(experiment))

    def test_critique_agent_cannot_observe_scored_cases(self) -> None:
        result = run_experiment(seed=17, rounds=4, public_count=8, holdout_count=12)
        scored = set(result["holdout_truth"]) | set(result["transfer_truth"])
        critique_run = next(run for run in result["runs"] if run.agent == "Deutsch critique loop")
        acquired = {observation.case for observation in critique_run.acquired_observations}

        self.assertFalse(scored & acquired)

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
        self.assertNotIn("Freyja", report)
        self.assertNotIn("fjord", report)
        self.assertNotIn("necklace", report)
        self.assertNotIn("ravens", report)

    def test_transfer_world_changes_family(self) -> None:
        world = HiddenWorld.generate(17)
        transfer = world.transfer_world()

        self.assertNotEqual(world.config.family, transfer.config.family)

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
        self.assertIn("matched passive extra observations", report)
        self.assertIn("matched random tests", report)


if __name__ == "__main__":
    unittest.main()
