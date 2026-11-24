"""Convex boundaries in a unit world. Normals point inward."""
import math
from dataclasses import dataclass
from functools import cached_property
from agentlab.core.vector import Vec2

SHAPES = ('square', 'rectangle', 'circle', 'triangle')


@dataclass(frozen=True)
class Boundary:
    shape: str
    aspect_ratio: float = 1.6

    def __post_init__(self):
        if not .5 <= self.aspect_ratio <= 3:
            raise ValueError("Rectangle aspect ratio must be 0.5 to 3 (width / height).")
        if self.shape not in SHAPES:
            raise ValueError(f'Unknown shape: {self.shape}')

    @cached_property
    def vertices(self) -> tuple[Vec2, ...]:
        if self.shape == 'square':
            return (Vec2(.07, .07), Vec2(.93, .07), Vec2(.93, .93), Vec2(.07, .93))
        if self.shape == 'rectangle':
            width = .86 * min(1., self.aspect_ratio)
            height = .86 * min(1., 1 / self.aspect_ratio)
            x0, x1 = .5-width/2, .5+width/2
            y0, y1 = .5-height/2, .5+height/2
            return (Vec2(x0,y0), Vec2(x1,y0), Vec2(x1,y1), Vec2(x0,y1))
        if self.shape == 'triangle':
            # Three vertices on the same circumcircle, separated by 120 degrees.
            return tuple(Vec2(.5 + .47 * math.cos(a), .5 + .47 * math.sin(a))
                         for a in (-math.pi / 2, math.pi / 6, 5 * math.pi / 6))
        return ()

    @cached_property
    def planes(self):
        result = []
        vertices = self.vertices
        for a, b in zip(vertices, vertices[1:] + vertices[:1]):
            edge = b - a
            result.append((a, Vec2(-edge.y, edge.x).unit()))
        return tuple(result)

    def contacts(self, position: Vec2, radius: float) -> list[tuple[Vec2, float]]:
        """Return (inward normal, penetration) for violated ball-centre constraints."""
        if self.shape == 'circle':
            delta = Vec2(.5, .5) - position
            penetration = delta.length() + radius - .44
            return [(delta.unit(), penetration)] if penetration > 0 else []
        result = []
        for a, normal in self.planes:
            depth = radius - (position - a).dot(normal)
            if depth > 0:
                result.append((normal, depth))
        return result

    def contains(self, position: Vec2, radius: float, tolerance: float = 1e-9) -> bool:
        return all(depth <= tolerance for _, depth in self.contacts(position, radius))
