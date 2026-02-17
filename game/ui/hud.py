"""In-game HUD (Heads-Up Display)."""

import pygame
from typing import Tuple
import game.constants as constants
from game.constants import COLOR_TEXT, COLOR_TEXT_HIGHLIGHT


class HUD:
    """In-game HUD showing score, progress, and controls."""

    def __init__(self, renderer):
        self.renderer = renderer

        # HUD area and buttons will be created dynamically
        self.rect = None
        self.pause_button = None

        # State
        self.emissions_fired = 0
        self.total_emissions = 0
        self.current_difficulty = ""
        self.is_correction_phase = False

    def _create_layout(self):
        """Create HUD layout based on current window size."""
        w = constants.WINDOW_WIDTH
        hud_h = constants.HUD_HEIGHT

        self.rect = pygame.Rect(0, 0, w, hud_h)

        self.pause_button = pygame.Rect(
            w - 100, 20,
            80, 40
        )

    def reset(self):
        """Fully reset HUD state for a new game."""
        self.emissions_fired = 0
        self.total_emissions = 0
        self.current_difficulty = ""
        self.is_correction_phase = False

    def set_game_info(self, difficulty: str, total_emissions: int):
        """Set game information to display."""
        self.current_difficulty = difficulty
        self.total_emissions = total_emissions
        self.emissions_fired = 0
        self.is_correction_phase = False

    def update_progress(self, emissions_fired: int):
        """Update emission progress."""
        self.emissions_fired = emissions_fired

    def set_correction_phase(self, is_correction: bool):
        """Set whether in correction phase."""
        self.is_correction_phase = is_correction

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input events. Returns True if pause clicked."""
        # Ensure layout is created with current dimensions
        self._create_layout()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.pause_button.collidepoint(pygame.mouse.get_pos()):
                return True
        return False

    def draw(self):
        """Draw the HUD."""
        # Recreate layout each frame to handle dynamic sizing
        self._create_layout()

        w = constants.WINDOW_WIDTH
        hud_h = constants.HUD_HEIGHT
        hud_pad = constants.HUD_PADDING

        # Background
        pygame.draw.rect(
            self.renderer.screen,
            (30, 30, 40),
            self.rect
        )
        pygame.draw.line(
            self.renderer.screen,
            (60, 60, 70),
            (0, hud_h),
            (w, hud_h),
            2
        )

        # Difficulty
        self.renderer.draw_text(
            f"Difficulty: {self.current_difficulty}",
            (hud_pad, hud_pad),
            COLOR_TEXT,
            font_size="small"
        )

        # Progress
        if not self.is_correction_phase:
            progress_text = f"Emissions: {self.emissions_fired}/{self.total_emissions}"
            progress = self.emissions_fired / max(1, self.total_emissions)
        else:
            progress_text = "Correction Phase - Click to adjust your guesses"
            progress = 1.0

        self.renderer.draw_text(
            progress_text,
            (w // 2, hud_pad),
            COLOR_TEXT_HIGHLIGHT if self.is_correction_phase else COLOR_TEXT,
            font_size="small",
            center=True
        )

        # Progress bar
        bar_width = int(w * 0.17)
        bar_height = 12
        bar_x = w // 2 - bar_width // 2
        bar_y = hud_pad + 28

        self.renderer.draw_progress_bar(
            (bar_x, bar_y),
            bar_width, bar_height,
            progress,
            color=(100, 180, 100) if not self.is_correction_phase else (180, 180, 100)
        )

        # Pause button
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.pause_button.collidepoint(mouse_pos)
        self.renderer.draw_button(self.pause_button, "Menu", hovered)

        # Instructions hint
        hint = "Click grid to mark guesses" if not self.is_correction_phase else "Click to toggle pixels, then Finalize"
        self.renderer.draw_text(
            hint,
            (w - hud_pad - 300, hud_h - 25),
            (120, 120, 130),
            font_size="small"
        )
