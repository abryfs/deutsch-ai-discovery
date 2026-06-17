# Deutsch-Style AI Discovery Benchmark

Seeds: `1` through `50`
Runs: `50`
Rounds per run: `4`

## Aggregate Scores

agent | wins | avg truth | stdev truth | avg prediction | avg transfer reach | avg explanation | avg criticizability
--- | ---: | ---: | ---: | ---: | ---: | ---: | ---:
Deutsch critique loop | 32 | 0.638 | 0.252 | 0.635 | 0.643 | 0.596 | 0.806
pure prediction | 6 | 0.447 | 0.117 | 0.455 | 0.433 | 0.386 | 0.167
no-critique conjecture | 9 | 0.419 | 0.091 | 0.424 | 0.411 | 0.325 | 0.167
myth-preserving storyteller | 3 | 0.380 | 0.118 | 0.384 | 0.374 | 0.058 | 0.167

## Failure Cases

A failure case is any seed where the Deutsch critique loop does not rank first.

seed | winner | Deutsch rank | Deutsch truth | winning truth
--- | --- | ---: | ---: | ---:
1 | no-critique conjecture | 3 | 0.315 | 0.565
2 | no-critique conjecture | 3 | 0.383 | 0.417
3 | pure prediction | 4 | 0.355 | 0.652
4 | no-critique conjecture | 2 | 0.367 | 0.550
7 | pure prediction | 3 | 0.432 | 0.465
11 | no-critique conjecture | 2 | 0.512 | 0.525
13 | pure prediction | 3 | 0.518 | 0.518
15 | pure prediction | 2 | 0.353 | 0.353
16 | no-critique conjecture | 2 | 0.550 | 0.550
18 | no-critique conjecture | 4 | 0.302 | 0.585
23 | myth-preserving storyteller | 2 | 0.733 | 0.733
25 | no-critique conjecture | 2 | 0.417 | 0.445
28 | no-critique conjecture | 2 | 0.383 | 0.468
32 | myth-preserving storyteller | 4 | 0.365 | 0.435
36 | pure prediction | 2 | 0.453 | 0.565
43 | pure prediction | 2 | 0.415 | 0.518
44 | myth-preserving storyteller | 2 | 0.353 | 0.547
49 | no-critique conjecture | 2 | 0.235 | 0.335

## Per-Seed Winners

seed | winner | winning truth score
--- | --- | ---:
1 | no-critique conjecture | 0.565
2 | no-critique conjecture | 0.417
3 | pure prediction | 0.652
4 | no-critique conjecture | 0.550
5 | Deutsch critique loop | 0.848
6 | Deutsch critique loop | 1.000
7 | pure prediction | 0.465
8 | Deutsch critique loop | 0.550
9 | Deutsch critique loop | 0.615
10 | Deutsch critique loop | 0.950
11 | no-critique conjecture | 0.525
12 | Deutsch critique loop | 0.682
13 | pure prediction | 0.518
14 | Deutsch critique loop | 0.518
15 | pure prediction | 0.353
16 | no-critique conjecture | 0.550
17 | Deutsch critique loop | 1.000
18 | no-critique conjecture | 0.585
19 | Deutsch critique loop | 1.000
20 | Deutsch critique loop | 0.782
21 | Deutsch critique loop | 0.503
22 | Deutsch critique loop | 0.432
23 | myth-preserving storyteller | 0.733
24 | Deutsch critique loop | 0.682
25 | no-critique conjecture | 0.445
26 | Deutsch critique loop | 1.000
27 | Deutsch critique loop | 1.000
28 | no-critique conjecture | 0.468
29 | Deutsch critique loop | 1.000
30 | Deutsch critique loop | 1.000
31 | Deutsch critique loop | 0.400
32 | myth-preserving storyteller | 0.435
33 | Deutsch critique loop | 0.900
34 | Deutsch critique loop | 0.870
35 | Deutsch critique loop | 0.965
36 | pure prediction | 0.565
37 | Deutsch critique loop | 0.730
38 | Deutsch critique loop | 1.000
39 | Deutsch critique loop | 0.370
40 | Deutsch critique loop | 0.780
41 | Deutsch critique loop | 0.600
42 | Deutsch critique loop | 1.000
43 | pure prediction | 0.518
44 | myth-preserving storyteller | 0.547
45 | Deutsch critique loop | 0.617
46 | Deutsch critique loop | 0.498
47 | Deutsch critique loop | 0.635
48 | Deutsch critique loop | 1.000
49 | no-critique conjecture | 0.335
50 | Deutsch critique loop | 0.522