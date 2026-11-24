"""Pure grid rules. No GUI and no agent-specific decisions live here."""
from dataclasses import dataclass
import math

ACTIONS = {'L': (0, -1), 'R': (0, 1), 'D': (1, 0), 'U': (-1, 0), 'S': (0, 0)}
MOVES = ('U', 'R', 'D', 'L')  # Fixed order makes demonstrations repeatable.


def normalize_grid(grid):
    if not isinstance(grid, (list, tuple)) or len(grid) < 3:
        raise ValueError('Grid needs at least 3 rows.')
    if not isinstance(grid[0], (list, tuple)) or len(grid[0]) < 3:
        raise ValueError('Grid needs at least 3 columns.')
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError('Grid must be rectangular.')
    if any(type(v) is not int or v not in (0, 1) for row in grid for v in row):
        raise ValueError('Grid cells must be integers 0 (wall) or 1 (floor).')
    result = [list(row) for row in grid]
    for r in range(len(result)):
        for c in range(width):
            if r in (0, len(result)-1) or c in (0, width-1):
                result[r][c] = 0
    return result


def coordinate(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2 or any(type(x) is not int for x in value):
        raise ValueError('Positions must be [row, column] integer pairs.')
    return tuple(value)


def is_free(grid, pos):
    return pos is not None and 0 <= pos[0] < len(grid) and 0 <= pos[1] < len(grid[0]) and grid[pos[0]][pos[1]] == 1


def move(grid, pos, action):
    dr, dc = ACTIONS[action]
    candidate = (pos[0]+dr, pos[1]+dc)
    return candidate if is_free(grid, candidate) else pos


def neighbors(grid, pos):
    for action in MOVES:
        nxt = move(grid, pos, action)
        if nxt != pos:
            yield action, nxt


@dataclass(frozen=True)
class Scoring:
    start: float = 50
    step_cost: float = 1
    food_reward: float = 50

    def __post_init__(self):
        for value in (self.start, self.step_cost, self.food_reward):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError('Scoring values must be finite numbers.')
        if self.start <= 0 or self.step_cost <= 0 or self.food_reward < 0:
            raise ValueError('Start and step cost must be positive; food reward cannot be negative.')


class Game:
    def __init__(self, grid, foods, agent_position, scoring=None):
        self.grid = normalize_grid(grid)
        self.scoring = scoring or Scoring()
        self.warnings = []
        if any(list(a) != b for a, b in zip(grid, self.grid)):
            self.warnings.append('Open boundary cells were converted to walls.')
        self.foods = set()
        for raw in foods:
            pos = coordinate(raw)
            if is_free(self.grid, pos):
                self.foods.add(pos)
            else:
                self.warnings.append(f'Ignored food on wall/outside grid: {pos}.')
        pos = coordinate(agent_position) if agent_position is not None else None
        self.position = pos if is_free(self.grid, pos) else None
        if self.position is None:
            self.warnings.append('Agent is not on a free cell: hidden; play is disabled.')
        self.score = self.scoring.start
        self.tick = 0
        self.eaten = 0
        self.last_action = 'S'
        self.status = 'ready'
        # Occupying a food cell at time zero counts as collecting that food.
        if self.position in self.foods:
            self.foods.remove(self.position)
            self.score += self.scoring.food_reward
            self.eaten += 1
        if self.position is None:
            self.status = 'invalid'
        elif not self.foods:
            self.status = 'won'

    def step(self, action):
        if self.status not in ('ready', 'running'):
            return {'bump': False, 'ate': False}
        if not isinstance(action, str) or action.upper() not in ACTIONS:
            raise ValueError(f'Invalid action {action!r}; expected L, R, D, U or S.')
        action = action.upper()
        old = self.position
        self.position = move(self.grid, old, action)
        self.last_action = action
        self.tick += 1
        self.score -= self.scoring.step_cost
        ate = self.position in self.foods
        if ate:
            self.foods.remove(self.position)
            self.eaten += 1
            self.score += self.scoring.food_reward
        # Loss wins a simultaneous tie: all food collected with <=0 score is a loss.
        self.status = 'lost' if self.score <= 0 else ('won' if not self.foods else 'running')
        return {'bump': action != 'S' and old == self.position, 'ate': ate}

    def raw(self):
        return {'grid': [row[:] for row in self.grid], 'foods': [list(p) for p in sorted(self.foods)],
                'agent': list(self.position) if self.position is not None else None,
                'scoring': {'start': self.scoring.start, 'step_cost': self.scoring.step_cost,
                            'food_reward': self.scoring.food_reward}}
