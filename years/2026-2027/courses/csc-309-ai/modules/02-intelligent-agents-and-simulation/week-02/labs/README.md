# Week 02 Practical Labs

The practical code is organised as two independent Python projects. Both require Python 3.10 or later and Tkinter for their graphical interfaces. They use no third-party Python packages.

## AgentLab: particles, agents, and ant foraging

[AgentLab](agentlab/README.md) models particles and agents in a bounded environment. It supports perception, policies, collision avoidance, controlled evaluation, and ant-foraging exercises.

```powershell
cd agentlab
python run.py --help
python agents.py --paused
python ants.py
```

Use [Ant Foraging: PEAS and Algorithms](../materials/ant-foraging-peas-and-algorithms.pdf) alongside this lab.

## Pacman Lab: reflex decisions, search, and replanning

[Pacman Lab](pacman-lab/README.md) is a grid-world environment for comparing human play, reflex agents, map-aware agents, BFS, uniform-cost search, A*, and bounded replanning.

```powershell
cd pacman-lab
python run.py --help
python explore.py
```

Use [Agent Architectures Pacman Lab](../materials/agent-architectures-pacman-lab.pdf) alongside this lab.

## Safe classroom use

Run the code from its own lab directory. Generated `__pycache__/`, `.ipynb_checkpoints/`, evaluation output, and local experiment data must not be committed.
