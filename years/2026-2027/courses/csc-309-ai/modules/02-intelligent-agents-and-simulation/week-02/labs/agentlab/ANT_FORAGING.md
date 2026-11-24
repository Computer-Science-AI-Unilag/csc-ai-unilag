# Ant foraging

A custom Python teaching model of indirect communication through pheromone trails. No Mesa, NetLogo or third-party Python packages are required. Python 3.10+ and Tcl/Tk are needed for the desktop interface.

## Start

Extract the ZIP, open a terminal in `AgentLab`, and run:

```bash
python ants.py
python ants.py --ants 150 --foods 6 --food-units 120 --seed 42
python ants.py --autostart --speed 2
```

On Windows, `py` may replace `python`. Check desktop support with `python -m tkinter`. The existing `particles.py`, `agents.py` and `evaluate.py` programs remain available.

## Explore the interface

- **World:** ant count, number of randomly positioned food sources, food units at each source, random seed and physical ant speed.
- **Behaviour:** sensing distance, sensor spread, steering angle, exploration probability, deposit rate, evaporation and diffusion. Disable pheromone communication to compare with independent searching.
- **View:** show or hide ants and the pheromone field; show the selected ant's sensors; adjust trail brightness without changing the model.
- **Apply settings & reset:** applies World and Behaviour edits and rebuilds the colony. **Reset seed** repeats the currently applied configuration. Change the seed to obtain a new food arrangement.
- **Start / Pause / Single step:** control progress. Pause takes effect after any small batch already running finishes. Escape also pauses.
- **Playback:** changes viewing speed without changing the fixed simulation timestep. High workloads may run more slowly than the requested multiplier.
- Click an ant to inspect its latest decision and deliveries. The graph records cumulative food delivered. Teal ants search; gold ants carry food; green circles are food sources; the purple circle is the nest.

The world scales with the window while retaining its physical dimensions and aspect ratio. Resizing does not relocate food or change the model. Settings panels scroll when space is limited.

## Behaviour and assumptions

1. Searching ants detect food locally. If food is within range, they approach it and pick up one unit on contact.
2. Otherwise they sample pheromone ahead, left and right. A usable signal usually makes them steer towards the strongest sample; exploration produces a random turn. Without a signal they also turn randomly.
3. Loaded ants know the direction of the nest and return directly. They deposit pheromone outside the nest zone, with deposit strength declining as the return trip progresses. This creates a stronger signal nearer the food.
4. At the nest they deliver their unit, turn around and resume searching. Other ants can follow the shared trail and reinforce it after finding food themselves.
5. Diffusion spreads the existing field between adjacent cells; evaporation weakens it; new deposits are then added. All ants sense the previous field, so deposits affect decisions on the next tick.

This is **stigmergy**: one ant changes the environment, and another responds to that change. Ants do not exchange food coordinates or use a global food map. Nest direction is idealised built-in knowledge. Ant-ant collisions, obstacles, biological chemistry and shortest-path guarantees are not modelled. This foraging model is not the discrete Ant Colony Optimisation algorithm for graph problems.

Strong trails appear brighter; diffusion broadens them. When a source runs out, an old trail may attract ants until it fades. The display uses a nonlinear colour scale; brightness is not a linear measure of concentration. The run ends when every food unit has been delivered.

## Command-line settings

Use `python ants.py --help` to list all options. Each tick represents 1/30 simulated second. The world measures 1.5 by 1 world unit, with a 90 by 60 pheromone grid.

| Option | Default | Meaning |
|---|---:|---|
| `--ants` | 100 | Number of ants, 1–500 |
| `--foods` | 4 | Random food sources, 1–12 |
| `--food-units` | 100 | Units per source, 1–2000 |
| `--seed` | 42 | Repeatable random initialisation |
| `--ant-speed` | 0.12 | World units per simulated second |
| `--sensor-distance` | 0.045 | Pheromone sample distance in world units |
| `--sensor-angle` | 40 | Left/right sensor offset in degrees |
| `--turn-angle` | 18 | Steering turn in degrees per tick; random turns lie within this range |
| `--exploration` | 0.12 | Probability of exploring despite a usable trail |
| `--deposit` | 5 | Initial pheromone deposition rate per simulated second |
| `--evaporation` | 0.12 | Exponential decay constant per simulated second |
| `--diffusion` | 1.2 | Diffusion rate per simulated second |
| `--no-pheromones` | off | Disable both deposition and trail sensing |
| `--speed` | 1 | Playback multiplier, 0.1–8; no effect on headless results |

Food detection range is fixed at 0.055 world units; pickup contact range is 0.025. Sensing distance controls pheromone sampling, not food detection. Direct food approach and nest homing use ideal direction knowledge rather than the exploratory steering limit.

## Non-visual experiments

```bash
python ants.py --headless --runs 100 --steps 6000 --seed 42 --output trails.csv
python ants.py --headless --runs 100 --steps 6000 --seed 42 --no-pheromones --output baseline.csv
python ants.py --headless --runs 20 --ants 150 --foods 6 --evaporation 0.2 --exploration 0.1 --output experiment.csv
```

Each run uses `seed + run_index`. Match seeds and all other settings when comparing communication on/off. Random food layouts are matched; subsequent random decisions can diverge between conditions. Headless mode does not open a window or import Tk.

The terminal reports mean, minimum, maximum and population standard deviation of delivered food, plus completed runs. CSV rows include delivered food, remaining food, food being carried, elapsed steps, completion status and the first delivery step. Runs stop at the step limit or when all food is delivered. The adjacent `.csv.config.json` records the configuration. Choose a new output filename each time; existing results are not overwritten.

Higher food delivery at a common step limit is better. If both conditions deliver all food, compare completion steps among completed runs and also report the completion fraction. A run that reaches its limit unfinished has not demonstrated its full completion time. First-delivery time is not total collection time.

## Code map

- `ants.py`: entry point.
- `agentlab/foraging/model.py`: simulation state, decisions and pheromone field; independent of the GUI.
- `agentlab/foraging/ui.py`: responsive Tk interface, drawing and worker scheduling.
- `agentlab/foraging/cli.py`: argument parsing and batch results.
- `tests/test_foraging.py`: deterministic model and conservation checks.
- `docs/Ant_Foraging_Flowcharts.pdf`: three presentation pages explaining discovery, individual decisions and shared signals.

Run checks with `python -m unittest discover -s tests -v` from the project directory.
