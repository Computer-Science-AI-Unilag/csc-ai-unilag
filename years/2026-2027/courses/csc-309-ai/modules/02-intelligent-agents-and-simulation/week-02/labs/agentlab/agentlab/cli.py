"""Launch either classroom program or a single headless run."""
import argparse
import json
import math
from agentlab.simulations.balls import BallConfig
from agentlab.simulations.policies import AgentSettings,POLICIES
from agentlab.simulations.session import Session


def parser(default_program='agents'):
    p=argparse.ArgumentParser(description='AgentLab: passive particles and sensing/steering agents.')
    p.add_argument('--program',choices=['particles','agents'],default=default_program)
    p.add_argument('--shape',choices=['square','rectangle','circle','triangle'],default='square')
    p.add_argument('--aspect-ratio',type=float,default=1.6,help='Rectangle width / height (0.5 to 3)')
    p.add_argument('--balls',type=int,default=24)
    p.add_argument('--seed',type=int,default=42)
    p.add_argument('--radius',type=float,default=.012)
    p.add_argument('--speed',type=float,default=1)
    p.add_argument('--policy',choices=POLICIES,default='predictive_robust')
    p.add_argument('--no-sensing',action='store_true')
    p.add_argument('--sensing-radius',type=float,default=.15)
    p.add_argument('--angle',type=float,default=5)
    p.add_argument('--horizon',type=int,default=1)
    p.add_argument('--steps',type=int,default=1000,help='Maximum simulation steps')
    p.add_argument('--mode',choices=['survival','experiment'],default='survival' if default_program=='agents' else 'experiment')
    p.add_argument('--paused',action='store_true')
    p.add_argument('--autostart',action='store_true',help='Start the agent experiment immediately (otherwise opens paused)')
    p.add_argument('--no-trails',action='store_true')
    p.add_argument('--headless',action='store_true')
    return p


def main(argv=None,default_program='agents'):
    p=parser(default_program);args=p.parse_args(argv)
    try:
        if not math.isfinite(args.speed) or not .1<=args.speed<=4:raise ValueError('Speed must be 0.1 to 4.')
        config=BallConfig(args.shape,args.balls,args.seed,args.radius,args.aspect_ratio)
        settings=AgentSettings(policy='passive' if args.program=='particles' else args.policy,
            sensing=args.program=='agents' and not args.no_sensing,sensing_radius=args.sensing_radius,
            steering_angle=args.angle,horizon=args.horizon,max_steps=args.steps,mode=args.mode)
        if args.headless:
            session=Session(config,settings)
            while not session.done:session.step()
            print(json.dumps(session.result(),indent=2))
        else:
            try:
                from agentlab.ui.app import Application
                start_running=not args.paused and (args.program=='particles' or args.autostart)
                app=Application(config,args.speed,start_running,not args.no_trails,settings,args.program)
                app.mainloop()
            except ImportError as exc:p.exit(1,f'Install Python with Tcl/Tk support: {exc}\n')
            except Exception as exc:
                import tkinter
                if isinstance(exc,tkinter.TclError):p.exit(1,f'Cannot open desktop UI: {exc}\nTry --headless.\n')
                raise
    except ValueError as exc:p.error(str(exc))
    return 0
