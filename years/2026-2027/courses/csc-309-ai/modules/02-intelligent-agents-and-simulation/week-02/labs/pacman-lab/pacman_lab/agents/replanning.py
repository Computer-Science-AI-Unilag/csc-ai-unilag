"""Plan a short batch; execute it; plan again when the queue is empty.
Limited-horizon heuristics and beam pruning do not guarantee global optimality.
"""
from collections import deque, Counter
from .base import Agent
from .search import horizon_plan

class ReplanningAgent(Agent):
    heuristic = 'mst'
    default_beam = 80
    use_memory = False

    def __init__(self, depth=10, beam_width=None, max_expansions=50000, time_limit=5):
        super().__init__()
        if type(depth) is not int or not 1 <= depth <= 50:
            raise ValueError('Replanning depth must be 1 through 50.')
        self.depth = depth
        self.beam_width = self.default_beam if beam_width is None else beam_width
        if self.beam_width is not None and (type(self.beam_width) is not int or self.beam_width < 1):
            raise ValueError('Beam width must be positive.')
        self.max_expansions, self.time_limit = max_expansions,time_limit

    def init(self, agentPosition, foodPositions, gridWorld):
        self.grid = [list(row) for row in gridWorld]
        self.visits = Counter()
        self.batches = 0
        self.total_expanded = 0
        self.plan(agentPosition,foodPositions)

    def plan(self, agentPosition, foodPositions):
        actions,self.stats = horizon_plan(self.grid,agentPosition,foodPositions,self.depth,self.heuristic,
                    self.beam_width,self.max_expansions,self.time_limit,self.cancel,
                    self.visits if self.use_memory else None)
        self.actions = deque(actions)
        self.batches += 1
        self.total_expanded += self.stats['expanded']
        self.stats.update(batches=self.batches,total_expanded=self.total_expanded)

    def nextAction(self, agentPosition, foodPositions):
        self.visits[tuple(agentPosition)] += 1
        if not self.actions:
            self.plan(agentPosition,foodPositions)
        return self.actions.popleft()

class DepthReplanningAgent(ReplanningAgent):
    """Expand all non-cyclic state paths up to depth, subject to time/node budgets."""
    default_beam = None
    heuristic = 'nearest'

class BeamReplanningAgent(ReplanningAgent):
    """Keep a limited beam at each depth; rank by food count then MST estimate."""

class MemoryReplanningAgent(ReplanningAgent):
    """Add a visit penalty to the horizon evaluation, reducing repeated detours."""
    use_memory = True
