"""One bounded experiment, shared by desktop and non-visual evaluation."""
from agentlab.simulations.balls import BallConfig, BallSimulation
from agentlab.simulations.policies import AgentSettings, decide
from agentlab.simulations.motion import rotate

DT=1/240


class Session:
    def __init__(self,config=BallConfig(),settings=AgentSettings()):
        self.config=config
        self.settings=settings
        self.reset()

    def reset(self):
        self.world=BallSimulation(self.config)
        self.done=False
        self.reason='Ready'
        self.inspection={}
        self.turn_count=0

    def step(self,dt=DT):
        if self.done:return
        if abs(dt-DT)>1e-12:raise ValueError('Sessions use a fixed 1/240-second step.')
        turns,self.inspection=decide(self.world,self.settings,dt)
        for b in self.world.balls:
            action=turns[b.id]
            if action:
                b.velocity=rotate(b.velocity,action*self.settings.steering_angle)
                self.turn_count+=1
        self.world.step(dt)
        if self.settings.mode=='survival' and self.world.first_collision_step is not None:
            self.done=True
            self.reason='First collision'
        elif self.world.ticks>=self.settings.max_steps:
            self.done=True
            self.reason='Step limit reached'

    def result(self):
        first=self.world.first_collision_step
        score=first if first is not None else self.world.ticks
        return dict(seed=self.config.seed,policy=self.settings.policy,sensing=self.settings.sensing,
                    steps=self.world.ticks,survival_steps=score,survival_seconds=score*DT,
                    first_collision_step=first,censored=first is None,
                    collisions=self.world.pair_collisions,wall_collisions=self.world.wall_collisions,
                    steering_actions=self.turn_count)
