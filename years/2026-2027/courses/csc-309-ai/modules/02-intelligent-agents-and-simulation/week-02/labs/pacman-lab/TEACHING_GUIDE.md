# Teaching with the Pacman world

## 1. Representation before intelligence

Open explore.py and play manually. Show that the world is an array, the agent
position is a coordinate and food is a collection of coordinates. A move changes
the state; rendering simply displays it. The environment enforces movement and
food rules regardless of which controller supplied the action.

The decision-relevant search state is (position, remaining food). Two visits to
the same cell are different states if different food remains. The static map
does not need to be copied into every search node. The complete game state also
includes score and terminal status. The goal test is an empty food set; the game
also terminates unsuccessfully when score runs out.

## 2. Reflex decisions

A reflex controller chooses the next action from its present information using
a rule or evaluation function. Having a goal does not imply planning. Computing
the score of each immediate candidate move does not create a multi-step plan.

For a cell p=(r,c) and food f=(rf,cf):

- Manhattan distance: d1(p,f) = |r-rf| + |c-cf|.
- Euclidean distance: d2(p,f) = sqrt((r-rf)^2 + (c-cf)^2).

The first two reflex agents choose the hypothetical next cell with minimum
distance to its nearest food. They intentionally ignore wall information.
AxisFirstReflexAgent instead chooses the nearest food and resolves its row
difference after its column difference. Fixed tie-breaking makes demonstrations
repeatable. These controllers can repeatedly hit a wall even though a path exists.

## 3. More information, still local decisions

LegalMoveReflexAgent uses the map to discard wall moves. WallPenaltyReflexAgent
scores the nearest food using Manhattan distance plus three times the number of
walls sampled on the straight line to that food. A straight-line wall count is
not shortest-path distance: it can misjudge doors, long detours and U-shaped traps.
MemoryReflexAgent adds four times the visit count of the candidate cell.

These are progressively better-informed local rules, not guaranteed solutions.
Legal moves can still oscillate. A visit penalty can encourage exploration but
does not prove completeness or optimality.

Terminology matters: a supplied map is a world model. A textbook model-based
reflex agent usually maintains internal state using percept history and a model
of how the world changes. Here every agent receives the current position and
all remaining food, so hidden-state inference is unnecessary. The memory variant
does maintain history. The file name model_reflex groups map-aware reactive
strategies; map access alone is not a separate intelligence guarantee.

## 4. Complete planning

The full planner searches before moving. It simulates legal successors, removes
food in simulated states and searches until it finds an empty food set. Its
stored plan is a sequence of actions; nextAction returns one action from it.

Conceptual algorithm:

```text
frontier <- start state
best_cost[start] <- 0
while frontier is not empty:
    remove the next state according to the search strategy
    if remaining food is empty: reconstruct the action sequence
    for each legal movement action:
        compute successor position and remaining food
        if this path improves the successor's recorded cost:
            record its parent and action
            add successor to frontier
report failure if the frontier becomes empty
```

This is graph search, not an unpruned enumeration of all action sequences.
Repeated states are pruned. With V reachable cells and F initial foods, there
are at most V*2^F position/food combinations. Many combinations are unreachable,
but the bound explains why adding food makes exact search expensive.

BFS uses a FIFO queue and finds a shortest plan when all movement costs are
equal. UCS prioritizes accumulated cost g; with this project's unit costs it
has the same optimal route length as BFS. A* prioritizes f(s)=g(s)+h(s).

## 5. Cost, heuristic and utility are different

