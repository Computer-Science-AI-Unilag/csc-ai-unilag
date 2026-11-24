"""Complete collect-all plans created in init. Default: optimal A* with MST bound.
The optimum is minimum moves in a static maze, ignoring score-prefix constraints.
"""
from collections import deque
from .base import Agent
from .search import full_plan

class PlanningAgent(Agent):
    method, heuristic = 'astar', 'mst'

    def __init__(self, max_expansions=200000, time_limit=15):
        super().__init__()
        self.max_expansions = max_expansions
        self.time_limit = time_limit

    def init(self, agentPosition, foodPositions, gridWorld):
        actions,self.stats = full_plan(gridWorld,agentPosition,foodPositions,self.method,self.heuristic,
                                     self.max_expansions,self.time_limit,self.cancel)
        self.plan = deque(actions)

    def nextAction(self, agentPosition, foodPositions):
        return self.plan.popleft() if self.plan else 'S'

class BFSPlanningAgent(PlanningAgent):
    """Breadth first search; optimal for unit-cost moves, often expands many states."""
    method, heuristic = 'bfs', 'zero'

class UCSPlanningAgent(PlanningAgent):
    """Uniform-cost search; equivalent optimal cost to BFS with these unit costs."""
    method, heuristic = 'ucs', 'zero'

class NearestAStarPlanningAgent(PlanningAgent):
    """A* using distance to nearest food: admissible but weak for collect-all."""
    heuristic = 'nearest'

class MSTPlanningAgent(PlanningAgent):
    """A*: nearest-food distance plus Manhattan food MST; admissible lower bound."""
