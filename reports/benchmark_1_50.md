# Deutsch-Style AI Discovery Benchmark

Seeds: `1` through `50`
Runs: `50`
Rounds per run: `4`

## Aggregate Scores

agent | wins | avg truth | stdev truth | avg prediction | avg transfer reach | avg explanation | avg criticizability
--- | ---: | ---: | ---: | ---: | ---: | ---: | ---:
Deutsch critique loop | 32 | 0.631 | 0.254 | 0.640 | 0.613 | 0.616 | 0.835
pure prediction | 7 | 0.424 | 0.081 | 0.422 | 0.427 | 0.386 | 0.167
no-critique conjecture | 8 | 0.404 | 0.083 | 0.400 | 0.411 | 0.325 | 0.167
myth-preserving storyteller | 3 | 0.370 | 0.104 | 0.366 | 0.377 | 0.058 | 0.167

## Failure Cases

A failure case is any seed where the Deutsch critique loop does not rank first.

seed | winner | Deutsch rank | Deutsch truth | winning truth
--- | --- | ---: | ---: | ---:
1 | no-critique conjecture | 3 | 0.349 | 0.451
2 | myth-preserving storyteller | 2 | 0.406 | 0.443
3 | pure prediction | 3 | 0.514 | 0.539
7 | no-critique conjecture | 2 | 0.474 | 0.474
9 | pure prediction | 3 | 0.390 | 0.457
11 | no-critique conjecture | 2 | 0.571 | 0.571
16 | no-critique conjecture | 2 | 0.560 | 0.560
18 | no-critique conjecture | 4 | 0.384 | 0.540
21 | pure prediction | 2 | 0.426 | 0.444
25 | no-critique conjecture | 2 | 0.401 | 0.401
28 | no-critique conjecture | 4 | 0.265 | 0.432
31 | pure prediction | 4 | 0.314 | 0.389
32 | myth-preserving storyteller | 3 | 0.385 | 0.443
36 | pure prediction | 2 | 0.468 | 0.568
43 | pure prediction | 4 | 0.320 | 0.427
44 | myth-preserving storyteller | 4 | 0.407 | 0.625
45 | pure prediction | 3 | 0.336 | 0.499
46 | no-critique conjecture | 3 | 0.335 | 0.376

## Per-Seed Winners

seed | winner | winning truth score
--- | --- | ---:
1 | no-critique conjecture | 0.451
2 | myth-preserving storyteller | 0.443
3 | pure prediction | 0.539
4 | Deutsch critique loop | 0.620
5 | Deutsch critique loop | 0.801
6 | Deutsch critique loop | 0.975
7 | no-critique conjecture | 0.474
8 | Deutsch critique loop | 0.589
9 | pure prediction | 0.457
10 | Deutsch critique loop | 0.984
11 | no-critique conjecture | 0.571
12 | Deutsch critique loop | 0.657
13 | Deutsch critique loop | 0.438
14 | Deutsch critique loop | 0.609
15 | Deutsch critique loop | 0.416
16 | no-critique conjecture | 0.560
17 | Deutsch critique loop | 1.000
18 | no-critique conjecture | 0.540
19 | Deutsch critique loop | 1.000
20 | Deutsch critique loop | 0.681
21 | pure prediction | 0.444
22 | Deutsch critique loop | 0.457
23 | Deutsch critique loop | 0.623
24 | Deutsch critique loop | 0.958
25 | no-critique conjecture | 0.401
26 | Deutsch critique loop | 1.000
27 | Deutsch critique loop | 1.000
28 | no-critique conjecture | 0.432
29 | Deutsch critique loop | 1.000
30 | Deutsch critique loop | 0.974
31 | pure prediction | 0.389
32 | myth-preserving storyteller | 0.443
33 | Deutsch critique loop | 0.949
34 | Deutsch critique loop | 0.797
35 | Deutsch critique loop | 0.950
36 | pure prediction | 0.568
37 | Deutsch critique loop | 0.750
38 | Deutsch critique loop | 1.000
39 | Deutsch critique loop | 0.451
40 | Deutsch critique loop | 0.568
41 | Deutsch critique loop | 0.409
42 | Deutsch critique loop | 1.000
43 | pure prediction | 0.427
44 | myth-preserving storyteller | 0.625
45 | pure prediction | 0.499
46 | no-critique conjecture | 0.376
47 | Deutsch critique loop | 0.666
48 | Deutsch critique loop | 1.000
49 | Deutsch critique loop | 0.359
50 | Deutsch critique loop | 0.550