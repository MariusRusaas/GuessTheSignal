"""Physics simulation for PET imaging - photon emission, TOF calculations."""

import math
import numpy as np
from typing import Tuple, List, Optional
from game.utils import distance, line_circle_intersection, normalize_angle
from game.constants import TOF_TIMING_SCALE, TOF_MIN_DELAY, TOF_MAX_DELAY


class PhotonEmission:
    """Represents a single positron annihilation event producing two photons."""

    def __init__(self, source_pos: Tuple[float, float], emission_angle: float):
        self.source_pos = source_pos
        self.emission_angle = emission_angle  # Angle of first photon (second is +180°)

    def get_photon_directions(self) -> Tuple[float, float]:
        """Get the two photon directions (180° apart)."""
        return (self.emission_angle, normalize_angle(self.emission_angle + math.pi))


class PETPhysics:
    """Handles PET imaging physics calculations."""

    def __init__(self, ring_center: Tuple[float, float], ring_radius: float):
        self.ring_center = ring_center
        self.ring_radius = ring_radius

    def emit_from_pixel(
        self,
        pixel_pos: Tuple[float, float],
        angle: Optional[float] = None
    ) -> PhotonEmission:
        """
        Create a photon emission event from a pixel position.
        If angle is None, a random angle is chosen.
        """
        if angle is None:
            angle = np.random.uniform(0, 2 * math.pi)

        return PhotonEmission(pixel_pos, angle)

    def find_detector_hits(
        self,
        emission: PhotonEmission,
        detector_ring
    ) -> Tuple[int, int, float, float]:
        """
        Find which two detectors are hit by the photon pair.
        Returns: (detector1_index, detector2_index, distance1, distance2)
        """
        dir1, dir2 = emission.get_photon_directions()

        # Find intersection points with detector ring
        hits1 = line_circle_intersection(
            emission.source_pos, dir1,
            self.ring_center, self.ring_radius
        )
        hits2 = line_circle_intersection(
            emission.source_pos, dir2,
            self.ring_center, self.ring_radius
        )

        if not hits1 or not hits2:
            # Fallback: shouldn't happen if source is inside ring
            return (0, detector_ring.num_detectors // 2, 0, 0)

        # Get the first (closest) intersection for each direction
        hit_point1 = hits1[0]
        hit_point2 = hits2[0]

        # Find closest detectors to these hit points
        det1 = detector_ring.find_closest_detector(hit_point1)
        det2 = detector_ring.find_closest_detector(hit_point2)

        # Calculate distances from source to hit points
        dist1 = distance(emission.source_pos, hit_point1)
        dist2 = distance(emission.source_pos, hit_point2)

        return (det1, det2, dist1, dist2)

    def calculate_tof_delays(
        self,
        dist1: float,
        dist2: float,
        max_possible_distance: float
    ) -> Tuple[int, int]:
        """
        Calculate the blink delay times for two detectors based on TOF.
        Returns: (delay1_ms, delay2_ms) where the closer detector has smaller delay.
        """
        # Normalize distance difference to [0, 1] range
        diff = abs(dist1 - dist2)
        normalized_diff = min(diff / max_possible_distance, 1.0)

        # Scale to visible timing range
        delay_diff = int(TOF_MIN_DELAY + normalized_diff * (TOF_MAX_DELAY - TOF_MIN_DELAY))

        # Closer detector blinks first (delay = 0), farther one has the delay
        if dist1 <= dist2:
            return (0, delay_diff)
        else:
            return (delay_diff, 0)

    def calculate_probability_zone(
        self,
        det1_pos: Tuple[float, float],
        det2_pos: Tuple[float, float],
        tof_delay_diff: float,
        grid_size: int,
        matrix
    ) -> Tuple[List[Tuple[int, int]], List[float]]:
        """
        Calculate probability zone along LOR based on TOF information.
        Returns list of (row, col) positions and their probability intensities.
        """
        pixels = []
        intensities = []

        # Calculate LOR parameters
        lor_length = distance(det1_pos, det2_pos)
        dx = (det2_pos[0] - det1_pos[0]) / lor_length
        dy = (det2_pos[1] - det1_pos[1]) / lor_length

        # Estimate source position along LOR based on TOF
        # Delay difference relates to position: t_diff = 2 * d_from_center / c
        # Positive delay_diff means det1 is closer, so source is towards det1 side
        max_delay = TOF_MAX_DELAY - TOF_MIN_DELAY
        position_ratio = 0.5 - (tof_delay_diff / max_delay) * 0.4  # Center estimate

        estimated_pos_along_lor = position_ratio * lor_length
        estimated_x = det1_pos[0] + dx * estimated_pos_along_lor
        estimated_y = det1_pos[1] + dy * estimated_pos_along_lor

        # Create Gaussian probability distribution along LOR
        sigma = lor_length * 0.15  # Uncertainty width

        # Sample points along LOR within the grid
        num_samples = int(lor_length / (matrix.pixel_size * 0.5))
        for i in range(num_samples):
            t = i / (num_samples - 1) if num_samples > 1 else 0.5
            sample_x = det1_pos[0] + dx * t * lor_length
            sample_y = det1_pos[1] + dy * t * lor_length

            # Convert to grid coordinates
            pixel = matrix.screen_to_pixel(sample_x, sample_y)
            if pixel is not None:
                row, col = pixel

                # Calculate Gaussian probability
                dist_from_estimate = distance(
                    (sample_x, sample_y),
                    (estimated_x, estimated_y)
                )
                intensity = math.exp(-(dist_from_estimate ** 2) / (2 * sigma ** 2))

                if (row, col) not in [(p[0], p[1]) for p in pixels]:
                    pixels.append((row, col))
                    intensities.append(intensity)

        return pixels, intensities


def calculate_dice_score(true_mask: np.ndarray, guessed_pixels: set) -> float:
    """
    Calculate DICE similarity coefficient.
    DICE = 2|A∩B| / (|A| + |B|)
    """
    # Convert guessed pixels to mask
    guessed_mask = np.zeros_like(true_mask, dtype=bool)
    for row, col in guessed_pixels:
        if 0 <= row < true_mask.shape[0] and 0 <= col < true_mask.shape[1]:
            guessed_mask[row, col] = True

    # Calculate intersection and sizes
    intersection = np.sum(true_mask & guessed_mask)
    size_a = np.sum(true_mask)
    size_b = np.sum(guessed_mask)

    if size_a + size_b == 0:
        return 1.0  # Both empty = perfect match

    dice = 2 * intersection / (size_a + size_b)
    return dice
