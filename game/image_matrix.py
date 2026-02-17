"""Image matrix (grid) handling for the game."""

import pygame
import numpy as np
from typing import Tuple, Optional, Set
from game.constants import COLOR_GRID, COLOR_SHAPE_GUESSED, COLOR_SHAPE_CORRECT, COLOR_SHAPE_WRONG


class ImageMatrix:
    """Grid/matrix representing the imaging area."""

    def __init__(self, grid_size: int, center: Tuple[float, float], pixel_size: float):
        self.grid_size = grid_size
        self.center = center
        self.pixel_size = pixel_size

        # Calculate top-left corner
        total_size = grid_size * pixel_size
        self.top_left = (
            center[0] - total_size / 2,
            center[1] - total_size / 2
        )

        # Guessed pixels (set of (row, col) tuples)
        self.guessed_pixels: Set[Tuple[int, int]] = set()

        # True shape mask (set after shape generation)
        self.true_shape: Optional[np.ndarray] = None

    def set_true_shape(self, shape_mask: np.ndarray):
        """Set the true shape that players are trying to reconstruct."""
        self.true_shape = shape_mask

    def pixel_to_screen(self, row: int, col: int) -> Tuple[float, float]:
        """Convert grid pixel (row, col) to screen coordinates (center of pixel)."""
        x = self.top_left[0] + col * self.pixel_size + self.pixel_size / 2
        y = self.top_left[1] + row * self.pixel_size + self.pixel_size / 2
        return (x, y)

    def screen_to_pixel(self, screen_x: float, screen_y: float) -> Optional[Tuple[int, int]]:
        """Convert screen coordinates to grid pixel (row, col). Returns None if outside grid."""
        # Calculate relative position
        rel_x = screen_x - self.top_left[0]
        rel_y = screen_y - self.top_left[1]

        # Check bounds
        total_size = self.grid_size * self.pixel_size
        if rel_x < 0 or rel_x >= total_size or rel_y < 0 or rel_y >= total_size:
            return None

        col = int(rel_x / self.pixel_size)
        row = int(rel_y / self.pixel_size)

        # Clamp to valid range
        col = max(0, min(self.grid_size - 1, col))
        row = max(0, min(self.grid_size - 1, row))

        return (row, col)

    def toggle_guess(self, row: int, col: int) -> bool:
        """Toggle a pixel guess. Returns True if added, False if removed."""
        pixel = (row, col)
        if pixel in self.guessed_pixels:
            self.guessed_pixels.remove(pixel)
            return False
        else:
            self.guessed_pixels.add(pixel)
            return True

    def add_guess(self, row: int, col: int):
        """Add a pixel guess."""
        self.guessed_pixels.add((row, col))

    def remove_guess(self, row: int, col: int):
        """Remove a pixel guess."""
        self.guessed_pixels.discard((row, col))

    def clear_guesses(self):
        """Clear all guessed pixels."""
        self.guessed_pixels.clear()

    def is_point_in_grid(self, screen_x: float, screen_y: float) -> bool:
        """Check if a screen point is within the grid area."""
        return self.screen_to_pixel(screen_x, screen_y) is not None

    def get_grid_bounds(self) -> Tuple[float, float, float, float]:
        """Get the bounding rectangle of the grid (x, y, width, height)."""
        total_size = self.grid_size * self.pixel_size
        return (self.top_left[0], self.top_left[1], total_size, total_size)

    def draw(self, surface: pygame.Surface, show_results: bool = False):
        """Draw the grid and guessed pixels."""
        total_size = self.grid_size * self.pixel_size

        # Draw grid background
        pygame.draw.rect(
            surface,
            COLOR_GRID,
            (self.top_left[0], self.top_left[1], total_size, total_size)
        )

        # Draw grid lines
        line_color = (50, 50, 60)
        for i in range(self.grid_size + 1):
            # Vertical lines
            x = self.top_left[0] + i * self.pixel_size
            pygame.draw.line(
                surface, line_color,
                (x, self.top_left[1]),
                (x, self.top_left[1] + total_size)
            )
            # Horizontal lines
            y = self.top_left[1] + i * self.pixel_size
            pygame.draw.line(
                surface, line_color,
                (self.top_left[0], y),
                (self.top_left[0] + total_size, y)
            )

        # Draw guessed pixels
        if show_results and self.true_shape is not None:
            # Show correct/incorrect coloring
            for row, col in self.guessed_pixels:
                x = self.top_left[0] + col * self.pixel_size
                y = self.top_left[1] + row * self.pixel_size

                if self.true_shape[row, col]:
                    color = COLOR_SHAPE_CORRECT
                else:
                    color = COLOR_SHAPE_WRONG

                # Draw with alpha
                s = pygame.Surface((self.pixel_size - 1, self.pixel_size - 1), pygame.SRCALPHA)
                s.fill(color)
                surface.blit(s, (x + 0.5, y + 0.5))

            # Also show missed pixels (true shape pixels not guessed)
            for row in range(self.grid_size):
                for col in range(self.grid_size):
                    if self.true_shape[row, col] and (row, col) not in self.guessed_pixels:
                        x = self.top_left[0] + col * self.pixel_size
                        y = self.top_left[1] + row * self.pixel_size

                        # Draw missed pixels with different color
                        s = pygame.Surface((self.pixel_size - 1, self.pixel_size - 1), pygame.SRCALPHA)
                        s.fill((100, 100, 200, 100))  # Blue-ish for missed
                        surface.blit(s, (x + 0.5, y + 0.5))
        else:
            # Normal gameplay - just show guessed pixels
            for row, col in self.guessed_pixels:
                x = self.top_left[0] + col * self.pixel_size
                y = self.top_left[1] + row * self.pixel_size

                # Draw with alpha
                s = pygame.Surface((self.pixel_size - 1, self.pixel_size - 1), pygame.SRCALPHA)
                s.fill(COLOR_SHAPE_GUESSED)
                surface.blit(s, (x + 0.5, y + 0.5))

    def draw_probability_zone(self, surface: pygame.Surface, pixels: list, intensities: list):
        """Draw probability zone highlighting (for tutorial mode)."""
        for (row, col), intensity in zip(pixels, intensities):
            if 0 <= row < self.grid_size and 0 <= col < self.grid_size:
                x = self.top_left[0] + col * self.pixel_size
                y = self.top_left[1] + row * self.pixel_size

                # Draw with varying alpha based on intensity
                alpha = int(intensity * 150)
                s = pygame.Surface((self.pixel_size - 1, self.pixel_size - 1), pygame.SRCALPHA)
                s.fill((255, 255, 100, alpha))
                surface.blit(s, (x + 0.5, y + 0.5))
