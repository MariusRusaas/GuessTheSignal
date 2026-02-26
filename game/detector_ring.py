"""Detector ring visualization and logic."""

import pygame
import math
from typing import List, Tuple, Optional
from game.constants import (
    COLOR_DETECTOR_IDLE, COLOR_DETECTOR_HIT,
    DETECTOR_ARC_ANGLE, DETECTOR_BLINK_DURATION, BLINK_FADE_STEPS
)
from game.utils import normalize_angle, point_on_circle


class Detector:
    """Single detector in the ring."""

    def __init__(self, index: int, angle: float, arc_angle: float):
        self.index = index
        self.angle = angle  # Center angle in radians
        self.arc_angle = arc_angle  # Angular width in radians
        self.is_hit = False
        self.hit_time = 0
        self.blink_progress = 0.0  # 0 = not blinking, 1 = fully bright

    def trigger_hit(self, current_time: int):
        """Trigger a hit on this detector."""
        self.is_hit = True
        self.hit_time = current_time
        self.blink_progress = 1.0

    def update(self, current_time: int):
        """Update detector state (handle blink fade)."""
        if self.is_hit:
            elapsed = current_time - self.hit_time
            if elapsed < DETECTOR_BLINK_DURATION:
                # Fade out over the blink duration
                self.blink_progress = 1.0 - (elapsed / DETECTOR_BLINK_DURATION)
            else:
                self.is_hit = False
                self.blink_progress = 0.0

    def get_color(self) -> Tuple[int, int, int]:
        """Get current color based on hit state."""
        if self.blink_progress > 0:
            # Interpolate between idle and hit colors
            r = int(COLOR_DETECTOR_IDLE[0] + (COLOR_DETECTOR_HIT[0] - COLOR_DETECTOR_IDLE[0]) * self.blink_progress)
            g = int(COLOR_DETECTOR_IDLE[1] + (COLOR_DETECTOR_HIT[1] - COLOR_DETECTOR_IDLE[1]) * self.blink_progress)
            b = int(COLOR_DETECTOR_IDLE[2] + (COLOR_DETECTOR_HIT[2] - COLOR_DETECTOR_IDLE[2]) * self.blink_progress)
            return (r, g, b)
        return COLOR_DETECTOR_IDLE


class DetectorRing:
    """Circular arrangement of detectors around the image matrix."""

    def __init__(self, num_detectors: int, center: Tuple[float, float], radius: float):
        self.num_detectors = num_detectors
        self.center = center
        self.radius = radius
        self.inner_radius = radius - 15  # Inner edge of detector arc
        self.outer_radius = radius + 15  # Outer edge of detector arc

        # Calculate arc angle for each detector - fill full spacing so detectors are back-to-back
        self.detector_spacing = 2 * math.pi / num_detectors
        self.arc_angle = self.detector_spacing

        # Create detectors
        self.detectors: List[Detector] = []
        for i in range(num_detectors):
            angle = i * self.detector_spacing
            self.detectors.append(Detector(i, angle, self.arc_angle))

        # Pending hits (for TOF delayed triggering)
        self.pending_hits: List[Tuple[int, int]] = []  # (detector_index, trigger_time)

    def get_detector_position(self, index: int) -> Tuple[float, float]:
        """Get the center position of a detector on the ring."""
        angle = self.detectors[index].angle
        return point_on_circle(self.center, self.radius, angle)

    def find_closest_detector(self, point: Tuple[float, float]) -> int:
        """Find the detector closest to a given point on the ring."""
        # Calculate angle from center to point
        dx = point[0] - self.center[0]
        dy = point[1] - self.center[1]
        angle = normalize_angle(math.atan2(dy, dx))

        # Find closest detector by angle
        best_index = 0
        best_diff = float('inf')

        for i, detector in enumerate(self.detectors):
            diff = abs(normalize_angle(angle - detector.angle))
            if diff > math.pi:
                diff = 2 * math.pi - diff
            if diff < best_diff:
                best_diff = diff
                best_index = i

        return best_index

    def schedule_hit(self, detector_index: int, delay_ms: int, current_time: int):
        """Schedule a detector hit with a delay (for TOF effect)."""
        trigger_time = current_time + delay_ms
        self.pending_hits.append((detector_index, trigger_time))

    def update(self, current_time: int):
        """Update all detectors and process pending hits."""
        # Process pending hits
        remaining_hits = []
        for det_index, trigger_time in self.pending_hits:
            if current_time >= trigger_time:
                self.detectors[det_index].trigger_hit(current_time)
            else:
                remaining_hits.append((det_index, trigger_time))
        self.pending_hits = remaining_hits

        # Update all detectors
        for detector in self.detectors:
            detector.update(current_time)

    def draw(self, surface: pygame.Surface):
        """Draw the detector ring."""
        for detector in self.detectors:
            color = detector.get_color()

            # Draw arc segment
            start_angle = detector.angle - self.arc_angle / 2
            end_angle = detector.angle + self.arc_angle / 2

            # Create arc as polygon points
            points = []
            num_points = 8

            # Outer arc
            for i in range(num_points + 1):
                t = i / num_points
                a = start_angle + t * (end_angle - start_angle)
                points.append(point_on_circle(self.center, self.outer_radius, a))

            # Inner arc (reversed)
            for i in range(num_points, -1, -1):
                t = i / num_points
                a = start_angle + t * (end_angle - start_angle)
                points.append(point_on_circle(self.center, self.inner_radius, a))

            if len(points) >= 3:
                pygame.draw.polygon(surface, color, points)

                # Draw outline
                outline_color = tuple(max(0, c - 30) for c in color)
                pygame.draw.polygon(surface, outline_color, points, 1)

    def get_active_lor(self) -> Optional[Tuple[int, int]]:
        """Get currently active LOR (two detectors that are both hit)."""
        hit_indices = [d.index for d in self.detectors if d.is_hit]
        if len(hit_indices) >= 2:
            return (hit_indices[0], hit_indices[1])
        return None