- Step cost c(s,a,s') is the actual cost of a transition, here one move.
- g(s) is the accumulated cost from the start to s.
- h(s) estimates the cost still needed to reach the goal.
- Utility measures preference for outcomes; the game's score is one such measure.

A heuristic is not a reward and does not have to equal actual remaining cost.
For A*, an admissible heuristic never overestimates the cheapest remaining cost.
The nearest-food Manhattan estimate is admissible but ignores most remaining
food. A stronger estimate used here is:

    h(p,F) = min distance_Manhattan(p,f) + MST_Manhattan(F)

The minimum is over food f in F. MST is the minimum spanning tree connecting
the foods with Manhattan edge weights; the empty-food estimate is zero. Any
collect-all route must first reach some food and then connect all food locations.
Ignoring walls cannot make those distances too large. The estimate is therefore
a lower bound. A* can find the same shortest plan while expanding fewer states.

For a completed game with F foods and T ticks, score = start + reward*F - cost*T.
Thus, among successful runs with the same foods, fewer ticks means a better score.
However, a route must also stay above zero after each tick. The supplied planners
optimize geometric collect-all length, not score feasibility at every prefix.
A shortest route can lose before reaching its first food if starting points are
too low. Increase starting score for search demonstrations. A planner that must
respect this constraint needs score/budget information in its planning model;
the requested two-method agent interface does not supply scoring settings.

## 6. Replanning in batches

DepthReplanningAgent searches paths up to depth H, then commits to a chosen
partial plan. Each nextAction consumes its next move. When that list is empty,
the controller calls plan again using the current state.

Partial plans are ranked first by fewer foods remaining, then lower estimated
remaining distance, then shorter path length. MemoryReplanningAgent adds twice
the endpoint's prior visit count to the distance term. Candidates include all
positive depths up to H, so a batch may contain fewer than H actions. A goal,
dead end or search budget can also produce a shorter batch. If no move exists,
the agent returns S.

Depth search excludes repeated identical states within a candidate path, but
can revisit a position after collecting food. Beam search retains only the best
B candidates at each depth. It lowers memory and computation requirements but
can discard the branch leading to the best solution. The visit penalty helps
with repetitive behaviour, without guaranteeing escape from every trap.

Replanning does not necessarily mean moving only one step before planning
again. This implementation executes a batch as requested. In a changing world,
one might instead replan after every move or invalidate a plan after new events.
Here walls and food are static except for the agent collecting food, so a valid
full plan normally remains valid.

## 7. Six demonstrations

| Lesson | Setup | Main comparison |
|---|---|---|
| 1 | Open room, one food | Coordinates, actions, greedy movement; 5-move optimum |
| 2 | A detour, one food | Distance decreases versus an actual route; 8-move optimum |
| 3 | Open room, four foods | Food order is part of planning; 19-move optimum |
| 4 | U-shaped trap, two foods | Local rules versus search; 18-move optimum |
| 5 | Four rooms, three foods | Doors and partial planning; 27-move optimum |
| 6 | Long corridor, two foods | Geometric closeness versus route distance; 34-move optimum |

For lesson 4 with default settings, tested results were: Manhattan reflex lost
after 50 ticks; MemoryReflexAgent collected all food in 22 moves; BFS and MST-A*
both used 18 moves. BFS expanded 66 states, MST-A* expanded 24. These are results
for this fixed configuration and tie-breaking, not a universal ranking.

Suggested sequence: play manually; inspect arrays; implement always-right;
implement distance-based action scores; reject illegal moves; add wall/history
penalties; run BFS; compare A*; then vary replanning depth and beam width.

## 8. Reading search output

`expanded` counts states whose successors were examined, not complete paths.
`generated` counts successor attempts before duplicate pruning. `frontier_peak`
is the largest recorded pending collection (for replanning, a candidate layer).
`plan_length` counts planned actions. `seconds` measures computation time.
Replanning also records cumulative expansions across its planning calls.

Compare route length, score and computational work separately. A faster search
need not produce a shorter route. A lower heuristic value does not prove that
a state is better. A full planner that reaches its search limit reports failure
instead of pretending its partial result is a complete plan; a bounded replanner
may use its best partial plan and reports the budget cutoff.

Useful questions: Why is a position alone not a sufficient search state? Why can
the best first move increase distance to food? What makes a heuristic admissible?
Why can two agents have identical scores but different computational costs?
What changes when only nearby food is observable or ghosts can move?
