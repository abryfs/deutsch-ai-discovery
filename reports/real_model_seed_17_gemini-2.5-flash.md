# Real Model Discovery Run

Model: `gemini-2.5-flash`
Seed: `17`
Truth score: `0.750`
Holdout accuracy: `0.750`
Transfer reach: `0.750`

## Explanation

Title: **Causal factors for garden states**

The gardens bloom if and only if Freyja polishes her necklace (a=r1), stands near the hearth (b=d0), the ravens rest (c=m0), and it is the lower fjord (e=w0).
The gardens sleep if Freyja polishes her necklace (a=r1) and the ravens quarrel (c=m1), AND either she stands near the hearth in the upper fjord (b=d0, e=w1) OR she stands behind the veil in the lower fjord (b=d1, e=w0).
In all other circumstances, the gardens stir (wake).

Falsifier: None

## Hidden World Revealed

`seed=17, family=interaction, period=10, axial_phase=4, heat_lag=2, weights=(axial=2.37, distance=0.71, moon=-0.32, wind=0.25, interaction=0.98)`