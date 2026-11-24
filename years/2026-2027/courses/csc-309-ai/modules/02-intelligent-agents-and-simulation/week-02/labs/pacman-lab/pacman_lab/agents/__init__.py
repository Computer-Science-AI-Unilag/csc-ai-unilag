from .base import Agent
from .reflex import SimpleReflexAgent, ManhattanReflexAgent, EuclideanReflexAgent, AxisFirstReflexAgent
from .model_reflex import ModelReflexAgent, LegalMoveReflexAgent, WallPenaltyReflexAgent, MemoryReflexAgent
from .planning import PlanningAgent, BFSPlanningAgent, UCSPlanningAgent, NearestAStarPlanningAgent, MSTPlanningAgent
from .replanning import ReplanningAgent, DepthReplanningAgent, BeamReplanningAgent, MemoryReplanningAgent

AGENTS = {
    'manhattan': ManhattanReflexAgent, 'euclidean': EuclideanReflexAgent, 'axis': AxisFirstReflexAgent,
    'legal': LegalMoveReflexAgent, 'walls': WallPenaltyReflexAgent, 'memory': MemoryReflexAgent,
    'bfs': BFSPlanningAgent, 'ucs': UCSPlanningAgent, 'astar-nearest': NearestAStarPlanningAgent,
    'astar-mst': MSTPlanningAgent, 'replan-depth': DepthReplanningAgent,
    'replan-beam': BeamReplanningAgent, 'replan-memory': MemoryReplanningAgent,
}
