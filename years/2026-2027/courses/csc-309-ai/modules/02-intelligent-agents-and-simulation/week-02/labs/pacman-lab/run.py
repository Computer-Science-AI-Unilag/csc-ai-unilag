"""CLI alternative to editing explore.py. python run.py --help"""
import argparse
import json
from pacman_lab import Pacman
from pacman_lab.agents import AGENTS

def main():
    p=argparse.ArgumentParser(description='Pacman Classroom: human play and explainable agents')
    source=p.add_mutually_exclusive_group()
    source.add_argument('--special',type=int,choices=range(1,7))
    source.add_argument('--world',type=int,choices=range(1,11))
    source.add_argument('--random',action='store_true')
    source.add_argument('--config',help='JSON containing grid, foods and agent')
    p.add_argument('--agent',choices=['human']+list(AGENTS),default='human')
    for key,value in [('width',21),('height',15),('foods',4),('seed',42),('tick-ms',250),('depth',10),('beam-width',80),('max-expansions',200000),('max-steps',10000)]:
        p.add_argument('--'+key,type=int,default=value)
    for key in ['start-score','step-cost','food-reward']: p.add_argument('--'+key,type=float)
    p.add_argument('--time-limit',type=float,default=15)
    p.add_argument('--headless',action='store_true'); p.add_argument('--print-config',action='store_true')
    args=p.parse_args()
    try:
        if args.max_expansions<1 or args.time_limit<=0 or args.max_steps<1: raise ValueError('Budgets must be positive.')
        data={}
        if args.config:
            with open(args.config,encoding='utf8') as f: data=json.load(f)
        scoring=data.get('scoring',{})
        options=dict(start_score=args.start_score if args.start_score is not None else scoring.get('start',50),
                     step_cost=args.step_cost if args.step_cost is not None else scoring.get('step_cost',1),
                     food_reward=args.food_reward if args.food_reward is not None else scoring.get('food_reward',50),tick_ms=args.tick_ms)
        if args.config: world=Pacman(data['grid'],data.get('foods',[]),data.get('agent'),**options)
        elif args.random: world=Pacman(width=args.width,height=args.height,food_count=args.foods,seed=args.seed,**options)
        elif args.world: world=Pacman.world(args.world,food_count=args.foods,seed=args.seed,**options)
        else: world=Pacman.special(args.special or 1,**options)
        if args.print_config: print(json.dumps(world.config,indent=2)); return
        agent=None
        if args.agent!='human':
            kwargs={}
            if args.agent in ('bfs','ucs','astar-nearest','astar-mst') or args.agent.startswith('replan'):
                kwargs.update(max_expansions=args.max_expansions,time_limit=args.time_limit)
            if args.agent.startswith('replan'):
                kwargs['depth']=args.depth
                if args.agent!='replan-depth': kwargs['beam_width']=args.beam_width
            agent=AGENTS[args.agent](**kwargs)
        if args.headless:
            if agent is None: raise ValueError('Headless mode requires --agent.')
            game=world.run(agent,args.max_steps)
            print(json.dumps(dict(status=game.status,score=game.score,steps=game.tick,food_left=len(game.foods),stats=getattr(agent,'stats',{})),indent=2))
        else: world.play(agent)
    except (ValueError,KeyError,OSError,RuntimeError) as error: p.exit(2,f'Error: {error}\n')
if __name__=='__main__': main()
