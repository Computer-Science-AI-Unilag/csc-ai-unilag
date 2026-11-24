# Validation for the agent upgrade

Tested on Linux with Python 3.12. Native Windows/macOS desktop testing remains outstanding.

## Automated checks

**24 tests passed**, including the desktop integration test under a virtual X display:

- Original physical response: momentum/energy, wall reflection, equilateral geometry, high-speed substeps and 120-particle containment.
- Steering preserves speed; sensing disabled exactly matches passive physics.
- All policies receive identical initial states for a matched seed.
- One-step and predictive variants produce identical trajectories when horizon = 1.
- Local sensing excludes out-of-range particles; decision calculation does not mutate the snapshot.
- Robust choice agrees with the evaluated worst-case scores.
- Forecasts detect contact between endpoints and after wall reflection.
- First collision stops survival mode, marks the pair and records the containing step.
- Collision-free trials stop at the limit with a censoring flag; solver iterations do not multiply encounter counts.
- Mean/min/max/population-standard-deviation calculations.
- Desktop settings, step/reset, start/stop, invalid input handling, sensing switch, resizing and panel hiding.

Both desktop programs were launched and visually inspected at normal and smaller window sizes. Background simulation publishes copies to the UI. Desktop tests and successive launch checks use main-thread collection between separate Tk roots in the test harness.

## Non-visual evaluations

Completed **100 runs for each of five policies** at horizon 1 (500 trials), and another **100 per policy** at horizon 20 (500 trials). All used seeds 42–141, 24 particles, square, 1,000-step survival limit, sensing radius 0.15 and 5° steering.

The horizon-20 reports are included under `sample_results/horizon_20/`. They are actual measured output for this exact setup, not general performance guarantees:

| Policy | Mean capped survival steps | Minimum | Maximum | Population SD | Reached 1,000 without contact |
|---|---:|---:|---:|---:|---:|
| Passive | 66.65 | 2 | 285 | 54.82 | 0/100 |
| One-step random | 66.70 | 2 | 285 | 54.84 | 0/100 |
| One-step robust | 71.56 | 2 | 322 | 64.18 | 0/100 |
| Predictive random | 98.43 | 2 | 464 | 88.81 | 0/100 |
| Predictive robust | 948.18 | 2 | 1,000 | 209.10 | 93/100 |

At horizon 1, predictive results matched their corresponding one-step variants, as intended. A separate 10-seed repeated evaluation matched all 50 corresponding per-trial results exactly. Experiment mode was also checked with two worker processes and outputs collision count mean/min/max/SD.

Do not interpret censored survival scores as actual failure times. These benchmarks measure the implemented teaching model and its numerical collision solver. Changing density, shape, sensor range, angle or horizon may change the rankings.

## Rectangle update

All **27 tests passed** with the new rectangle geometry, including the desktop test. Checked landscape and portrait aspect ratios, containment, wall-aware projection, agent sessions, desktop resizing without state changes, and rectangle CLI evaluation. The rectangle interface was visually inspected at normal and smaller sizes. Earlier sample benchmark reports remain square-world experiments.

## Ant-foraging extension (11 November 2026)

- Full suite: 34 tests, 33 passed and one existing desktop-only test skipped without a display.
- Separate desktop smoke check on a virtual X display: start, pause, reset, apply settings, single step and resizing to 880×620 passed.
- Two default headless runs (seeds 42 and 43) collected all 400 food units in 2,543 and 3,482 steps respectively. These are smoke checks, not evidence of superiority over a baseline.
- CLI decimal settings and CSV/config export checked.
- Three-page PDF rendered and visually inspected; text boxes checked for overflow.
- Native Windows/macOS execution was not tested in this environment.
