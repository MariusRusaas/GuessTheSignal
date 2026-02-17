"""End screen showing results and DICE score."""

import pygame
from typing import Optional
import game.constants as constants
from game.constants import COLOR_TEXT, COLOR_TEXT_HIGHLIGHT


class EndScreen:
    """Results screen showing DICE score and options."""

    def __init__(self, renderer):
        self.renderer = renderer
        self.dice_score = 0.0
        self.true_pixels = 0
        self.guessed_pixels = 0
        self.correct_pixels = 0

        # Buttons will be created dynamically
        self.play_again_button = None
        self.menu_button = None

    def set_results(
        self,
        dice_score: float,
        true_pixels: int,
        guessed_pixels: int,
        correct_pixels: int
    ):
        """Set the results to display."""
        self.dice_score = dice_score
        self.true_pixels = true_pixels
        self.guessed_pixels = guessed_pixels
        self.correct_pixels = correct_pixels

    def _create_buttons(self):
        """Create buttons based on current window size."""
        w = constants.WINDOW_WIDTH
        h = constants.WINDOW_HEIGHT

        panel_width = int(w * 0.32)
        panel_x = w - panel_width - 20
        panel_y = int(h * 0.11)
        panel_height = h - int(h * 0.22)

        button_width = int(panel_width * 0.4)
        button_height = 45
        button_y = panel_y + panel_height - 70

        self.play_again_button = pygame.Rect(
            panel_x + 15,
            button_y,
            button_width,
            button_height
        )

        self.menu_button = pygame.Rect(
            panel_x + panel_width - button_width - 15,
            button_y,
            button_width,
            button_height
        )

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle input events. Returns 'play_again' or 'menu'."""
        # Ensure buttons are created with current dimensions
        self._create_buttons()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()

            if self.play_again_button.collidepoint(mouse_pos):
                return "play_again"

            if self.menu_button.collidepoint(mouse_pos):
                return "menu"

        return None

    def _get_score_grade(self) -> tuple:
        """Get grade and color based on DICE score."""
        if self.dice_score >= 0.9:
            return "Excellent!", (100, 255, 100)
        elif self.dice_score >= 0.75:
            return "Great!", (150, 255, 100)
        elif self.dice_score >= 0.6:
            return "Good", (255, 255, 100)
        elif self.dice_score >= 0.4:
            return "Fair", (255, 200, 100)
        else:
            return "Keep Practicing", (255, 150, 100)

    def draw(self):
        """Draw the end screen as an overlay panel on the right side."""
        w = constants.WINDOW_WIDTH
        h = constants.WINDOW_HEIGHT

        # Draw semi-transparent panel on the right side
        panel_width = int(w * 0.32)
        panel_x = w - panel_width - 20
        panel_y = int(h * 0.11)
        panel_height = h - int(h * 0.22)

        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill((30, 30, 45, 230))
        self.renderer.screen.blit(panel_surface, (panel_x, panel_y))

        # Draw panel border
        pygame.draw.rect(
            self.renderer.screen,
            (80, 80, 100),
            (panel_x, panel_y, panel_width, panel_height),
            2,
            border_radius=8
        )

        # Center x for text within panel
        text_center_x = panel_x + panel_width // 2

        # Title
        self.renderer.draw_text(
            "Results",
            (text_center_x, panel_y + 30),
            COLOR_TEXT_HIGHLIGHT,
            font_size="large",
            center=True
        )

        # DICE Score (big and prominent)
        score_percent = int(self.dice_score * 100)
        grade, grade_color = self._get_score_grade()

        self.renderer.draw_text(
            f"DICE Score: {score_percent}%",
            (text_center_x, panel_y + 90),
            grade_color,
            font_size="large",
            center=True
        )

        self.renderer.draw_text(
            grade,
            (text_center_x, panel_y + 130),
            grade_color,
            font_size="medium",
            center=True
        )

        # Statistics
        stats_y = panel_y + 180
        line_height = 30

        stats = [
            f"True shape: {self.true_pixels} px",
            f"Your guess: {self.guessed_pixels} px",
            f"Correct: {self.correct_pixels} px",
        ]

        for i, stat in enumerate(stats):
            self.renderer.draw_text(
                stat,
                (text_center_x, stats_y + i * line_height),
                COLOR_TEXT,
                font_size="small",
                center=True
            )

        # Legend
        legend_y = stats_y + len(stats) * line_height + 30
        self.renderer.draw_text(
            "Legend:",
            (text_center_x, legend_y),
            COLOR_TEXT_HIGHLIGHT,
            font_size="small",
            center=True
        )

        legend_items = [
            ("Green = Correct", (100, 200, 100)),
            ("Red = Wrong guess", (200, 100, 100)),
            ("Blue = Missed", (100, 100, 200)),
        ]

        for i, (text, color) in enumerate(legend_items):
            self.renderer.draw_text(
                text,
                (text_center_x, legend_y + 25 + i * 25),
                color,
                font_size="small",
                center=True
            )

        # Create buttons at bottom of panel
        self._create_buttons()

        mouse_pos = pygame.mouse.get_pos()

        hovered = self.play_again_button.collidepoint(mouse_pos)
        self.renderer.draw_button(
            self.play_again_button, "Play Again", hovered,
            color=(60, 120, 80),
            hover_color=(80, 150, 100)
        )

        hovered = self.menu_button.collidepoint(mouse_pos)
        self.renderer.draw_button(self.menu_button, "Menu", hovered)


class CorrectionPhase:
    """UI for correction phase before final scoring."""

    def __init__(self, renderer):
        self.renderer = renderer

        # Buttons will be created dynamically
        self.finalize_button = None
        self.clear_button = None

    def _create_buttons(self):
        """Create buttons based on current window size."""
        w = constants.WINDOW_WIDTH
        h = constants.WINDOW_HEIGHT

        self.finalize_button = pygame.Rect(
            w - 180,
            h - 70,
            160,
            50
        )

        self.clear_button = pygame.Rect(
            20,
            h - 70,
            120,
            50
        )

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle input events. Returns 'finalize' or 'clear'."""
        # Ensure buttons are created with current dimensions
        self._create_buttons()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()

            if self.finalize_button.collidepoint(mouse_pos):
                return "finalize"

            if self.clear_button.collidepoint(mouse_pos):
                return "clear"

        return None

    def draw(self):
        """Draw correction phase UI elements."""
        # Recreate buttons each frame to handle dynamic sizing
        self._create_buttons()

        w = constants.WINDOW_WIDTH
        h = constants.WINDOW_HEIGHT

        mouse_pos = pygame.mouse.get_pos()

        # Finalize button
        hovered = self.finalize_button.collidepoint(mouse_pos)
        self.renderer.draw_button(
            self.finalize_button, "Finalize", hovered,
            color=(60, 120, 80),
            hover_color=(80, 150, 100)
        )

        # Clear button
        hovered = self.clear_button.collidepoint(mouse_pos)
        self.renderer.draw_button(
            self.clear_button, "Clear All", hovered,
            color=(120, 60, 60),
            hover_color=(150, 80, 80)
        )

        # Instructions
        self.renderer.draw_text(
            "Click pixels to toggle guesses. Click Finalize when ready.",
            (w // 2, h - 100),
            (150, 150, 160),
            font_size="small",
            center=True
        )
