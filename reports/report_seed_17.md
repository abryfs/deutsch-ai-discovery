# Deutsch-Style AI Discovery Report

Seed: `17`
Rounds: `4`

## Public Observations

case | outcome | myth
--- | --- | ---
step=0, a=r0, b=d0, c=m1, e=w1 | wake | When Freyja polishes her necklace, stands near the hearth, and the ravens quarrel, upper fjord: the gardens stir.
step=3, a=r1, b=d0, c=m1, e=w1 | sleep | When Freyja polishes her necklace, stands near the hearth, and the ravens quarrel, lower fjord: the gardens sleep.
step=2, a=r0, b=d1, c=m0, e=w1 | wake | When Freyja hides her necklace, stands behind the veil, and the ravens quarrel, upper fjord: the gardens stir.
step=2, a=r1, b=d0, c=m0, e=w0 | bloom | When Freyja hides her necklace, stands near the hearth, and the ravens rest, lower fjord: the gardens bloom.
step=6, a=r1, b=d1, c=m1, e=w0 | sleep | When Freyja polishes her necklace, stands behind the veil, and the ravens rest, lower fjord: the gardens sleep.
step=3, a=r1, b=d0, c=m0, e=w1 | wake | When Freyja hides her necklace, stands near the hearth, and the ravens quarrel, lower fjord: the gardens stir.
step=4, a=r1, b=d0, c=m1, e=w0 | wake | When Freyja polishes her necklace, stands near the hearth, and the ravens rest, lower fjord: the gardens stir.
step=9, a=r0, b=d0, c=m0, e=w0 | wake | When Freyja hides her necklace, stands near the hearth, and the ravens rest, upper fjord: the gardens stir.
step=5, a=r1, b=d1, c=m1, e=w0 | sleep | When Freyja polishes her necklace, stands behind the veil, and the ravens rest, lower fjord: the gardens sleep.
step=6, a=r0, b=d1, c=m0, e=w0 | sleep | When Freyja hides her necklace, stands behind the veil, and the ravens rest, upper fjord: the gardens sleep.

## Scoreboard

agent | truth score | prediction | transfer reach | explanation score | hard-to-vary | criticizability | error-correction
--- | ---: | ---: | ---: | ---: | ---: | ---: | ---:
Deutsch critique loop | 1.000 | 1.000 | 1.000 | 0.493 | 0.833 | 0.458 | 0.000
myth-preserving storyteller | 0.524 | 0.550 | 0.475 | 0.058 | 0.000 | 0.167 | 0.000
pure prediction | 0.484 | 0.475 | 0.500 | 0.386 | 0.820 | 0.167 | 0.000
no-critique conjecture | 0.449 | 0.475 | 0.400 | 0.325 | 0.667 | 0.167 | 0.000

## Runs

### myth-preserving storyteller

Initial explanation: **Freyja's moods**

The factor_a changes because Freyja alternates between hiding and revealing her favor. New outcomes can be absorbed as new moods.

Final explanation: **Freyja's moods**

The factor_a changes because Freyja alternates between hiding and revealing her favor. New outcomes can be absorbed as new moods.

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

### no-critique conjecture

Initial explanation: **cycle-only**

The first plausible causal conjecture is kept without asking for risky tests. The current explanation uses cycle. It is better when removing or changing one term damages predictions.

Final explanation: **cycle-only**

The first plausible causal conjecture is kept without asking for risky tests. The current explanation uses cycle. It is better when removing or changing one term damages predictions.

Falsifier: A decisive refutation would be an unobserved case where a close rival predicts a different outcome and the current explanation loses.

Critiques:
- No criticism pass was allowed, so weak spots remain untested.

Acquired observations:
- None

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
- step=7, a=r0, b=d1, c=m1, e=w1 -> bloom; When Freyja polishes her necklace, stands behind the veil, and the ravens quarrel, upper fjord: the gardens bloom.

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

### no-critique conjecture

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
