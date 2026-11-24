# Pacman Classroom

A small Python grid world for teaching states, actions, reflex decisions, search,
heuristics and replanning. No ghosts, networking, external assets or third-party
Python packages. Game rules, agent decisions and rendering are separate.

## Start here

Use Python 3.10 or newer with Tkinter. Extract the ZIP, open a terminal inside
`PacmanClassroom`, then run:

```sh
python explore.py
```

Click **Start**, click the maze if keyboard focus is in a control, and use the
arrow keys. `L`, `R`, `D`, `U` also work; `S` or Space means wait. Holding a key
continues movement. Releasing it means waiting, which still costs points.
Escape pauses. There is no cost while paused or while an agent computes.

On Windows, `py` can replace `python`. The normal Python desktop installer
includes Tcl/Tk. On Debian/Ubuntu, install `python3-tk` if it is missing.
`python -m tkinter` is a quick installation check. No pip install is required.

## Editable classroom runner

Edit **explore.py**. It contains explicit-array and random-world examples.
The only difference between human and agent play is the argument to `play`:

```python
from pacman_lab import Pacman
from pacman_lab.agents import MSTPlanningAgent, BeamReplanningAgent

pacman = Pacman.special(4)
pacman.play()                              # human
# pacman.play(MSTPlanningAgent())          # complete plan
# pacman.play(BeamReplanningAgent(depth=10)) # batches of up to 10 moves
```

Choose just one play line per run. Full planning happens inside `init` before
the first game step; later calls return stored actions. Replanning calls `plan`
again when its stored batch is empty.

## Command-line examples

```sh
python run.py --special 4 --agent manhattan
python run.py --special 4 --agent memory
python run.py --special 4 --agent bfs
python run.py --special 4 --agent astar-mst
python run.py --special 5 --agent replan-memory --depth 10 --beam-width 80
python run.py --random --width 25 --height 17 --foods 6 --seed 12 --start-score 200
python run.py --world 8 --foods 3 --seed 42 --agent astar-mst
python run.py --config examples/lesson_4.json --agent legal
python run.py --special 4 --agent astar-mst --headless
python run.py --random --seed 42 --print-config
python evaluate.py --special 4 --output comparison.csv
python run.py --help
```

`--tick-ms` changes the interval between game ticks (250 ms by default). Smaller
values play faster. `--start-score`, `--step-cost`, `--food-reward`, `--depth`,
`--beam-width`, `--max-expansions` and `--time-limit` configure scoring/search.
Search defaults to at most 200,000 expansions or 15 seconds per planning call
through run.py. `--max-steps` limits headless execution. `evaluate.py` compares
agents on exactly the same lesson configuration and optionally creates a CSV;
choose a new filename for each CSV. Search progress also prints to the terminal.

## World and entity arrays

All coordinates are zero-based **(row, column)**, never (x, y). Rows run downwards;
columns run rightwards. `0` is a wall and `1` is floor. Example:

```python
pacman = Pacman(
    gridWorld=[
        [0,0,0,0,0],
        [0,1,1,1,0],
        [0,1,0,1,0],
        [0,1,1,1,0],
        [0,0,0,0,0],
    ],
    foodPositions=[[1,3], [3,3]],
    agentPosition=(1,1),
    start_score=50, step_cost=1, food_reward=50,
)
pacman.play()
```

The array determines dimensions. It must be rectangular, at least 3 by 3, and
contain only integer 0/1 entries. Edge cells are forced to walls. Duplicate
foods collapse to one; food on walls or outside the map is ignored. An invalid
agent position is hidden and the game cannot start. Invalid coordinates are
reported rather than silently relocated. Unreachable food in manually supplied
maps is allowed: it is useful for demonstrating failure.

```python
Pacman(width=21, height=15, food_count=4, seed=42) # random maze + random entities
Pacman.world(1, food_count=4, seed=42)             # one of 10 fixed mazes
Pacman.special(1)                                # one of 6 authored lessons
```

Random mazes support dimensions 5–101, have connected floor space, and place
food on distinct reachable cells other than the starting cell. Seeds reproduce
the world and initial placements. Large maps are for exploration; full search
with many foods can exceed its budget.

## UI controls and raw configuration

- Select a lesson/world and press **Load**. Random maze opens the array editor.
- Choose human or an agent, then **Reset** and **Start** to change controller.
  `custom` means the agent instance passed to `play`, including its parameters.
- **Pause** freezes execution; **Start** resumes. **Stop** ends the session;
  **Reset** restores the initial world, food, agent and score.
