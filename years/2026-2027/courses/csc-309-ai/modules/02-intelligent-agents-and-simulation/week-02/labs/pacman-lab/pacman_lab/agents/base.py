"""The two-method classroom contract. cancellation is an optional engine hook."""
from abc import ABC, abstractmethod
from threading import Event

class Agent(ABC):
    def __init__(self):
        self.cancel = Event()
        self.stats = {}

    @abstractmethod
    def init(self, agentPosition, foodPositions, gridWorld):
        pass

    @abstractmethod
    def nextAction(self, agentPosition, foodPositions):
        pass


def manhattan(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])
