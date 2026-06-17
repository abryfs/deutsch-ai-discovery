# Multi-Round Real Model Discovery Run

Model: `gemini-2.5-flash`
Seed: `17`
Rounds: `3`
Truth score: `0.750`
Holdout accuracy: `0.750`
Transfer reach: `0.750`

## Oracle Loop

- Round 1: step=8, a=r1, b=d1, c=m1, e=w1 -> wake; When Freyja polishes her necklace, stands behind the veil, and the ravens quarrel, lower fjord: the gardens stir.
- Round 2: step=0, a=r0, b=d1, c=m1, e=w0 -> wake; When Freyja polishes her necklace, stands behind the veil, and the ravens rest, upper fjord: the gardens stir.
- Round 3: step=5, a=r1, b=d1, c=m0, e=w0 -> wake; When Freyja hides her necklace, stands behind the veil, and the ravens rest, lower fjord: the gardens stir.

## Final Explanation

Title: **Fjord Location, Freyja's Necklace and Stance, and Ravens' State Determine Garden Outcome**

The gardens bloom only when it is the lower fjord (a=r1), Freyja stands near the hearth (b=d0), hides her necklace (c=m0), and the ravens rest (e=w0). The gardens sleep when it is the lower fjord (a=r1), Freyja polishes her necklace (c=m1), and either she stands near the hearth (b=d0) while the ravens quarrel (e=w1), or she stands behind the veil (b=d1) while the ravens rest (e=w0). In all other circumstances, the gardens stir (wake).

Falsifier: None

## Hidden World Revealed

`seed=17, family=interaction, period=10, axial_phase=4, heat_lag=2, weights=(axial=2.37, distance=0.71, moon=-0.32, wind=0.25, interaction=0.98)`