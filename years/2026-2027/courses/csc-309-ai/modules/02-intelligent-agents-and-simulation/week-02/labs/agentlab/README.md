# AgentLab — Particles, Agents & Ant Foraging

The particle classroom programs share one modular Python simulation engine. A separate command-line evaluator runs matched-seed experiments without opening a window.

## Ant-foraging module

Run `python ants.py` for the new ant colony explorer. See [ANT_FORAGING.md](ANT_FORAGING.md) for settings, model assumptions and headless experiments. The three-page teaching PDF is in `docs/Ant_Foraging_Flowcharts.pdf`.

## Requirements

**Python 3.10+ with Tcl/Tk** for the desktop programs. No third-party pip dependencies. On Windows, enable the Python installer's **Tcl/Tk and IDLE** option. `python -m tkinter` checks Tk installation. On Linux, the distribution's `python3-tk` package may be needed. Headless evaluation does not import Tk and needs no display or internet.

Extract the archive and open a terminal inside `AgentLab`.

## 1. Passive particles

```bash
python particles.py
python particles.py --shape triangle --balls 40 --steps 5000
```

Pure physical particles: **no sensing, decision policy or steering**. Default mode is experiment, which continues to the step limit and counts contacts. Wall bounces and particle collisions remain physical interactions.

## 2. Agents

```bash
python agents.py
python agents.py --shape circle --balls 24 --policy predictive_robust --horizon 20 --angle 5 --sensing-radius 0.15
python agents.py --no-sensing --mode experiment
python agents.py --paused --seed 123
```

The agent program opens paused so you can choose settings before the first collision. Click Start, or pass `--autostart`. The passive program starts automatically unless `--paused` is supplied.

Default settings: 24 particles, square, seed 42, radius 0.012, sensing enabled, sensing radius 0.15, 5° turn, predictive robust policy, **horizon 1**, maximum 1,000 steps, survival mode.

`run.py` and `python -m agentlab` launch the agent program. `python run.py --program particles` chooses passive mode; add `--mode experiment` for a full-duration baseline. The dedicated `particles.py` already defaults to experiment mode.

On Windows, `py` can replace `python`. Absolute script paths work from other working directories.

## Desktop controls

| Control | Behaviour |
|---|---|
| Start / Stop | Resume / pause at a completed physics tick |
| Single step | Pause and advance one simulation tick |
| Reset | Repeat the currently applied configuration and seed |
| Playback speed | Live 0.1×–4× viewing speed; never changes the timestep |
| World tab | Shape, count, seed, particle radius, maximum steps and run mode |
| Agents tab | Sensing switch, policy, sensing radius, steering angle and horizon |
| View tab | Trails, velocity arrows, particle numbers, selected sensor range and forecast path |
| Apply settings & reset | Apply configuration changes and restart the experiment from step zero |
| Click a particle | Inspect its speed, observed neighbour count, threat count and last decision |
| Show / hide settings | Give the world more room, useful for projection |
| Space / Escape | Toggle playback / stop |

Settings other than playback speed and View options apply when you click **Apply settings & reset**. This also applies to the sensing checkbox. Disabling sensing makes every particle continue without deliberate steering, exactly reproducing the passive baseline for the same seed and configuration.

The bounded shape expands to fit the available canvas while preserving its geometry: circles stay circular, triangles stay equilateral, and squares stay square. Wide windows may retain empty space around these shapes. The settings tabs scroll on smaller screens. Resizing changes rendering only, not world dimensions, particle density, scores or physics.

### Run modes

- **survival:** stop after the physics tick containing the first particle–particle collision. Highlight the colliding pair(s). Higher survival steps is better.
- **experiment:** run through the maximum steps, recording the first collision and all distinct particle collision events. Lower collision count is better.
- Wall collisions do not end a run and do not count against either score.
- A run ending without collision is **censored at the limit**. “Survived 1,000 steps” does not claim that failure would occur at step 1,000.

The fixed timestep is **1/240 simulated second**. 1,000 steps is approximately 4.17 simulated seconds. Playback speed affects viewing duration only. A busy computer may run below the requested playback rate; the UI reports workload limiting instead of skipping simulation steps or enlarging dt.

