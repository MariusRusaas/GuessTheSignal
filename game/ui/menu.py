"""Main menu and difficulty selection UI."""

import pygame
from typing import Optional
import game.constants as constants
from game.constants import (
    DIFFICULTY_ORDER,
    COLOR_TEXT, COLOR_TEXT_HIGHLIGHT
)


class MainMenu:
    """Main menu screen."""

    def __init__(self, renderer):
        self.renderer = renderer
        self.buttons = []
        self.selected_difficulty: Optional[str] = None
        self.load_scores_button = None

    def _create_buttons(self):
        """Create menu buttons based on current window size."""
        self.buttons = []

        w = constants.WINDOW_WIDTH
        h = constants.WINDOW_HEIGHT
        btn_w = constants.MENU_BUTTON_WIDTH
        btn_h = constants.MENU_BUTTON_HEIGHT
        btn_spacing = constants.MENU_BUTTON_SPACING

        # Title position
        self.title_pos = (w // 2, int(h * 0.12))
        self.subtitle_pos = (w // 2, int(h * 0.18))

        # Buttons: Play, PET Introduction, Tutorial, Quit
        start_y = int(h * 0.26)
        button_defs = [
            ("play",      "Play Game"),
            ("tutorial",  "How to Play"),
            ("pet_intro", "PET Introduction"),
            ("quit",      "Quit"),
        ]
        for i, (action, label) in enumerate(button_defs):
            rect = pygame.Rect(
                w // 2 - btn_w // 2,
                start_y + i * (btn_h + btn_spacing),
                btn_w,
                btn_h
            )
            self.buttons.append((action, rect, label))

        # Small "Load Scores" button at lower-left
        self.load_scores_button = pygame.Rect(20, h - btn_h - 20, 140, btn_h)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle input events. Returns action string if button clicked."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            for action, rect, _ in self.buttons:
                if rect.collidepoint(mouse_pos):
                    return action
            if self.load_scores_button and self.load_scores_button.collidepoint(mouse_pos):
                return "load_scores"
        return None

    def draw(self):
        """Draw the main menu."""
        # Recreate buttons each frame to handle dynamic sizing
        self._create_buttons()

        self.renderer.clear()
        self.renderer.draw_intro_background()

        # Title
        self.renderer.draw_text(
            "GuessTheSignal",
            self.title_pos,
            COLOR_TEXT_HIGHLIGHT,
            font_size="large",
            center=True
        )

        # Subtitle
        self.renderer.draw_text(
            "A PET Imaging Game",
            self.subtitle_pos,
            COLOR_TEXT,
            font_size="small",
            center=True
        )

        # Buttons
        mouse_pos = pygame.mouse.get_pos()
        for action, rect, text in self.buttons:
            hovered = rect.collidepoint(mouse_pos)
            self.renderer.draw_button(rect, text, hovered)

        # Load Scores button (lower-left)
        if self.load_scores_button:
            hovered = self.load_scores_button.collidepoint(mouse_pos)
            self.renderer.draw_button(self.load_scores_button, "Load Scores", hovered)


class DifficultySelect:
    """Difficulty selection screen."""

    def __init__(self, renderer):
        self.renderer = renderer
        self.buttons = []
        self.back_button = None

    def _create_buttons(self):
        """Create difficulty buttons based on current window size."""
        self.buttons = []

        w = constants.WINDOW_WIDTH
        h = constants.WINDOW_HEIGHT
        btn_w = constants.MENU_BUTTON_WIDTH
        btn_h = constants.MENU_BUTTON_HEIGHT
        btn_spacing = constants.MENU_BUTTON_SPACING

        # Create a button for each difficulty
        start_y = int(h * 0.22)
        for i, difficulty in enumerate(DIFFICULTY_ORDER):
            rect = pygame.Rect(
                w // 2 - btn_w // 2,
                start_y + i * (btn_h + btn_spacing),
                btn_w,
                btn_h
            )
            self.buttons.append((difficulty, rect))

        # Back button
        self.back_button = pygame.Rect(
            20, h - btn_h - 20,
            120, btn_h
        )

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle input events. Returns difficulty name or 'back'."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()

            # Check difficulty buttons
            for difficulty, rect in self.buttons:
                if rect.collidepoint(mouse_pos):
                    return difficulty

            # Check back button
            if self.back_button and self.back_button.collidepoint(mouse_pos):
                return "back"

        return None

    def draw(self):
        """Draw the difficulty selection screen."""
        # Recreate buttons each frame
        self._create_buttons()

        self.renderer.clear()
        self.renderer.draw_intro_background()

        w = constants.WINDOW_WIDTH
        h = constants.WINDOW_HEIGHT

        # Title
        self.renderer.draw_text(
            "Select Difficulty",
            (w // 2, int(h * 0.10)),
            COLOR_TEXT_HIGHLIGHT,
            font_size="large",
            center=True
        )

        # Description
        self.renderer.draw_text(
            "Choose the challenge level",
            (w // 2, int(h * 0.16)),
            COLOR_TEXT,
            font_size="small",
            center=True
        )

        # Difficulty buttons
        mouse_pos = pygame.mouse.get_pos()
        for difficulty, rect in self.buttons:
            hovered = rect.collidepoint(mouse_pos)
            self.renderer.draw_button(rect, difficulty, hovered)

        # Back button
        hovered = self.back_button.collidepoint(mouse_pos)
        self.renderer.draw_button(self.back_button, "Back", hovered)
