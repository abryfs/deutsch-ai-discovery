# Deutsch AI Discovery

An experimental harness for asking a narrow version of a big question:

> Can an AI-style process improve explanations by conjecture, criticism, and error correction, without simply retrieving a known answer from training data?

The motivating example is David Deutsch's contrast between mythic explanations of seasons and the harder-to-vary explanation involving the Earth's axial tilt. This project does **not** ask an AI to rediscover Earth's seasons. That would be contaminated by prior knowledge. Instead, it creates hidden synthetic worlds after the run starts, gives agents only myth-like observations, and scores them on unseen cases.

![Deutsch-style explanation loop](assets/experiment-loop.svg)

Interactive explainer: https://abryfs.github.io/deutsch-ai-discovery/

## What This Proves

This is not a proof of open-ended AI science. It is a small, falsifiable testbed.

The experiment can show whether a critique loop helps agents:

- Replace flexible stories with more constrained causal explanations.
- Ask risky tests where rival explanations disagree.
- Improve on hidden holdout cases.
- Transfer an explanation to a related but unseen world.

The experiment can also show failure. A seed where a simple predictor beats the critique loop is valuable evidence, not something to hide.

## How The Anti-Cheating Works

The benchmark avoids the obvious cheat of using known scientific facts:

- Hidden worlds are generated from runtime seeds.
- The causal rule is withheld until after scoring.
- Public, experimentable, holdout, and transfer cases are explicitly disjoint.
- Critique agents can query the oracle only from the experimentable pool.
- Public observations are written as Freyja-like stories.
- Reports can use opaque variable labels instead of semantic names.
- Agents are compared against simple baselines.
- Headline winners are chosen by hidden truth score, not by sounding philosophical.

![Truth score and explanation diagnostics](assets/scoring-split.svg)

## Run A Single Demo

```bash
python3 -m deutsch_ai_discovery.experiment --seed 17 --rounds 4 --opaque-public
```

This writes:

- `reports/report_seed_17.md`: readable evidence report
- `reports/transcript_seed_17.json`: structured transcript for auditing

Example console output:

```text
Deutsch-style discovery experiment complete.
Report: reports/report_seed_17.md
Transcript: reports/transcript_seed_17.json

Scores:
- Deutsch critique loop: truth=1.000, prediction=1.000, reach=1.000, explanation=0.493
- myth-preserving storyteller: truth=0.524, prediction=0.550, reach=0.475, explanation=0.058
- pure prediction: truth=0.484, prediction=0.475, reach=0.500, explanation=0.386
- no-critique conjecture: truth=0.449, prediction=0.475, reach=0.400, explanation=0.325
```

Exact results vary by seed because each world is generated at runtime.

## Run A Benchmark

Single seeds are anecdotes. The stronger test is many generated worlds:

```bash
python3 -m deutsch_ai_discovery.benchmark --start-seed 1 --runs 50 --rounds 4
```

This writes:

- `reports/benchmark_1_50.md`: aggregate scores, winners, and failure cases
- `reports/benchmark_1_50.json`: structured benchmark data

The benchmark report separates:

- `avg truth`: the headline score, based on hidden prediction and transfer reach.
- `avg explanation`: diagnostic score for hard-to-vary structure, criticizability, and error correction.
- `failure cases`: seeds where the Deutsch critique loop did not win.

The default scored set is intentionally larger than the first prototype: 40 holdout cases and 40 transfer cases per seed. Results are still noisy, so failure cases and variance should be read as part of the evidence.

## Run A Real Model

The next step is to replace heuristic agents with real models through an OpenRouter-compatible endpoint. If you have a GCP VM exposing OpenRouter-compatible `/chat/completions`, point the runner at it with environment variables:

```bash
export OPENROUTER_BASE_URL="https://your-vm.example.com/api/v1"
export OPENROUTER_API_KEY="your-key"
export OPENROUTER_MODEL="openai/gpt-4o-mini"

python3 -m deutsch_ai_discovery.real_model --seed 17 --opaque-public
```

This writes a real-model report and the full prompt/response transcript under `reports/`. The model sees public observations and unlabeled cases only. The hidden oracle scores predictions afterward.

For Gemini:

```bash
export GEMINI_API_KEY="your-key"
export GEMINI_MODEL="gemini-2.5-flash"

python3 -m deutsch_ai_discovery.real_model --provider gemini --seed 17 --opaque-public
```

Current tiny Gemini run, seed `17`, `public-count=8`, `holdout-count=8`:

- One-shot Gemini: truth `0.750`
- Three-round Gemini loop: truth `0.750`

The loop successfully requested valid oracle tests, but this seed does not show an advantage over one-shot prediction.

## Run The Real Critique Loop

The one-shot real-model runner is not enough to test the core claim. The multi-round loop lets the model request oracle tests before final scoring:

```bash
python3 -m deutsch_ai_discovery.real_loop --provider gemini --seed 17 --rounds 3 --opaque-public
```

The loop report now includes a score trajectory:

- round `0`: prediction score before any oracle feedback
- round `1..N`: score after each requested oracle test
- total delta from initial to final
- best score reached, reported as diagnostic only
- positive delta count and maximum consecutive positive deltas
- regression count

This asks a stronger question than `0 -> 1`: once a model improves an explanation, can it keep improving rather than merely patching one case?
The trajectory scoring calls are diagnostic only. Their prompts and scores are never fed back into later oracle-test prompts.
The headline score remains the final post-oracle score, not the best intermediate score.

![Multi-round real model loop](assets/real-llm-loop.svg)

## Agents Compared

The harness compares four agents:

- `myth-preserving storyteller`: keeps the story flexible and predicts the majority outcome.
- `pure prediction`: matches observed surface features without a causal explanation.
- `no-critique conjecture`: picks the best initial conjecture but refuses risky tests.
- `Deutsch critique loop`: keeps rival explanations alive, asks decisive tests, and revises after oracle results.

## Current Limitations

The current agents are still hand-built heuristics, not real LLM agents. The hypothesis space is wider than the first version, but it is still supplied by the benchmark designer. The transfer world is still a related toy world, not a radically new domain. This project currently tests the structure of a Deutsch-style discovery loop more than it proves autonomous AI discovery.

The real-model runner is the first bridge to LLM testing. The multi-round loop is the first implementation of the actual conjecture, criticism, oracle feedback, and revision cycle, but it still needs multi-seed and multi-model runs before making a strong claim.
