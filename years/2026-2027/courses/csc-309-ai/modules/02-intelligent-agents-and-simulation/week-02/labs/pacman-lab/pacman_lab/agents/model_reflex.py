"""Immediate-action heuristics using a stored map; no forward action-tree search.
Map awareness alone is not belief-state inference: the supplied map is complete.
MemoryReflexAgent additionally updates a small history-based internal state.
"""
from collections import Counter
from .base import Agent, manhattan
from ..core import neighbors

class ModelReflexAgent(Agent):
    def init(self, agentPosition, foodPositions, gridWorld):
        self.grid = [list(row) for row in gridWorld]
        self.visits = Counter()
        self.stats = {}

    def evaluate(self, pos, foods):
        return min(manhattan(pos,f) for f in foods)

    def nextAction(self, agentPosition, foodPositions):
        if not foodPositions:
            return 'S'
        self.visits[tuple(agentPosition)] += 1
        options = list(neighbors(self.grid, tuple(agentPosition)))
        return min(options, key=lambda ap: self.evaluate(ap[1], foodPositions))[0] if options else 'S'

class LegalMoveReflexAgent(ModelReflexAgent):
    """Exclude wall actions, then greedily reduce Manhattan distance. Can cycle."""

class WallPenaltyReflexAgent(ModelReflexAgent):
    """Add walls crossed by a sampled straight line; this is NOT maze distance."""
    def walls_between(self, a, b):
        count = max(abs(a[0]-b[0]),abs(a[1]-b[1]))
        if not count:
            return 0
        cells = {(round(a[0]+(b[0]-a[0])*i/count),round(a[1]+(b[1]-a[1])*i/count)) for i in range(1,count+1)}
        return sum(not self.grid[r][c] for r,c in cells)

    def evaluate(self, pos, foods):
        return min(manhattan(pos,f)+3*self.walls_between(pos,f) for f in foods)

class MemoryReflexAgent(WallPenaltyReflexAgent):
    """Discourage revisits to escape some greedy loops; success is not guaranteed."""
    def evaluate(self, pos, foods):
        return super().evaluate(pos,foods) + 4*self.visits[pos]
