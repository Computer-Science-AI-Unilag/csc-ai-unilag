"""Edit this file in class, then run: python explore.py"""
from pacman_lab import Pacman
from pacman_lab.agents import *

if __name__ == '__main__':
    pacman = Pacman.special(2, start_score=50, step_cost=1, food_reward=50, tick_ms=250)
    # Alternative: explicit arrays (row, column), 0=wall, 1=floor:
    # pacman = Pacman([[0,0,0,0,0],[0,1,1,1,0],[0,1,0,1,0],
    #                  [0,1,1,1,0],[0,0,0,0,0]], [[1,3],[3,3]], (1,1))
    # Alternative: random connected maze:
    # pacman = Pacman(width=21, height=15, food_count=4, seed=42)
    pacman.play()
    # Replace the line above with one of these:
    # pacman.play(ManhattanReflexAgent())
    # pacman.play(MSTPlanningAgent())
    # pacman.play(BeamReplanningAgent(depth=10))