## 3. Evaluate policies without animation

Default: **100 runs per policy**, including the passive baseline (500 runs total).

```bash
python evaluate.py
```

Configure the experiment:

```bash
python evaluate.py --runs 100 --steps 1000 --seed 42 --horizon 20 --shape square --balls 24 --angle 5 --sensing-radius 0.15 --workers 2 --output results_h20
```

For a collision-count experiment:

```bash
python evaluate.py --runs 100 --steps 1000 --mode experiment --horizon 20 --workers 2 --output results_collisions
```

Select policies or test sensing disabled:

```bash
python evaluate.py --policies passive predictive_robust --runs 100 --horizon 20 --output comparison
python evaluate.py --no-sensing --runs 10 --output sensing_off
```

A single non-visual run:

```bash
python agents.py --headless --horizon 20 --steps 1000
```

Use `--help` on any script for all options. Evaluation runs in its own process, independently of the interactive explorer. `--workers 2` uses two worker processes; default is one. No animation is rendered. Avoid using all available CPU cores if simultaneously teaching with the GUI.

### Fair seed matching

With `--seed 42 --runs 100`, **every policy uses seeds 42 through 141**. Each seed creates the same positions and velocities across policies. Steering randomness is independent of initialization and indexed by seed, step and particle ID. Worker scheduling and playback do not change random decisions. This compares a varied, paired seed set rather than repeating the identical deterministic trial 100 times.

### Console results and files

Console summaries include mean, minimum, maximum, **population standard deviation**, limit-survival count and mean collisions. Scores are in **simulation steps**. Experiment mode additionally prints collision count min/max/SD.

Each output directory contains:

- `runs.csv`: one record per policy and seed, including capped survival steps/seconds, first collision step, censoring flag and collision/steering counts.
- `summary.csv`: aggregate survival and collision statistics by policy.
- `report.json`: full configuration, seed scheme inputs, fixed dt, statistic definitions and runtime.

Existing report files are not overwritten: use a fresh `--output` directory. Per-run rows are flushed as they finish; an interrupted batch leaves partial rows but no completed summary. Treat it as incomplete.

## Policies

| CLI name | Prediction horizon | Response to a predicted threat |
|---|---|---|
| `passive` | None | No sensing or steering |
| `reactive_random` | Always 1 | Random left or right turn |
| `reactive_robust` | Always 1 | Best worst-case action against neighbour responses |
| `predictive_random` | Configurable | Random left or right turn |
| `predictive_robust` | Configurable | Best worst-case action against neighbour responses |

“One-step” is the UI name for the reactive variants. At **horizon 1**, corresponding one-step and predictive variants intentionally behave identically.

All policies trigger only when the current no-steering forecast predicts a collision with an observed neighbour. Otherwise they continue straight. Robust variants evaluate left, straight and right against each reachable observed neighbour's left, straight and right responses. This includes neighbours that were not initially threats but could become threats after a turn.

The robust rule maximizes the worst outcome across those pairwise scenarios:

1. Prefer no predicted collision in every evaluated response.
2. If every action risks collision, prefer the latest worst-case first contact.
3. Break remaining ties using greater worst-case minimum surface clearance.
4. If equally scored, prefer straight; otherwise use reproducible random tie-breaking.

No policy is guaranteed collision-free. One-step warning may be too late for a 5° turn.

### Prediction assumptions

The forecast applies **one candidate turn now**, then projects constant-speed motion with wall reflections over the horizon. It tests contact continuously along each piecewise-linear forecast segment, including between sampled endpoints. It does not branch into future steering sequences. The next real tick observes and decides again.

Currently observed neighbours are projected for the whole horizon, even if the projected paths later leave the sensor range. New neighbours become available at the next actual observation. Hypothetical neighbour–neighbour collisions and resulting velocity changes are not modelled. Forecasts are conditional models, not guarantees.

Nearby pairs that cannot close their surface gap within the horizon even at the sum of their speeds are safely excluded from collision reasoning. This reduces work without removing a possible speed-preserving encounter in the model.

