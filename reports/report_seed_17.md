# Deutsch-Style AI Discovery Report

Seed: `17`
Rounds: `4`

## Protocol Notes

- Primary metric: final hidden truth score on holdout plus structurally shifted transfer cases.
- Diagnostic metrics: explanation proxy scores, critiques, and acquired observations.
- Opaque mode removes mythic story text from model-facing observations.
- Matched controls share the critique loop's hypothesis library and label budget.

## Public Observations

case | outcome
--- | ---
step=0, a=r0, b=d0, c=m1, e=w1 | wake
step=3, a=r1, b=d0, c=m1, e=w1 | sleep
step=2, a=r0, b=d1, c=m0, e=w1 | wake
step=2, a=r1, b=d0, c=m0, e=w0 | bloom
step=6, a=r1, b=d1, c=m1, e=w0 | sleep
step=3, a=r1, b=d0, c=m0, e=w1 | wake
step=4, a=r1, b=d0, c=m1, e=w0 | wake
step=9, a=r0, b=d0, c=m0, e=w0 | wake
step=5, a=r1, b=d1, c=m1, e=w0 | sleep
step=6, a=r0, b=d1, c=m0, e=w0 | sleep

## Scoreboard

agent | truth score | prediction | transfer reach | explanation score | hard-to-vary | criticizability | error-correction
--- | ---: | ---: | ---: | ---: | ---: | ---: | ---:
matched no-critique conjecture | 0.755 | 1.000 | 0.300 | 0.392 | 0.833 | 0.167 | 0.000
matched passive extra observations | 0.755 | 1.000 | 0.300 | 0.392 | 0.833 | 0.167 | 0.000
matched random tests | 0.755 | 1.000 | 0.300 | 0.392 | 0.833 | 0.167 | 0.000
Deutsch critique loop | 0.755 | 1.000 | 0.300 | 0.493 | 0.833 | 0.458 | 0.000
myth-preserving storyteller | 0.498 | 0.550 | 0.400 | 0.058 | 0.000 | 0.167 | 0.000
pure prediction | 0.475 | 0.475 | 0.475 | 0.386 | 0.820 | 0.167 | 0.000

## Runs

### myth-preserving storyteller

Initial explanation: **story_agent's moods**

The factor_a changes because story_agent alternates between hiding and revealing her favor. New outcomes can be absorbed as new moods.

Final explanation: **story_agent's moods**

The factor_a changes because story_agent alternates between hiding and revealing her favor. New outcomes can be absorbed as new moods.

Falsifier: No single observation would decisively refute a story with new moods.

Critiques:
- The explanation is easy to vary because any surprise becomes a new mood.

Acquired observations:
- None

### pure prediction

Initial explanation: **surface lookup**

This agent predicts by matching surface features and does not claim a causal mechanism. The current explanation uses factor_a, factor_b, factor_c. It is better when removing or changing one term damages predictions.

Final explanation: **surface lookup**

This agent predicts by matching surface features and does not claim a causal mechanism. The current explanation uses factor_a, factor_b, factor_c. It is better when removing or changing one term damages predictions.

Falsifier: A decisive refutation would be an unobserved case where a close rival predicts a different outcome and the current explanation loses.

Critiques:
- It predicts labels but has no account of why these variables matter.

Acquired observations:
- None

### matched no-critique conjecture

Initial explanation: **interaction pair model**

The first plausible causal conjecture is kept without asking for risky tests. The current explanation uses factor_a_factor_c, factor_b_factor_e. It is better when removing or changing one term damages predictions.

Final explanation: **interaction pair model**

The first plausible causal conjecture is kept without asking for risky tests. The current explanation uses factor_a_factor_c, factor_b_factor_e. It is better when removing or changing one term damages predictions.

Falsifier: A decisive refutation would be an unobserved case where a close rival predicts a different outcome and the current explanation loses.

Critiques:
- No criticism pass was allowed, so weak spots remain untested.

Acquired observations:
- None

### matched passive extra observations

Initial explanation: **interaction pair model**

Initial conjecture before extra observations. The current explanation uses factor_a_factor_c, factor_b_factor_e. It is better when removing or changing one term damages predictions.

Final explanation: **interaction pair model**

Revised after receiving extra observations selected without rival-critique logic. The current explanation uses factor_a_factor_c, factor_b_factor_e. It is better when removing or changing one term damages predictions.

Falsifier: A decisive refutation would be an unobserved case where a close rival predicts a different outcome and the current explanation loses.

Critiques:
- Extra labels were allowed, but no discriminating criticism selected them.

Acquired observations:
- step=7, a=r0, b=d1, c=m1, e=w1 -> bloom
- step=6, a=r1, b=d1, c=m0, e=w0 -> wake
- step=4, a=r0, b=d0, c=m0, e=w1 -> sleep
- step=3, a=r0, b=d1, c=m0, e=w0 -> sleep

### matched random tests

Initial explanation: **interaction pair model**

Initial conjecture before random oracle tests. The current explanation uses factor_a_factor_c, factor_b_factor_e. It is better when removing or changing one term damages predictions.

Final explanation: **interaction pair model**

Revised after the same label budget was spent on random experiment cases. The current explanation uses factor_a_factor_c, factor_b_factor_e. It is better when removing or changing one term damages predictions.

Falsifier: A decisive refutation would be an unobserved case where a close rival predicts a different outcome and the current explanation loses.

Critiques:
- Random tests control for the value of extra labels without active criticism.

