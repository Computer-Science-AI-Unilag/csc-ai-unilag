"""Small immutable 2D vectors, independent of the GUI."""
from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class Vec2:
    x: float
    y: float

    def __add__(self, other: 'Vec2') -> 'Vec2':
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Vec2') -> 'Vec2':
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> 'Vec2':
        return Vec2(self.x * scalar, self.y * scalar)

    def dot(self, other: 'Vec2') -> float:
        return self.x * other.x + self.y * other.y

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def unit(self) -> 'Vec2':
        length = self.length()
        return self * (1.0 / length) if length > 1e-12 else Vec2(1, 0)
