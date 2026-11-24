"""Compare agents on one identical world; write CSV to a new filename."""
import argparse
import csv
from pacman_lab import Pacman
from pacman_lab.agents import AGENTS

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--special',type=int,default=2,choices=range(1,7))
    p.add_argument('--agents',nargs='+',choices=list(AGENTS),default=['manhattan','legal','memory','bfs','astar-mst','replan-beam'])
    p.add_argument('--output',default=None); args=p.parse_args(); rows=[]
    for name in args.agents:
        agent=AGENTS[name]()
        try:
            game=Pacman.special(args.special).run(agent)
            row=dict(agent=name,status=game.status,score=game.score,steps=game.tick,food_left=len(game.foods),expanded=agent.stats.get('total_expanded',agent.stats.get('expanded',0)))
        except Exception as error: row=dict(agent=name,status=str(error),score='',steps='',food_left='',expanded='')
        rows.append(row)
    print('\nAGENT                STATUS           SCORE  STEPS  LEFT  EXPANDED')
    for r in rows:
        print(f'{r["agent"]:20} {r["status"][:16]:16} {str(r["score"]):>5} {str(r["steps"]):>6} {str(r["food_left"]):>5} {str(r["expanded"]):>9}')
    if args.output:
        with open(args.output,'x',newline='',encoding='utf8') as f:
            writer=csv.DictWriter(f,fieldnames=rows[0]); writer.writeheader(); writer.writerows(rows)
if __name__=='__main__': main()
