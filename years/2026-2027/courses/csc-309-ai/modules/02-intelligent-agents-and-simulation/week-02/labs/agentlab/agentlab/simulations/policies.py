"""Snapshot-based local sensing and independent, simultaneous steering choices."""
from dataclasses import dataclass
import math
import random
from agentlab.simulations.motion import trace, rotate, encounter

POLICIES = ('passive','reactive_random','reactive_robust','predictive_random','predictive_robust')
LABELS = {
    'passive':'Passive particles',
    'reactive_random':'One-step / random',
    'reactive_robust':'One-step / robust',
    'predictive_random':'Predictive / random',
    'predictive_robust':'Predictive / robust',
}


@dataclass(frozen=True)
class AgentSettings:
    policy: str = 'predictive_robust'
    sensing: bool = True
    sensing_radius: float = .15
    steering_angle: float = 5.0
    horizon: int = 1
    max_steps: int = 1000
    mode: str = 'survival'

    def __post_init__(self):
        if self.policy not in POLICIES:raise ValueError('Unknown policy.')
        if not .0<=self.sensing_radius<=2:raise ValueError('Sensing radius must be 0 to 2 world units.')
        if not 0<=self.steering_angle<=90:raise ValueError('Steering angle must be 0 to 90 degrees.')
        if not isinstance(self.horizon,int) or not 1<=self.horizon<=240:raise ValueError('Horizon must be 1 to 240 steps.')
        if not isinstance(self.max_steps,int) or not 1<=self.max_steps<=1000000:raise ValueError('Maximum steps must be 1 to 1,000,000.')
        if self.mode not in ('survival','experiment'):raise ValueError('Mode must be survival or experiment.')


def decide(sim, settings: AgentSettings, dt: float):
    """Return turns and inspection data without mutating the world.

    Nine immediate action combinations per pair. Then coast (reflecting at walls).
    Recompute next actual tick. Neighbour-neighbour interactions are not forecast.
    """
    balls=sim.balls
    turns={b.id:0 for b in balls}
    details={b.id:{'neighbours':[], 'threats':[], 'action':0, 'reason':'Sensing disabled'} for b in balls}
    if not settings.sensing or settings.policy=='passive':return turns,details
    horizon=1 if settings.policy.startswith('reactive') else settings.horizon
    duration=horizon*dt
    cache={}
    risks={}
    def path(b,action):
        key=(b.id,action)
        if key not in cache:
            cache[key]=trace(sim.boundary,b.position,rotate(b.velocity,action*settings.steering_angle),b.radius,duration)[0]
        return cache[key]
    def risk(a,act,b,other):
        key=(a.id,act,b.id,other)
        if key not in risks:
            result=encounter(path(a,act),path(b,other),a.radius+b.radius,duration)
            risks[key]=result
            risks[(b.id,other,a.id,act)]=result
        return risks[key]
    for a in balls:
        neighbours=[b for b in balls if b.id!=a.id and (b.position-a.position).length()<=settings.sensing_radius]
        # No speed-preserving turns can close a gap faster than the sum of speeds.
        candidates=[b for b in neighbours if (b.position-a.position).length()-a.radius-b.radius <=
                    (a.velocity.length()+b.velocity.length())*duration+1e-10]
        threats=[b for b in candidates if risk(a,0,b,0)[0]<=duration]
        detail={'neighbours':[b.id for b in neighbours], 'threats':[b.id for b in threats],
                'action':0,'reason':'No collision predicted'}
        details[a.id]=detail
        if not threats:continue
        rng=random.Random(f'{sim.config.seed}:{sim.ticks}:{a.id}:steer')
        if settings.policy.endswith('random'):
            action=rng.choice((-1,1))
            detail['reason']='Threat: random turn'
        else:
            # A maximizes its worst outcome across all reachable neighbours/responses.
            scores={}
            for act in (-1,0,1):
                worst=(1,duration,math.inf)
                for b in candidates:
                    for other in (-1,0,1):
                        first,clearance=risk(a,act,b,other)
                        score=(int(first>duration), min(first,duration),clearance)
                        worst=min(worst,score)
                scores[act]=worst
            best=max(scores.values())
            tied=[act for act,s in scores.items() if s[0]==best[0] and abs(s[1]-best[1])<1e-10
                  and (s[2]==best[2] or abs(s[2]-best[2])<1e-10)]
            action=0 if 0 in tied else rng.choice(tied)
            detail['reason']='Threat: safest worst case'
            detail['scores']={str(k):list(v) for k,v in scores.items()}
        turns[a.id]=action
        detail['action']=action
    return turns,details