Acquired observations:
- step=3, a=r0, b=d0, c=m1, e=w1 -> wake
- step=2, a=r0, b=d1, c=m1, e=w0 -> wake
- step=1, a=r1, b=d1, c=m1, e=w1 -> wake
- step=7, a=r1, b=d1, c=m1, e=w0 -> sleep

### Deutsch critique loop

Initial explanation: **interaction pair model**

Initial conjecture before criticism. The current explanation uses factor_a_factor_c, factor_b_factor_e. It is better when removing or changing one term damages predictions.

Final explanation: **interaction pair model**

Revised conjecture after exposing rival explanations to risky tests. The current explanation uses factor_a_factor_c, factor_b_factor_e. It is better when removing or changing one term damages predictions.

Falsifier: A decisive refutation would be an unobserved case where a close rival predicts a different outcome and the current explanation loses.

Critiques:
- Criticism: interaction pair model and cycle-only both fit what is known, so ask a risky unobserved test where they disagree.
- interaction pair model currently has no close rival on observed cases.

Acquired observations:
- step=7, a=r0, b=d1, c=m1, e=w1 -> bloom

## Holdout Predictions

### myth-preserving storyteller

case | prediction | truth
--- | --- | ---
step=3, a=r0, b=d1, c=m1, e=w0 | wake | wake
step=2, a=r1, b=d1, c=m1, e=w1 | wake | wake
step=0, a=r0, b=d0, c=m1, e=w0 | wake | bloom
step=2, a=r0, b=d0, c=m1, e=w1 | wake | wake
step=4, a=r1, b=d1, c=m1, e=w1 | wake | wake
step=0, a=r0, b=d1, c=m0, e=w1 | wake | wake
step=0, a=r0, b=d1, c=m1, e=w1 | wake | bloom
step=0, a=r0, b=d1, c=m0, e=w0 | wake | sleep

### pure prediction

case | prediction | truth
--- | --- | ---
step=3, a=r0, b=d1, c=m1, e=w0 | wake | wake
step=2, a=r1, b=d1, c=m1, e=w1 | sleep | wake
step=0, a=r0, b=d0, c=m1, e=w0 | wake | bloom
step=2, a=r0, b=d0, c=m1, e=w1 | wake | wake
step=4, a=r1, b=d1, c=m1, e=w1 | sleep | wake
step=0, a=r0, b=d1, c=m0, e=w1 | wake | wake
step=0, a=r0, b=d1, c=m1, e=w1 | wake | bloom
step=0, a=r0, b=d1, c=m0, e=w0 | wake | sleep

### matched no-critique conjecture

case | prediction | truth
--- | --- | ---
step=3, a=r0, b=d1, c=m1, e=w0 | wake | wake
step=2, a=r1, b=d1, c=m1, e=w1 | wake | wake
step=0, a=r0, b=d0, c=m1, e=w0 | bloom | bloom
step=2, a=r0, b=d0, c=m1, e=w1 | wake | wake
step=4, a=r1, b=d1, c=m1, e=w1 | wake | wake
step=0, a=r0, b=d1, c=m0, e=w1 | wake | wake
step=0, a=r0, b=d1, c=m1, e=w1 | bloom | bloom
step=0, a=r0, b=d1, c=m0, e=w0 | sleep | sleep

### matched passive extra observations

case | prediction | truth
--- | --- | ---
step=3, a=r0, b=d1, c=m1, e=w0 | wake | wake
step=2, a=r1, b=d1, c=m1, e=w1 | wake | wake
step=0, a=r0, b=d0, c=m1, e=w0 | bloom | bloom
step=2, a=r0, b=d0, c=m1, e=w1 | wake | wake
step=4, a=r1, b=d1, c=m1, e=w1 | wake | wake
step=0, a=r0, b=d1, c=m0, e=w1 | wake | wake
step=0, a=r0, b=d1, c=m1, e=w1 | bloom | bloom
step=0, a=r0, b=d1, c=m0, e=w0 | sleep | sleep

### matched random tests

case | prediction | truth
--- | --- | ---
step=3, a=r0, b=d1, c=m1, e=w0 | wake | wake
step=2, a=r1, b=d1, c=m1, e=w1 | wake | wake
step=0, a=r0, b=d0, c=m1, e=w0 | bloom | bloom
step=2, a=r0, b=d0, c=m1, e=w1 | wake | wake
step=4, a=r1, b=d1, c=m1, e=w1 | wake | wake
step=0, a=r0, b=d1, c=m0, e=w1 | wake | wake
step=0, a=r0, b=d1, c=m1, e=w1 | bloom | bloom
step=0, a=r0, b=d1, c=m0, e=w0 | sleep | sleep

### Deutsch critique loop

case | prediction | truth
--- | --- | ---
step=3, a=r0, b=d1, c=m1, e=w0 | wake | wake
step=2, a=r1, b=d1, c=m1, e=w1 | wake | wake
step=0, a=r0, b=d0, c=m1, e=w0 | bloom | bloom
step=2, a=r0, b=d0, c=m1, e=w1 | wake | wake
step=4, a=r1, b=d1, c=m1, e=w1 | wake | wake
step=0, a=r0, b=d1, c=m0, e=w1 | wake | wake
step=0, a=r0, b=d1, c=m1, e=w1 | bloom | bloom
step=0, a=r0, b=d1, c=m0, e=w0 | sleep | sleep

## Hidden World Revealed

The hidden configuration is revealed only after scoring, so it cannot guide the agents during the run.

`seed=17, family=interaction, period=10, axial_phase=4, heat_lag=2, weights=(axial=2.37, factor_b=0.71, factor_c=-0.32, factor_e=0.25, interaction=0.98)`
