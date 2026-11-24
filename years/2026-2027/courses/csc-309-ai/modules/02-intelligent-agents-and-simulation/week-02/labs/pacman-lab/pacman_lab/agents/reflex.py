"""No lookahead: score immediate candidate positions using food coordinates only.
These agents intentionally ignore walls, so a greedy choice may repeatedly bump.
"""
import math
from .base import Agent, manhattan
from ..core import MOVES, ACTIONS

class SimpleReflexAgent(Agent):
    distance = staticmethod(manhattan)

    def init(self, agentPosition, foodPositions, gridWorld):
        self.stats = {}

    def nextAction(self, agentPosition, foodPositions):
        if not foodPositions:
            return 'S'
        r, c = agentPosition
        def score(action):
            dr, dc = ACTIONS[action]
            return min(self.distance((r+dr,c+dc), f) for f in foodPositions)
        return min(MOVES, key=score)

class ManhattanReflexAgent(SimpleReflexAgent):
    """Greedy nearest-food Manhattan distance; ties use U,R,D,L."""

class EuclideanReflexAgent(SimpleReflexAgent):
    """Greedy straight-line distance; no wall knowledge."""
    distance = staticmethod(math.dist)

class AxisFirstReflexAgent(SimpleReflexAgent):
    """Pick the nearest Manhattan food; finish horizontal alignment first."""
    def nextAction(self, agentPosition, foodPositions):
        if not foodPositions:
            return 'S'
        target = min(foodPositions, key=lambda f: (manhattan(agentPosition,f),tuple(f)))
        r,c = agentPosition
        if c != target[1]:
            return 'R' if c < target[1] else 'L'
        if r != target[0]:
            return 'D' if r < target[0] else 'U'
        return 'S'
