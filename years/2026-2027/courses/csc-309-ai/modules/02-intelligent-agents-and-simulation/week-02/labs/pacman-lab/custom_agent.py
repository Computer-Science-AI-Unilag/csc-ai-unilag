"""The minimal two-method contract. Deliberately keeps trying right."""
from pacman_lab import Pacman
class MyAgent:
    def init(self, agentPosition, foodPositions, gridWorld):
        self.grid = gridWorld
    def nextAction(self, agentPosition, foodPositions):
        return 'R'
if __name__ == '__main__':
    Pacman.special(1).play(MyAgent())
