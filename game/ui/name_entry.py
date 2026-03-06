"""Name entry screen shown before each game."""

import pygame
from typing import Optional
import game.constants as constants
from game.constants import COLOR_TEXT, COLOR_TEXT_HIGHLIGHT


class NameEntry:
    """Screen for entering player name before a game starts."""

    def __init__(self, renderer):
        self.renderer = renderer
        self.name = ""
        self.difficulty = ""
        self._error = ""
        self.start_button = None
        self.back_button = None

    def reset(self, difficulty: str):
        """Reset for a new name entry with the given difficulty."""
        self.name = ""
        self.difficulty = difficulty
        self._error = ""

    def _create_buttons(self):
        w = constants.WINDOW_WIDTH
        h = constants.WINDOW_HEIGHT
        btn_w = constants.MENU_BUTTON_WIDTH
        btn_h = constants.MENU_BUTTON_HEIGHT
        self.start_button = pygame.Rect(w // 2 - btn_w // 2, int(h * 0.60), btn_w, btn_h)
        self.back_button = pygame.Rect(20, h - btn_h - 20, 120, btn_h)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Returns 'start', 'back', or None."""
        self._create_buttons()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.name = self.name[:-1]
                self._error = ""
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.name.strip():
                    return "start"
                self._error = "Please enter a name"
            elif event.key == pygame.K_ESCAPE:
                return "back"
            elif len(event.unicode) == 1 and event.unicode.isprintable() and len(self.name) < 30:
                self.name += event.unicode
                self._error = ""
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = pygame.mouse.get_pos()
            if self.start_button and self.start_button.collidepoint(mp):
                if self.name.strip():
                    return "start"
                self._error = "Please enter a name"
            elif self.back_button and self.back_button.collidepoint(mp):
                return "back"
        return None

    def draw(self, current_time: int):
        """Draw the name entry screen."""
        self._create_buttons()
        self.renderer.clear()
        self.renderer.draw_intro_background()

        w = constants.WINDOW_WIDTH
        h = constants.WINDOW_HEIGHT

        self.renderer.draw_text(
            "Enter Your Name",
            (w // 2, int(h * 0.12)),
            COLOR_TEXT_HIGHLIGHT, font_size="large", center=True
        )
        self.renderer.draw_text(
            f"Difficulty: {self.difficulty}",
            (w // 2, int(h * 0.20)),
            COLOR_TEXT, font_size="small", center=True
        )
        self.renderer.draw_text(
            "Your name will appear on the scoreboard.",
            (w // 2, int(h * 0.26)),
            (150, 150, 160), font_size="small", center=True
        )

        # Text input box
        box_w = int(w * 0.42)
        box_h = max(40, int(h * 0.07))
        box_x = w // 2 - box_w // 2
        box_y = int(h * 0.38)
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.renderer.screen, (245, 245, 250), box_rect, border_radius=6)
        pygame.draw.rect(self.renderer.screen, (100, 110, 160), box_rect, 2, border_radius=6)

        cursor = "|" if (current_time // 500) % 2 == 0 else " "
        self.renderer._update_fonts()
        text_h = self.renderer.font_medium.get_height()
        self.renderer.draw_text(
            self.name + cursor,
            (box_x + 10, box_y + (box_h - text_h) // 2),
            (30, 30, 50), font_size="medium"
        )

        if self._error:
            self.renderer.draw_text(
                self._error,
                (w // 2, int(h * 0.52)),
                (180, 60, 60), font_size="small", center=True
            )

        mouse_pos = pygame.mouse.get_pos()
        self.renderer.draw_button(
            self.start_button, "Start Game",
            self.start_button.collidepoint(mouse_pos),
            color=(60, 120, 80), hover_color=(80, 150, 100)
        )
        self.renderer.draw_button(
            self.back_button, "Back",
            self.back_button.collidepoint(mouse_pos)
        )
