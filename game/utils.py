"""Helper utility functions."""

import math
from typing import Tuple, List


def distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculate Euclidean distance between two points."""
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def normalize_angle(angle: float) -> float:
    """Normalize angle to [0, 2*pi) range."""
    while angle < 0:
        angle += 2 * math.pi
    while angle >= 2 * math.pi:
        angle -= 2 * math.pi
    return angle


def point_on_circle(center: Tuple[float, float], radius: float, angle: float) -> Tuple[float, float]:
    """Get point on circle at given angle (radians)."""
    return (
        center[0] + radius * math.cos(angle),
        center[1] + radius * math.sin(angle)
    )


def line_circle_intersection(
    line_start: Tuple[float, float],
    line_angle: float,
    circle_center: Tuple[float, float],
    circle_radius: float
) -> List[Tuple[float, float]]:
    """
    Find intersection points of a line (starting from point going in direction)
    with a circle.
    """
    # Parametric line: P = line_start + t * direction
    dx = math.cos(line_angle)
    dy = math.sin(line_angle)

    # Translate to circle-centered coordinates
    fx = line_start[0] - circle_center[0]
    fy = line_start[1] - circle_center[1]

    # Quadratic equation coefficients
    a = dx * dx + dy * dy
    b = 2 * (fx * dx + fy * dy)
    c = fx * fx + fy * fy - circle_radius * circle_radius

    discriminant = b * b - 4 * a * c

    if discriminant < 0:
        return []

    intersections = []
    sqrt_disc = math.sqrt(discriminant)

    t1 = (-b - sqrt_disc) / (2 * a)
    t2 = (-b + sqrt_disc) / (2 * a)

    for t in [t1, t2]:
        if t > 0:  # Only forward direction
            px = line_start[0] + t * dx
            py = line_start[1] + t * dy
            intersections.append((px, py))

    return intersections


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b."""
    return a + (b - a) * t


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value to range [min_val, max_val]."""
    return max(min_val, min(max_val, value))


def ease_out_quad(t: float) -> float:
    """Quadratic ease-out function for animations."""
    return 1 - (1 - t) ** 2


def ease_in_out_quad(t: float) -> float:
    """Quadratic ease-in-out function."""
    if t < 0.5:
        return 2 * t * t
    else:
        return 1 - (-2 * t + 2) ** 2 / 2
