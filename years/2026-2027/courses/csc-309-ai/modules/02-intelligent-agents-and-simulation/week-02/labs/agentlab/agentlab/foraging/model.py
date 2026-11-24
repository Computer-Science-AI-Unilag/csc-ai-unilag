"""Local pheromone sensing with explicit, idealised nest-direction knowledge.

One tick: read the old field, decide/move, transact food, diffuse/evaporate,
then add deposits. Ants never read another ant's private state or food location.
"""
from dataclasses import dataclass
import math
import random

DT = 1 / 30
WIDTH, HEIGHT = 1.5, 1.0
COLS, ROWS = 90, 60
NEST = (WIDTH / 2, HEIGHT / 2)
NEST_RADIUS = .035
FOOD_RADIUS = .025

@dataclass(frozen=True)
class Config:
    ants: int = 100
    foods: int = 4
    food_units: int = 100
    seed: int = 42
    ant_speed: float = .12
    sensor_distance: float = .045
    sensor_angle: float = 40.0
    turn_angle: float = 18.0
    exploration: float = .12
    deposit: float = 5.0
    evaporation: float = .12
    diffusion: float = 1.2
    pheromones: bool = True

    def __post_init__(self):
        for name,lo,hi in [('ants',1,500),('foods',1,12),('food_units',1,2000)]:
            v=getattr(self,name)
            if not isinstance(v,int) or isinstance(v,bool) or not lo<=v<=hi:raise ValueError(f'{name}: use an integer from {lo} to {hi}.')
        for name,lo,hi in [('ant_speed',.02,.4),('sensor_distance',.01,.15),('sensor_angle',5,90),('turn_angle',1,90),('exploration',0,1),('deposit',0,30),('evaporation',0,2),('diffusion',0,5)]:
            v=getattr(self,name)
            if not math.isfinite(v) or not lo<=v<=hi:raise ValueError(f'{name}: use {lo} to {hi}.')

@dataclass
class Food:
    x: float
    y: float
    remaining: int
    initial: int

@dataclass
class Ant:
    x: float
    y: float
    heading: float
    carrying: bool = False
    return_time: float = 0
    decision: str = 'Exploring'
    delivered: int = 0

class Colony:
    def __init__(self,config=Config()):
        self.config=config;self.rng=random.Random(config.seed)
        self.tick=0;self.delivered=0;self.first_delivery=None;self.discovered=set()
        self.field=[0.]*(COLS*ROWS);self.food=[];self.history=[(0,0)]
        for _ in range(config.foods):
            for attempt in range(10000):
                x=self.rng.uniform(.10,WIDTH-.10);y=self.rng.uniform(.10,HEIGHT-.10)
                if math.dist((x,y),NEST)>.18 and all(math.hypot(x-f.x,y-f.y)>.12 for f in self.food):break
            else:raise ValueError('Unable to place food. Try another seed or fewer food sources.')
            self.food.append(Food(x,y,config.food_units,config.food_units))
        self.ants=[Ant(*NEST,self.rng.uniform(-math.pi,math.pi)) for _ in range(config.ants)]

    @property
    def done(self):return self.delivered==self.config.foods*self.config.food_units
    @property
    def remaining(self):return sum(f.remaining for f in self.food)

    def index(self,x,y):
        return min(ROWS-1,max(0,int(y/HEIGHT*ROWS)))*COLS+min(COLS-1,max(0,int(x/WIDTH*COLS)))

    def samples(self,a):
        d=self.config.sensor_distance;offset=math.radians(self.config.sensor_angle)
        return [(a.x+d*math.cos(a.heading+t),a.y+d*math.sin(a.heading+t)) for t in (-offset,0,offset)]

    def update_field(self,deposits):
        c=self.config;old=self.field;new=old.copy();mix=c.diffusion*DT;decay=math.exp(-c.evaporation*DT)
        # Pairwise flux conserves chemical at reflecting boundaries; no wraparound.
        if mix:
            for y in range(ROWS):
                for x in range(COLS):
                    i=y*COLS+x
                    if x+1<COLS:
                        flux=(old[i+1]-old[i])*mix/4;new[i]+=flux;new[i+1]-=flux
                    if y+1<ROWS:
                        flux=(old[i+COLS]-old[i])*mix/4;new[i]+=flux;new[i+COLS]-=flux
        self.field=[max(0.,v*decay) for v in new]
        for i,amount in deposits:self.field[i]=min(1000.,self.field[i]+amount)

    def step(self):
        if self.done:return
        c=self.config;deposits=[]
        order=list(range(len(self.ants)));self.rng.shuffle(order)
        for i in order:
            a=self.ants[i]
            if a.carrying:
                a.heading=math.atan2(NEST[1]-a.y,NEST[0]-a.x)
                a.decision='Returning food; depositing trail';a.return_time+=DT
                if c.pheromones and math.dist((a.x,a.y),NEST)>NEST_RADIUS*1.5:
                    deposits.append((self.index(a.x,a.y),c.deposit*DT*math.exp(-a.return_time/5)))
            else:
                close=[(j,f) for j,f in enumerate(self.food) if f.remaining and math.hypot(a.x-f.x,a.y-f.y)<.055]
                if close:
                    j,f=min(close,key=lambda p:math.hypot(a.x-p[1].x,a.y-p[1].y))
                    a.heading=math.atan2(f.y-a.y,f.x-a.x);a.decision='Food detected locally'
                else:
                    values=[self.field[self.index(x,y)] if 0<=x<=WIDTH and 0<=y<=HEIGHT else 0 for x,y in self.samples(a)]
                    if c.pheromones and max(values)>.015 and self.rng.random()>=c.exploration:
                        best=max(values);choices=[j for j,v in enumerate(values) if abs(v-best)<1e-10]
                        choice=self.rng.choice(choices);a.heading+=(choice-1)*math.radians(c.turn_angle)
                        a.decision='Following strongest local pheromone'
                    else:
                        a.heading+=self.rng.uniform(-1,1)*math.radians(c.turn_angle);a.decision='Exploring'
            a.x+=math.cos(a.heading)*c.ant_speed*DT;a.y+=math.sin(a.heading)*c.ant_speed*DT
            if a.x<0 or a.x>WIDTH:a.x=max(0,min(WIDTH,a.x));a.heading=math.pi-a.heading
            if a.y<0 or a.y>HEIGHT:a.y=max(0,min(HEIGHT,a.y));a.heading=-a.heading
            if a.carrying:
                if math.dist((a.x,a.y),NEST)<=NEST_RADIUS:
                    a.carrying=False;a.delivered+=1;self.delivered+=1;a.heading+=math.pi;a.decision='Delivered; exploring again'
                    if self.first_delivery is None:self.first_delivery=self.tick+1
            else:
                for j,f in enumerate(self.food):
                    if f.remaining and math.hypot(a.x-f.x,a.y-f.y)<=FOOD_RADIUS:
                        f.remaining-=1;a.carrying=True;a.return_time=0;a.heading+=math.pi;self.discovered.add(j);a.decision='Picked up food';break
        self.update_field(deposits);self.tick+=1
        if self.tick%30==0:self.history.append((self.tick,self.delivered))
