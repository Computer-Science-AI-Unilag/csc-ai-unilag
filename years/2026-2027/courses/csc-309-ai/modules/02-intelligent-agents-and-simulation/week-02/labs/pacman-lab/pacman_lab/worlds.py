"""Ten literal maps plus a connected random maze. '#' is only an authoring aid."""
import random
from .core import normalize_grid, neighbors

MAPS = [
('Open room', ['#########','#.......#','#.......#','#.......#','#.......#','#.......#','#########']),
('One detour', ['#########','#...#...#','#...#...#','#...#...#','#.......#','#.......#','#########']),
('Two doors', ['###########','#....#....#','#.........#','#....#....#','###.###.###','#....#....#','#.........#','#....#....#','###########']),
('Greedy trap', ['###########','#.........#','#..#####..#','#..#...#..#','#..#...#..#','#..#......#','#..#####..#','#.........#','###########']),
('Four rooms', ['#############','#.....#.....#','#.....#.....#','#...........#','#.....#.....#','###.#####.###','#.....#.....#','#...........#','#.....#.....#','#############']),
('Long corridor', ['#############','#...........#','###########.#','#...........#','#.###########','#...........#','#############']),
('Branches', ['#############','#...........#','###.###.###.#','#...#...#...#','#.###.###.###','#...........#','#############']),
('Pillars', ['#############','#...........#','#.#.#.#.#.#.#','#...........#','#.#.#.#.#.#.#','#...........#','#.#.#.#.#.#.#','#...........#','#############']),
('Nested detours', ['###############','#.............#','#.###########.#','#.#.........#.#','#.#.#######.#.#','#.#.........#.#','#.#########.#.#','#...........#.#','#############.#','#.............#','###############']),
('Large crossroads', ['#################','#.......#.......#','#.#####.#.#####.#','#.#...........#.#','#.#.###.#.###.#.#','#...#...#...#...#','###.#.#####.#.###','#...#.......#...#','#.#####.#.#####.#','#.......#.......#','#################']),
]


def fixed_world(number):
    if type(number) is not int or not 1 <= number <= len(MAPS):
        raise ValueError('World number must be 1 through 10.')
    return normalize_grid([[0 if ch == '#' else 1 for ch in row] for row in MAPS[number-1][1]])


def reachable(grid, start):
    seen = {start}
    stack = [start]
    while stack:
        for _, nxt in neighbors(grid, stack.pop()):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return sorted(seen)


def random_world(width=21, height=15, seed=42):
    if type(width) is not int or type(height) is not int or not 5 <= width <= 101 or not 5 <= height <= 101:
        raise ValueError('Random width and height must be integers from 5 to 101.')
    rng = random.Random(seed)
    grid = [[0]*width for _ in range(height)]
    stack = [(1, 1)]
    grid[1][1] = 1
    while stack:
        r, c = stack[-1]
        options = [(r+dr, c+dc) for dr, dc in ((-2,0),(2,0),(0,-2),(0,2))
                   if 0 < r+dr < height-1 and 0 < c+dc < width-1 and not grid[r+dr][c+dc]]
        if not options:
            stack.pop()
            continue
        nr, nc = rng.choice(options)
        grid[(r+nr)//2][(c+nc)//2] = grid[nr][nc] = 1
        stack.append((nr, nc))
    # A few extra doors create loops while preserving connectivity.
    for r in range(1, height-1):
        for c in range(1, width-1):
            if not grid[r][c] and rng.random() < .08:
                if (grid[r-1][c] and grid[r+1][c]) or (grid[r][c-1] and grid[r][c+1]):
                    grid[r][c] = 1
    return grid


def random_positions(grid, food_count=4, seed=42, start=None):
    if type(food_count) is not int or food_count < 0:
        raise ValueError('Food count must be a nonnegative integer.')
    rng = random.Random(seed)
    floors = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v]
    if not floors:
        raise ValueError('World has no floor cells.')
    start = tuple(start) if start is not None else rng.choice(floors)
    if start not in floors:
        raise ValueError('Random placement needs a start on a free cell.')
    choices = [p for p in reachable(grid, start) if p != start]
    if food_count > len(choices):
        raise ValueError(f'Only {len(choices)} reachable food cells are available.')
    return start, rng.sample(choices, food_count)


# Six reproducible lessons. All food is reachable from the specified start.
SPECIALS = {
 1: ('First steps', 1, (1,1), [(1,6)]),
 2: ('Distance can mislead', 2, (1,3), [(1,5)]),
 3: ('Collect all, not just nearest', 1, (3,4), [(1,1),(1,7),(5,1),(5,7)]),
 4: ('A U-shaped trap', 4, (3,4), [(3,2),(1,8)]),
 5: ('Doorways and route order', 5, (1,1), [(1,10),(7,2),(8,10)]),
 6: ('Short horizon versus long detour', 6, (1,1), [(3,1),(5,11)]),
}
