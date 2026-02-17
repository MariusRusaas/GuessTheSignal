"""Main rendering logic for the game."""

import pygame
import math
from typing import Tuple, Optional, List
import game.constants as constants
from game.constants import COLOR_BACKGROUND, COLOR_LOR_LINE, COLOR_TEXT, LOR_LINE_WIDTH


class Renderer:
    """Handles all rendering for the game."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self._last_height = 0
        self._update_fonts()

    def _update_fonts(self):
        """Update font sizes based on current window height."""
        h = constants.WINDOW_HEIGHT
        if h == self._last_height:
            return  # No change needed

        self._last_height = h
        # Scale fonts relative to a reference height of 900px
        scale = h / 900.0
        self.font_large = pygame.font.Font(None, max(24, int(48 * scale)))
        self.font_medium = pygame.font.Font(None, max(20, int(36 * scale)))
        self.font_small = pygame.font.Font(None, max(16, int(28 * scale)))

    def clear(self):
        """Clear the screen with background color."""
        self.screen.fill(COLOR_BACKGROUND)

    def draw_lor_line(
        self,
        start_pos: Tuple[float, float],
        end_pos: Tuple[float, float],
        alpha: int = 180
    ):
        """Draw a Line of Response between two detector positions."""
        # Create a surface with alpha for the line
        # Calculate line bounds
        min_x = min(start_pos[0], end_pos[0]) - 10
        min_y = min(start_pos[1], end_pos[1]) - 10
        max_x = max(start_pos[0], end_pos[0]) + 10
        max_y = max(start_pos[1], end_pos[1]) + 10

        width = int(max_x - min_x)
        height = int(max_y - min_y)

        if width > 0 and height > 0:
            line_surface = pygame.Surface((width, height), pygame.SRCALPHA)

            # Adjust positions relative to surface
            local_start = (start_pos[0] - min_x, start_pos[1] - min_y)
            local_end = (end_pos[0] - min_x, end_pos[1] - min_y)

            color = (*COLOR_LOR_LINE[:3], alpha)
            pygame.draw.line(
                line_surface, color,
                local_start, local_end,
                LOR_LINE_WIDTH
            )

            self.screen.blit(line_surface, (min_x, min_y))

    def draw_emission_indicator(
        self,
        position: Tuple[float, float],
        progress: float
    ):
        """Draw an indicator at the emission point (expanding circle)."""
        if progress > 0:
            radius = int(5 + progress * 20)
            alpha = int(255 * (1 - progress))

            s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 200, 50, alpha), (radius, radius), radius, 2)
            self.screen.blit(s, (position[0] - radius, position[1] - radius))

    def draw_text(
        self,
        text: str,
        position: Tuple[float, float],
        color: Tuple[int, int, int] = COLOR_TEXT,
        font_size: str = "medium",
        center: bool = False
    ):
        """Draw text on the screen."""
        # Update fonts if window size changed
        self._update_fonts()

        if font_size == "large":
            font = self.font_large
        elif font_size == "small":
            font = self.font_small
        else:
            font = self.font_medium

        text_surface = font.render(text, True, color)

        if center:
            rect = text_surface.get_rect(center=position)
            self.screen.blit(text_surface, rect)
        else:
            self.screen.blit(text_surface, position)

    def draw_button(
        self,
        rect: pygame.Rect,
        text: str,
        hovered: bool = False,
        color: Tuple[int, int, int] = None,
        hover_color: Tuple[int, int, int] = None
    ):
        """Draw a button."""
        from game.constants import COLOR_BUTTON, COLOR_BUTTON_HOVER, COLOR_BUTTON_TEXT

        # Update fonts if window size changed
        self._update_fonts()

        if color is None:
            color = COLOR_BUTTON
        if hover_color is None:
            hover_color = COLOR_BUTTON_HOVER

        current_color = hover_color if hovered else color

        # Draw button background
        pygame.draw.rect(self.screen, current_color, rect, border_radius=8)

        # Draw button border
        border_color = tuple(min(255, c + 30) for c in current_color)
        pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=8)

        # Draw text
        text_surface = self.font_medium.render(text, True, COLOR_BUTTON_TEXT)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)

    def draw_progress_bar(
        self,
        position: Tuple[float, float],
        width: float,
        height: float,
        progress: float,
        color: Tuple[int, int, int] = (100, 200, 100)
    ):
        """Draw a progress bar."""
        # Background
        pygame.draw.rect(
            self.screen,
            (50, 50, 60),
            (position[0], position[1], width, height),
            border_radius=4
        )

        # Fill
        fill_width = width * min(1.0, max(0.0, progress))
        if fill_width > 0:
            pygame.draw.rect(
                self.screen,
                color,
                (position[0], position[1], fill_width, height),
                border_radius=4
            )

        # Border
        pygame.draw.rect(
            self.screen,
            (80, 80, 90),
            (position[0], position[1], width, height),
            2,
            border_radius=4
        )

    def draw_ring_outline(
        self,
        center: Tuple[float, float],
        radius: float,
        color: Tuple[int, int, int] = (60, 60, 70)
    ):
        """Draw a circle outline (for reference)."""
        pygame.draw.circle(self.screen, color, center, int(radius), 1)
