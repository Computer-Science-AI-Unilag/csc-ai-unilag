"""Equal-mass elastic discs. No UI imports; usable from tests and batch runs."""
from collections import deque
from dataclasses import dataclass, field
import math
import random
from agentlab.core.vector import Vec2
from agentlab.simulations.boundaries import Boundary

COLORS = ('#59e1dd', '#9d91ff', '#ffbb6b', '#fa82a3', '#7ddfa1', '#70bbff')


@dataclass(frozen=True)
class BallConfig:
    shape: str = 'square'
    count: int = 24
    seed: int = 42
    radius: float = .012
    aspect_ratio: float = 1.6

    def __post_init__(self):
        Boundary(self.shape, self.aspect_ratio)
        if not 1 <= self.count <= 120:
            raise ValueError('Ball count must be between 1 and 120.')
        if not .005 <= self.radius <= .018:
            raise ValueError('Radius must be between 0.005 and 0.018.')


@dataclass
class Ball:
    id: int
    position: Vec2
    velocity: Vec2
    radius: float
    color: str
    trail: deque = field(default_factory=lambda: deque(maxlen=22))
    last_event: str = 'Free motion'
    event_time: float = -1.0


class BallSimulation:
    """Public interface: config, boundary, balls, reset(config), step(dt), metrics()."""
    name = 'Colliding balls'

    def __init__(self, config: BallConfig = BallConfig()):
        self.reset(config)

    def reset(self, config: BallConfig | None = None) -> None:
        config = config or self.config
        boundary = Boundary(config.shape, config.aspect_ratio)
        rng = random.Random(config.seed)
        balls = []
        for i in range(config.count):
            for _ in range(30000):
                position = Vec2(rng.uniform(.05, .95), rng.uniform(.05, .95))
                if boundary.contains(position, config.radius) and all(
                    (position - b.position).length() >= 2 * config.radius + .002 for b in balls
                ):
                    break
            else:
                raise ValueError('Could not place balls without overlap. Reduce count or radius.')
            angle = rng.uniform(0, math.tau)
            speed = rng.uniform(.12, .21)
            balls.append(Ball(i + 1, position, Vec2(math.cos(angle), math.sin(angle)) * speed,
                              config.radius, COLORS[i % len(COLORS)]))
        # Commit only after successful placement, preserving the old world on errors.
        self.config, self.boundary, self.balls = config, boundary, balls
        self.ticks = 0
        self.time = 0.0
        self.wall_collisions = 0
        self.pair_collisions = 0
        self.initial_energy = self.energy()
        self.first_collision_step = None
        self.first_collision_pairs = []
        self.active_contacts = set()

    def energy(self) -> float:
        return sum(.5 * b.velocity.dot(b.velocity) for b in self.balls)

    def _wall(self, ball: Ball) -> None:
        # Iteration handles vertices where two wall constraints meet.
        for _ in range(8):
            contacts = self.boundary.contacts(ball.position, ball.radius)
            if not contacts:
                break
            for normal, depth in [max(contacts, key=lambda contact: contact[1])]:
                # Project the deepest constraint; recompute the others next iteration.
                if depth <= 1e-12:
                    continue
                ball.position = ball.position + normal * (depth + 1e-11)
                incoming = ball.velocity.dot(normal)
                if incoming < 0:
                    ball.velocity = ball.velocity - normal * (2 * incoming)
                    self.wall_collisions += 1
                    ball.last_event = 'Boundary collision'
                    ball.event_time = self.time

    def _pair(self, a: Ball, b: Ball) -> None:
        delta = b.position - a.position
        distance = delta.length()
        overlap = a.radius + b.radius - distance
        if overlap <= 0:
            return
        normal = delta.unit()
        correction = normal * ((overlap + 1e-11) / 2)
        a.position = a.position - correction
        b.position = b.position + correction
        relative = (b.velocity - a.velocity).dot(normal)
        if relative < 0:
            # Equal mass, restitution=1: exchange normal velocity components.
            a.velocity = a.velocity + normal * relative
            b.velocity = b.velocity - normal * relative
            pair = tuple(sorted((a.id,b.id)))
            if pair not in self.active_contacts:
                self.pair_collisions += 1
                if self.first_collision_step is None:
                    self.first_collision_step = self.ticks + 1
                if self.first_collision_step == self.ticks + 1:
                    self.first_collision_pairs.append(pair)
            self.active_contacts.add(pair)
            a.last_event, b.last_event = f'Contact with ball {b.id:03}', f'Contact with ball {a.id:03}'
            a.event_time = b.event_time = self.time

    def _candidates(self):
        """Spatial hash: inspect only cells that can hold touching discs."""
        cell = 2 * self.config.radius
        grid = {}
        for b in self.balls:
            key = (int(b.position.x // cell), int(b.position.y // cell))
            grid.setdefault(key, []).append(b)
        for key, group in grid.items():
            x, y = key
            for a in group:
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for b in grid.get((x + dx, y + dy), ()):
                            if a.id < b.id:
                                yield a, b

    def step(self, dt: float) -> None:
        if not math.isfinite(dt) or dt <= 0:
            raise ValueError('dt must be finite and positive.')
        # Adaptive subdivisions bound travel to half a radius, even after energy exchange.
        maximum_speed = max(b.velocity.length() for b in self.balls)
        steps = max(1, math.ceil(maximum_speed * dt / (self.config.radius * .5)))
        h = dt / steps
        for _ in range(steps):
            # A new encounter starts only after a real surface gap has opened.
            by_id = {b.id:b for b in self.balls}
            self.active_contacts = {pair for pair in self.active_contacts
                if (by_id[pair[0]].position-by_id[pair[1]].position).length()
                <= by_id[pair[0]].radius+by_id[pair[1]].radius+1e-7}
            for ball in self.balls:
                ball.position = ball.position + ball.velocity * h
                self._wall(ball)
            for _ in range(4):
                for a, b in self._candidates():
                    self._pair(a, b)
                for ball in self.balls:
                    self._wall(ball)
        self.ticks += 1
        self.time += dt
        if self.ticks % 8 == 0:
            for ball in self.balls:
                ball.trail.append(ball.position)

    def metrics(self) -> dict:
        return {'ticks': self.ticks, 'simulation_seconds': round(self.time, 6),
                'balls': len(self.balls), 'wall_collisions': self.wall_collisions,
                'ball_collisions': self.pair_collisions, 'kinetic_energy': self.energy(),
                'relative_energy_drift': (self.energy() - self.initial_energy) / self.initial_energy}