- **Step** initializes on its first click; subsequent clicks request one agent
  action. In human mode Step performs `S` (a waiting tick).
- **Config / raw arrays** exposes editable JSON. Copy arrays, save/load JSON,
  inspect the current state, or generate new random arrays. **Apply & reset**
  validates and normalizes the configuration.
- Scoring is editable in the JSON `scoring` object: `start`, `step_cost`,
  `food_reward`. Tick interval is editable on the main toolbar.
- Sound is optional. Wall bumps shake/flash Pacman and display BONK.

The maze fills the central viewport and grows with the window; grid cells may
be rectangular to use the available space. At the default 1280×900 size the
maze viewport occupies over 80% of the window. Maximize for projection.

## Exact tick and score rules

Each tick: request one action, attempt the move, deduct the tick cost, collect
any food and its reward, then test termination. Wall bumps and `S` also cost a
tick. Actions are case-insensitive. Unknown actions stop with an error.

`new_score = old_score - step_cost + food_reward * food_collected`

The food reward is applied before checking zero score. If the resulting score
is <= 0, the game loses; otherwise an empty food set wins. Loss takes precedence
if both conditions hold. Food under the initial position is collected at time
zero, without movement cost. Starting with no food wins immediately when the
agent position is valid. Terminal games do not keep ticking.

Simulation ticks are separate from real time. Thinking and pause consume no
simulation ticks. While running manually, doing nothing consumes waiting ticks.

## Agent files

All agents are under **pacman_lab/agents/**.

| CLI name | Class | File | Decision rule |
|---|---|---|---|
| manhattan | ManhattanReflexAgent | reflex.py | Nearest food by Manhattan distance; ignores walls |
| euclidean | EuclideanReflexAgent | reflex.py | Nearest food by Euclidean distance; ignores walls |
| axis | AxisFirstReflexAgent | reflex.py | Move along the column difference first, then row |
| legal | LegalMoveReflexAgent | model_reflex.py | Only legal moves, then nearest-food Manhattan score |
| walls | WallPenaltyReflexAgent | model_reflex.py | Add a penalty for sampled walls along the line to food |
| memory | MemoryReflexAgent | model_reflex.py | Also penalize revisiting cells |
| bfs | BFSPlanningAgent | planning.py | Breadth-first collect-all graph search |
| ucs | UCSPlanningAgent | planning.py | Uniform-cost search; each move costs one |
| astar-nearest | NearestAStarPlanningAgent | planning.py | A* with nearest-food Manhattan lower bound |
| astar-mst | MSTPlanningAgent | planning.py | A* with nearest food plus food spanning-tree lower bound |
| replan-depth | DepthReplanningAgent | replanning.py | Search non-cyclic state paths up to a depth budget |
| replan-beam | BeamReplanningAgent | replanning.py | Limit candidates at each depth using a beam |
| replan-memory | MemoryReplanningAgent | replanning.py | Beam search with a revisit penalty |

`search.py` holds the shared search functions; `base.py` defines the interface.
The small agent subclasses select strategies rather than duplicating the engine.
See **TEACHING_GUIDE.md** for formulas, examples and limits.

## Write your own agent

```python
class MyAgent:
    def init(self, agentPosition, foodPositions, gridWorld):
        self.grid = gridWorld

    def nextAction(self, agentPosition, foodPositions):
        return 'R'
```

Use `pacman.play(MyAgent())`. Subclassing is optional; **custom_agent.py** is a
minimal starting point. Positions are tuples; foodPositions is a list of tuples;
gridWorld is a list of rows. Treat inputs as read-only snapshots. The grid is
supplied once because walls are static. Current position/remaining food are
supplied every tick. The engine removes food and resolves walls.

Agents run in a worker thread so the UI remains responsive. Built-in planners
check cancellation. Stop/reset discards stale results. An arbitrary custom agent
that never returns cannot be forcibly killed by a Python thread; the window can
still close, but a new session waits for that worker to return. Never manipulate
Tk widgets from an agent method.

## Project map and checks

`core.py`: rules and state. `worlds.py`: maps and generation. `pacman.py`: public
API. `ui.py`: rendering and input. `formatting.py`: readable raw JSON.

```sh
python -m unittest discover -s tests -v
```

Tests cover normalization, scoring, invalid positions, connectivity, agent
contracts, search failure/budgets and shortest-plan agreement. Keyboard play,
pause/reset/stop, agent execution, editor and resizing were also exercised in a
Linux Tk desktop. Windows/macOS native behaviour was not independently tested.

This project uses original code and simple drawn shapes; it is a teaching grid
world, not a reproduction of the commercial game's assets or rules.