## Shared architecture

| File | Responsibility |
|---|---|
| `particles.py`, `agents.py`, `run.py` | Desktop / single-run entry points |
| `evaluate.py` | Batch-evaluation entry point, safe Windows process guard |
| `agentlab/cli.py` | Shared launch options and validation |
| `agentlab/evaluation.py` | Matched seeds, process workers, statistics and reports |
| `agentlab/core/vector.py` | Independent vector math |
| `agentlab/core/clock.py` | Reusable fixed-step clock utility |
| `agentlab/simulations/balls.py` | Physical particle state, collision response and event counting |
| `agentlab/simulations/boundaries.py` | Boundary constraints and geometry |
| `agentlab/simulations/motion.py` | Wall-aware projected paths, rotations, continuous forecast encounter tests |
| `agentlab/simulations/policies.py` | Agent settings, local sensing and action selection |
| `agentlab/simulations/session.py` | Shared decision/physics tick and experiment stop conditions |
| `agentlab/ui/app.py` | Responsive Tk shell and background worker |
| `agentlab/ui/renderer.py` | View projection, particle graphics and teaching overlays |

Policies never mutate the world during decision-making. All agents observe the same pre-action snapshot. The session applies their turns simultaneously, then advances physical motion. Desktop and evaluator call the **same Session.step()**.

The GUI worker owns the live session. The main thread renders published copies, keeping Tk operations on the main thread. Reset creates a new session and rejects stale worker results. Pause takes effect at a tick boundary. Future modules can reuse the vector, timing, session/worker pattern and UI conventions without coupling their algorithms to Tk.

## Limits and physical assumptions

- 1–120 particles; radius 0.005–0.018; sensing radius 0–2; angle 0–90°; horizon 1–240; maximum steps 1–1,000,000. Dense placement can fail gracefully rather than spawning overlaps.
- Positions use normalized world units. Shape areas differ, so changing shape also changes density at fixed particle count.
- Steering preserves each particle's speed. Physical particle collisions may change individual speeds while conserving total kinetic energy for equal-mass elastic collisions.
- The real solver uses discrete steps, adaptive subdivisions and iterative overlap correction. Forecast collision checks are continuous along projected paths, but the physical solver is not an exact event-driven hard-disc solver. Grazing/dense simultaneous contacts may show small numerical differences or transient overlap.
- Collision events are counted once per pair until their surfaces separate beyond a small tolerance. Persistent contact does not become a new event every solver iteration.
- Survival is reported at the containing **whole physics step**, not a fabricated exact sub-step impact time. In survival mode the engine finishes that tick; it may register multiple contacts in it.
- Sensor links in the UI describe the most recent decision snapshot. The displayed positions are after that step. Yellow forecast paths show a fresh projection from the displayed state.
- Robust reasoning can cost more at large radii, populations and horizons. It compares neighbour responses pairwise, not an exponential global action tree.

## Tests

```bash
python -m unittest discover -s tests -v
python -m compileall -q agentlab agents.py particles.py evaluate.py run.py
```

The desktop test skips when no display is available. See `VALIDATION.md` for the delivered checks and `TEACHING_GUIDE.md` for classroom use.

## Rectangular environment

Choose **Rectangle** in the World tab. Set **Rectangle width / height** and click **Apply settings & reset**. Default aspect ratio is **1.6**; 2 means twice as wide as high, and 0.5 means twice as high as wide. Supported range is 0.5–3. The setting is ignored by other shapes, but must remain valid.

```bash
python particles.py --shape rectangle --aspect-ratio 2
python agents.py --shape rectangle --aspect-ratio 2 --balls 16 --horizon 20
python evaluate.py --shape rectangle --aspect-ratio 2 --balls 16 --runs 100 --horizon 20 --output rectangle_results
```

The rectangle expands or contracts to fit the available canvas at the chosen ratio. Hide the settings panel to give it more space. Resizing does not stretch particles, change the physical world or alter results. Changing the aspect ratio **does** change world geometry and area, and resets the experiment. Match the ratio between interactive and batch comparisons. Wall-aware prediction and collision physics use the same rectangle geometry.
