"""Paired-seed evaluation; never imports the desktop UI."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
from dataclasses import asdict,replace
import json
from pathlib import Path
import statistics
import time
from agentlab.simulations.balls import BallConfig
from agentlab.simulations.policies import AgentSettings,POLICIES
from agentlab.simulations.session import Session


def run_trial(task):
    config,settings=task
    session=Session(config,settings)
    while not session.done:session.step()
    return session.result()


def summarize(rows):
    scores=[r['survival_steps'] for r in rows]
    return dict(runs=len(rows),mean=statistics.mean(scores),minimum=min(scores),maximum=max(scores),
                stddev=statistics.pstdev(scores),median=statistics.median(scores),
                survived_to_limit=sum(r['censored'] for r in rows),
                mean_collisions=statistics.mean(r['collisions'] for r in rows),
                min_collisions=min(r['collisions'] for r in rows),
                max_collisions=max(r['collisions'] for r in rows),
                stddev_collisions=statistics.pstdev(r['collisions'] for r in rows))


def main(argv=None):
    p=argparse.ArgumentParser(description='Compare policies on identical initial seeds; no animation.')
    p.add_argument('--runs',type=int,default=100)
    p.add_argument('--seed',type=int,default=42,help='First seed; trials use seed, seed+1, ...')
    p.add_argument('--steps',type=int,default=1000)
    p.add_argument('--shape',choices=['square','rectangle','circle','triangle'],default='square')
    p.add_argument('--aspect-ratio',type=float,default=1.6,help='Rectangle width / height (0.5 to 3)')
    p.add_argument('--balls',type=int,default=24)
    p.add_argument('--radius',type=float,default=.012)
    p.add_argument('--sensing-radius',type=float,default=.15)
    p.add_argument('--angle',type=float,default=5)
    p.add_argument('--horizon',type=int,default=1)
    p.add_argument('--mode',choices=['survival','experiment'],default='survival')
    p.add_argument('--no-sensing',action='store_true')
    p.add_argument('--policies',nargs='+',choices=POLICIES,default=list(POLICIES))
    p.add_argument('--workers',type=int,default=1,help='Parallel worker processes (default 1)')
    p.add_argument('--output',default='results',help='Output directory, must not already contain report files')
    args=p.parse_args(argv)
    try:
        if not 1<=args.runs<=10000:raise ValueError('Runs must be 1 to 10,000.')
        if not 1<=args.workers<=32:raise ValueError('Workers must be 1 to 32.')
        config=BallConfig(args.shape,args.balls,args.seed,args.radius,args.aspect_ratio)
        settings=AgentSettings(sensing=not args.no_sensing,sensing_radius=args.sensing_radius,
            steering_angle=args.angle,horizon=args.horizon,max_steps=args.steps,mode=args.mode)
    except ValueError as exc:p.error(str(exc))
    folder=Path(args.output)
    if any((folder/n).exists() for n in ('runs.csv','summary.csv','report.json')):
        p.error('Output report already exists. Choose a new --output directory.')
    folder.mkdir(parents=True,exist_ok=True)
    tasks=[(replace(config,seed=args.seed+i),replace(settings,policy=policy))
           for policy in dict.fromkeys(args.policies) for i in range(args.runs)]
    rows=[];start=time.perf_counter()
    executor=ProcessPoolExecutor(args.workers) if args.workers>1 else None
    results=executor.map(run_trial,tasks) if executor else map(run_trial,tasks)
    print(f'{len(tasks)} trials | {args.runs} matched seeds per policy | horizon {args.horizon}',flush=True)
    print('Survival scores are steps, capped at the evaluation limit. Higher is better.',flush=True)
    try:
        with (folder/'runs.csv').open('w',newline='',encoding='utf-8') as file:
            writer=None
            for i,row in enumerate(results,1):
                if writer is None:
                    writer=csv.DictWriter(file,fieldnames=list(row));writer.writeheader()
                writer.writerow(row);file.flush();rows.append(row)
                if i%args.runs==0 or i%10==0:
                    print(f'  Completed {i}/{len(tasks)}  ({time.perf_counter()-start:.1f}s)',flush=True)
    finally:
        if executor:executor.shutdown(cancel_futures=True)
    summaries=[]
    print('\nPolicy                 Mean      Min      Max      SD      Reached limit   Mean collisions')
    for policy in dict.fromkeys(args.policies):
        group=[r for r in rows if r['policy']==policy]
        stat=dict(policy=policy,**summarize(group));summaries.append(stat)
        print(f'{policy:22} {stat["mean"]:8.2f} {stat["minimum"]:8} {stat["maximum"]:8} '
              f'{stat["stddev"]:8.2f}  {stat["survived_to_limit"]:4}/{args.runs:<4}       {stat["mean_collisions"]:8.2f}')
    if args.mode=='experiment':
        print('\nCollision counts (lower is better):')
        for stat in summaries:
            print(f'{stat["policy"]:22} mean={stat["mean_collisions"]:.2f}  min={stat["min_collisions"]}  max={stat["max_collisions"]}  SD={stat["stddev_collisions"]:.2f}')
    with (folder/'summary.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(summaries[0]));writer.writeheader();writer.writerows(summaries)
    report={'configuration':vars(args),'world':asdict(config),'agent':asdict(settings),'dt':1/240,
            'score_definition':'min(first collision step, maximum steps); capped survival, not uncensored lifetime',
            'stddev_definition':'population standard deviation across the requested seed set',
            'elapsed_seconds':time.perf_counter()-start,'summary':summaries}
    (folder/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f'\nSaved per-run data, summary and configuration to {folder.resolve()}')
    return 0
