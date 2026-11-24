"""Fixed-step scheduling shared by simulations. Never enlarge dt for speed."""
from dataclasses import dataclass
from typing import Callable


@dataclass
class FixedClock:
    dt: float = 1 / 240
    max_steps: int = 24
    accumulator: float = 0.0
    dropped_seconds: float = 0.0

    def reset(self) -> None:
        self.accumulator = 0.0
        self.dropped_seconds = 0.0

    def advance(self, elapsed: float, speed: float, step: Callable[[float], None]) -> int:
        requested = max(0.0, elapsed) * speed
        capacity = self.dt * self.max_steps
        accepted = min(requested, capacity)
        self.dropped_seconds += requested - accepted
        self.accumulator += accepted
        count = 0
        while self.accumulator + 1e-12 >= self.dt and count < self.max_steps:
            step(self.dt)
            self.accumulator -= self.dt
            count += 1
        return count
