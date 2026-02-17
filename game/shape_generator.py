"""Medical-inspired shape generation for PET imaging simulation."""

import numpy as np
from scipy.ndimage import binary_erosion, gaussian_filter
from typing import Tuple
import math


def create_blob(grid_size: int, seed: int = None) -> np.ndarray:
    """Create a simple blob shape using noise and thresholding."""
    if seed is not None:
        np.random.seed(seed)

    # Create base ellipse - smaller size with more random placement
    y, x = np.ogrid[:grid_size, :grid_size]
    # More random center position - can be up to 1/4 of grid away from center
    offset_range = max(1, grid_size // 4)
    center_x = grid_size // 2 + np.random.randint(-offset_range, offset_range + 1)
    center_y = grid_size // 2 + np.random.randint(-offset_range, offset_range + 1)

    radius_x = grid_size // 5 + np.random.randint(-grid_size // 12, max(1, grid_size // 12) + 1)
    radius_y = grid_size // 5 + np.random.randint(-grid_size // 12, max(1, grid_size // 12) + 1)

    # Ellipse equation
    ellipse = ((x - center_x) / max(1, radius_x)) ** 2 + ((y - center_y) / max(1, radius_y)) ** 2 <= 1

    # Add some noise for irregularity
    noise = np.random.random((grid_size, grid_size))
    noise = gaussian_filter(noise, sigma=grid_size / 8)
    noise = (noise - noise.min()) / (noise.max() - noise.min() + 1e-6)

    # Combine ellipse with noise
    shape = ellipse.astype(float) * 0.7 + (noise > 0.5).astype(float) * 0.3
    shape = gaussian_filter(shape, sigma=1.5)

    return (shape > 0.5).astype(bool)


def create_kidney(grid_size: int, seed: int = None) -> np.ndarray:
    """Create a kidney (bean) shaped region."""
    if seed is not None:
        np.random.seed(seed)

    shape = np.zeros((grid_size, grid_size), dtype=bool)
    # More random center position
    offset_range = max(1, grid_size // 5)
    center_x = grid_size // 2 + np.random.randint(-offset_range, offset_range + 1)
    center_y = grid_size // 2 + np.random.randint(-offset_range, offset_range + 1)

    # Kidney is like an ellipse with a concave indent - smaller size
    for y in range(grid_size):
        for x in range(grid_size):
            # Normalized coordinates - larger divisor = smaller shape
            nx = (x - center_x) / (grid_size / 4.5)
            ny = (y - center_y) / (grid_size / 6)

            # Basic ellipse
            ellipse_val = nx ** 2 + ny ** 2

            # Indent on one side (creates bean shape)
            indent = 0.3 * math.exp(-((nx + 0.5) ** 2 + ny ** 2) * 3)

            if ellipse_val - indent < 1:
                shape[y, x] = True

    # Smooth the edges
    shape = gaussian_filter(shape.astype(float), sigma=1.2) > 0.5

    return shape


def create_liver(grid_size: int, seed: int = None) -> np.ndarray:
    """Create a liver-like irregular polygon shape."""
    if seed is not None:
        np.random.seed(seed)

    shape = np.zeros((grid_size, grid_size), dtype=bool)
    # More random center position
    offset_range = max(1, grid_size // 6)
    center_x = grid_size // 2 + np.random.randint(-offset_range, offset_range + 1)
    center_y = grid_size // 2 + np.random.randint(-offset_range, offset_range + 1)

    # Create irregular shape using varying radius - smaller size
    for y in range(grid_size):
        for x in range(grid_size):
            dx = x - center_x
            dy = y - center_y

            angle = math.atan2(dy, dx)
            dist = math.sqrt(dx ** 2 + dy ** 2)

            # Varying radius based on angle - smaller base radius
            base_radius = grid_size / 5
            # Add lobes
            radius = base_radius * (1 +
                0.25 * math.cos(angle * 2) +
                0.12 * math.sin(angle * 3) +
                0.08 * math.cos(angle * 5))

            # Right side larger (liver shape)
            if angle > -math.pi / 2 and angle < math.pi / 2:
                radius *= 1.15

            if dist < radius:
                shape[y, x] = True

    # Smooth edges
    shape = gaussian_filter(shape.astype(float), sigma=1.5) > 0.5

    return shape


def create_heart(grid_size: int, seed: int = None) -> np.ndarray:
    """Create a simplified heart silhouette."""
    if seed is not None:
        np.random.seed(seed)

    shape = np.zeros((grid_size, grid_size), dtype=bool)
    # More random center position
    offset_range = max(1, grid_size // 6)
    center_x = grid_size // 2 + np.random.randint(-offset_range, offset_range + 1)
    center_y = grid_size // 2 + grid_size // 10 + np.random.randint(-offset_range, offset_range + 1)
    scale = grid_size / 4.5  # Smaller scale = smaller heart

    for y in range(grid_size):
        for x in range(grid_size):
            # Normalized coordinates
            nx = (x - center_x) / scale
            ny = (center_y - y) / scale  # Flip y for heart orientation

            # Heart curve equation (modified cardioid)
            # (x^2 + y^2 - 1)^3 - x^2*y^3 < 0
            val = (nx ** 2 + ny ** 2 - 1) ** 3 - nx ** 2 * ny ** 3

            if val < 0:
                shape[y, x] = True

    # Smooth edges
    shape = gaussian_filter(shape.astype(float), sigma=1.2) > 0.5

    return shape


def create_multi_region(grid_size: int, seed: int = None) -> np.ndarray:
    """Create multiple separate regions (lesions/tumors)."""
    if seed is not None:
        np.random.seed(seed)

    shape = np.zeros((grid_size, grid_size), dtype=bool)

    # Generate 2-4 separate regions (fewer, smaller regions)
    num_regions = np.random.randint(2, 5)

    # Keep track of used positions to avoid overlap
    used_positions = []

    for _ in range(num_regions):
        # Random position (avoiding edges and other regions)
        attempts = 0
        while attempts < 50:
            cx = np.random.randint(grid_size // 4, 3 * grid_size // 4)
            cy = np.random.randint(grid_size // 4, 3 * grid_size // 4)

            # Check distance from other regions
            valid = True
            for px, py in used_positions:
                if math.sqrt((cx - px) ** 2 + (cy - py) ** 2) < grid_size // 5:
                    valid = False
                    break

            if valid:
                used_positions.append((cx, cy))
                break
            attempts += 1

        if attempts >= 50:
            continue

        # Random ellipse parameters - smaller regions
        rx = np.random.randint(max(2, grid_size // 16), max(3, grid_size // 8))
        ry = np.random.randint(max(2, grid_size // 16), max(3, grid_size // 8))

        # Draw ellipse
        y, x = np.ogrid[:grid_size, :grid_size]
        ellipse = ((x - cx) / max(1, rx)) ** 2 + ((y - cy) / max(1, ry)) ** 2 <= 1
        shape |= ellipse

    # Smooth edges
    shape = gaussian_filter(shape.astype(float), sigma=1.2) > 0.5

    return shape


def generate_shape(shape_type: str, grid_size: int, seed: int = None) -> np.ndarray:
    """Generate a shape based on type."""
    generators = {
        "blob": create_blob,
        "kidney": create_kidney,
        "liver": create_liver,
        "heart": create_heart,
        "multi": create_multi_region
    }

    generator = generators.get(shape_type, create_blob)
    return generator(grid_size, seed)


def find_edge_pixels(shape_mask: np.ndarray) -> np.ndarray:
    """
    Find edge pixels of a shape using morphological erosion.
    Edge = shape - eroded_shape
    """
    # Create structuring element for erosion
    eroded = binary_erosion(shape_mask)

    # Edge pixels are in the original shape but not in the eroded version
    edge_pixels = shape_mask & ~eroded

    return edge_pixels


def get_edge_pixel_positions(edge_mask: np.ndarray) -> list:
    """Get list of (row, col) positions of edge pixels."""
    positions = np.argwhere(edge_mask)
    return [(int(pos[0]), int(pos[1])) for pos in positions]
