"""CLI and reproducible, non-visual batch experiments."""
import argparse
import csv
from dataclasses import asdict
import json
from pathlib import Path
import statistics
from .model import Config,Colony,DT

def main(argv=None):
    p=argparse.ArgumentParser(description='AgentLab | Ant foraging')
    for name,default in asdict(Config()).items():
        if name=='pheromones':continue
        p.add_argument('--'+name.replace('_','-'),type=type(default),default=default)
    p.add_argument('--no-pheromones',action='store_true',help='Disable trail sensing and deposition')
    p.add_argument('--speed',type=float,default=1,help='Playback multiplier, 0.1 to 8')
    p.add_argument('--autostart',action='store_true');p.add_argument('--headless',action='store_true')
    p.add_argument('--steps',type=int,default=6000);p.add_argument('--runs',type=int,default=1)
    p.add_argument('--output',type=Path,help='New CSV path for headless results')
    a=p.parse_args(argv)
    try:
        config=Config(**{k:getattr(a,k) for k in asdict(Config()) if k!='pheromones'},pheromones=not a.no_pheromones)
        if not .1<=a.speed<=8:raise ValueError('speed must be 0.1 to 8')
        if a.runs<1 or a.steps<1:raise ValueError('runs and steps must be positive')
    except ValueError as e:p.error(str(e))
    if a.headless:
        if a.output:
            sidecar=a.output.with_suffix(a.output.suffix+'.config.json')
            if a.output.exists() or sidecar.exists():p.error('Output CSV or config already exists; choose a new output path')
            if not a.output.parent.is_dir():p.error('Output directory does not exist')
        rows=[]
        for run in range(a.runs):
            opts=asdict(config);opts['seed']+=run;world=Colony(Config(**opts))
            for _ in range(a.steps):
                world.step()
                if world.done:break
            rows.append(dict(seed=opts['seed'],steps=world.tick,seconds=world.tick*DT,delivered=world.delivered,remaining=world.remaining,carrying=sum(x.carrying for x in world.ants),completed=world.done,first_delivery_step=world.first_delivery))
        vals=[r['delivered'] for r in rows]
        print(json.dumps({'runs':len(rows),'mean_delivered':statistics.mean(vals),'min':min(vals),'max':max(vals),'sd':statistics.pstdev(vals),'completed':sum(r['completed'] for r in rows)},indent=2))
        if a.output:
            with a.output.open('x',newline='',encoding='utf8') as f:
                writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
            with sidecar.open('x',encoding='utf8') as f:
                json.dump({'config':asdict(config),'step_limit':a.steps,'runs':a.runs,'dt':DT},f,indent=2)
    else:
        from .ui import ForagingApp
        ForagingApp(config,a.speed,a.autostart).mainloop()
    return 0
