# From particles to agents

## Baseline

Run `python particles.py`. Each particle has identity, position and velocity, but it has no explicit sensor or policy. The engine resolves collisions. Physical reactions alone do not establish intelligent behaviour.

## Add the perception–action loop

Run `python agents.py --paused`. Select a particle and enable its sensing-range overlay. Explain the roles:

| PEAS component | Implementation |
|---|---|
| Performance | Steps until first particle collision, capped at the experiment limit; optional total collision count |
| Environment | Bounded 2D space, other moving particles and physical interaction rules |
| Actuator | Rotate velocity left/right by the configured angle, or continue straight |
| Sensor | Own state and positions/velocities of neighbours inside R |

Boundary geometry and physics rules are built-in knowledge. The policy chooses an action using observations and a motion model. It is hand-written reasoning, not learned behaviour.

All agents sense the same pre-action world. Their decisions apply together. The physical engine then advances motion. A turn preserves speed, while an actual elastic collision may change a particle's speed.

## Suggested demonstrations

1. **Passive equivalence:** run the same seed in the passive program and in the agent program with sensing disabled. Use equal step limits and experiment mode. They should match.
2. **One-step warning:** use 5° steering and horizon 1. A particle may detect danger correctly yet lack enough time to avoid it. Sensing is not sufficient by itself.
3. **Look further ahead:** compare predictive policies at horizons 1 and 20. Only the predictive variants use this setting.
4. **Random versus robust:** random policies turn without comparing consequences. Robust policies assess left/straight/right against neighbours' immediate possible actions.
5. **Sensor range:** shorten R. A long prediction horizon cannot reveal particles the sensor has not detected.
6. **Wall awareness:** observe predicted paths reflecting at boundaries. An intersection outside the enclosure is not used as a collision location.
7. **Survival game:** stop at first collision, inspect the highlighted pair and the most recent decisions. A collision may still occur because of limited turning, missing neighbours or forecast assumptions.
8. **Controlled measurement:** use `evaluate.py` for 100 matched seeds. Compare capped mean survival, spread and the number of runs reaching the limit.

## What “robust” means here

For A's three candidate actions, evaluate B's three immediate responses. Repeat for each observed neighbour that can be reached within the horizon. Choose the best worst-case pairwise outcome. “Worst case” expresses caution, not hostility.

A candidate turn is applied once in the forecast, followed by coasting and wall bounces. Forecasts do not enumerate every subsequent turn. Increasing the horizon therefore extends projections rather than constructing a 9^H action tree. Agents observe and replan at the next real step.

This remains an approximation: neighbours may steer again, collide with each other, or receive observations A does not have. Robust selection does not guarantee zero collisions.

## Reading the score

Higher capped survival is better for the survival game. A score at the time limit without collision is incomplete lifetime information: the actual failure time is unknown. The percentage reaching the limit helps interpret this.

Collision count over a fixed duration measures a different objective. Use experiment mode if you care about repeated failures after the first collision. Random seed matching controls initial conditions, not the later trajectories, which necessarily diverge under different policies.

Playback speed and window size must not change results at equal simulation steps. Equal counts in different shapes are not equal density because the enclosed areas differ.
