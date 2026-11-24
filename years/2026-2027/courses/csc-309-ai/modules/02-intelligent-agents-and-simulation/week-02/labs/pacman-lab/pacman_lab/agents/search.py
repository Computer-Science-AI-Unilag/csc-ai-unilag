"""Search state = (position, remaining food). Paths with equal positions can differ.
BFS/UCS/A* are graph searches: repeated states are pruned, not re-expanded blindly.
"""
from collections import deque
from heapq import heappush, heappop
from itertools import count
import time
from .base import manhattan
from ..core import neighbors

class SearchStopped(RuntimeError):
    pass


def mst_food(foods):
    if not foods:
        return 0
    remaining = set(foods)
    first = min(remaining)
    remaining.remove(first)
    best = {p: manhattan(first,p) for p in remaining}
    total = 0
    while remaining:
        nxt = min(remaining, key=lambda p: (best[p],p))
        total += best[nxt]
        remaining.remove(nxt)
        for p in remaining:
            best[p] = min(best[p], manhattan(nxt,p))
    return total


def estimate(state, kind='mst', cache=None):
    pos, foods = state
    if not foods:
        return 0
    nearest = min(manhattan(pos,f) for f in foods)
    if kind == 'nearest':
        return nearest
    if kind == 'zero':
        return 0
    if cache is None:
        return nearest + mst_food(foods)
    if foods not in cache:
        cache[foods] = mst_food(foods)
    return nearest + cache[foods]


def reconstruct(parent, state):
    actions = []
    while parent[state] is not None:
        state, action = parent[state]
        actions.append(action)
    return list(reversed(actions))


def full_plan(grid, position, foods, method='astar', heuristic='mst',
              max_expansions=200000, time_limit=15, cancel=None):
    start_time = time.perf_counter()
    start = (tuple(position), frozenset(map(tuple,foods)))
    costs, parent = {start: 0}, {start: None}
    serial = count()
    cache = {}
    queue = deque([start])
    heap = [(estimate(start,heuristic,cache),next(serial),0,start)]
    expanded = generated = 0
    peak = 1
    def report(status, length=0):
        stats = dict(status=status,expanded=expanded,generated=generated,frontier_peak=peak,
                     seconds=round(time.perf_counter()-start_time,4),plan_length=length)
        print(f'[{method}/{heuristic}] {stats}', flush=True)
        return stats
    while queue if method == 'bfs' else heap:
        if (cancel is not None and cancel.is_set()) or expanded >= max_expansions or time.perf_counter()-start_time >= time_limit:
            report('cancelled/limit')
            raise SearchStopped('Search cancelled or budget reached; no complete plan claimed.')
        if method == 'bfs':
            state = queue.popleft()
            g = costs[state]
        else:
            _,_,g,state = heappop(heap)
            if costs.get(state) != g:
                continue
        if not state[1]:
            actions = reconstruct(parent,state)
            return actions, report('goal',len(actions))
        expanded += 1
        if expanded % 5000 == 0:
            print(f'  expanded={expanded:,}; frontier={len(queue) if method == "bfs" else len(heap):,}',flush=True)
        for action, pos in neighbors(grid,state[0]):
            generated += 1
            nxt = (pos,state[1]-{pos})
            ng = g+1
            if ng >= costs.get(nxt,float('inf')):
                continue
            costs[nxt] = ng
            parent[nxt] = (state,action)
            if method == 'bfs':
                queue.append(nxt)
            else:
                heappush(heap,(ng+estimate(nxt,heuristic,cache),next(serial),ng,nxt))
        peak = max(peak,len(queue) if method == 'bfs' else len(heap))
    report('unreachable')
    raise SearchStopped('No route collects all remaining food.')


def horizon_plan(grid, position, foods, depth=10, heuristic='mst', beam_width=None,
                 max_expansions=50000, time_limit=5, cancel=None, visits=None):
    """Search up to depth; prefer more food, then a smaller remaining estimate.
    Exhaustive here means all non-cyclic state paths up to depth within the budget.
    Beam mode keeps only the best width candidates at each depth (approximate).
    """
    began = time.perf_counter()
    start = (tuple(position),frozenset(map(tuple,foods)))
    layer = [(start,[],frozenset({start}))]
    best = None
    expanded = generated = 0
    peak = 1
    cache = {}
    visits = visits or {}
    def rank(item):
        state, path, _ = item
        return (len(state[1]),estimate(state,heuristic,cache)+2*visits.get(state[0],0),len(path),tuple(path))
    cutoff = False
    for _ in range(depth):
        next_layer = []
        for state,path,seen in layer:
            if cancel is not None and cancel.is_set():
                raise SearchStopped('Planning cancelled.')
            if expanded >= max_expansions or time.perf_counter()-began >= time_limit:
                cutoff = True
                break
            expanded += 1
            for action,pos in neighbors(grid,state[0]):
                generated += 1
                nxt = (pos,state[1]-{pos})
                if nxt in seen:
                    continue
                item = (nxt,path+[action],seen|{nxt})
                if not nxt[1]:
                    stats = dict(status='goal',expanded=expanded,generated=generated,frontier_peak=peak,seconds=round(time.perf_counter()-began,4),plan_length=len(item[1]))
                    print(f'[replan] {stats}',flush=True)
                    return item[1],stats
                next_layer.append(item)
                if best is None or rank(item)<rank(best):
                    best = item
        peak = max(peak,len(next_layer))
        if cutoff or not next_layer:
            break
        next_layer.sort(key=rank)
        layer = next_layer if beam_width is None else next_layer[:beam_width]
    actions = best[1] if best else ['S']
    stats = dict(status='budget' if cutoff else 'horizon',expanded=expanded,generated=generated,
                 frontier_peak=peak,seconds=round(time.perf_counter()-began,4),plan_length=len(actions))
    print(f'[replan] {stats}',flush=True)
    return actions,stats
