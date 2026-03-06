"""Save and Load dialogs for the scoreboard."""

import pygame
from typing import Optional
import game.constants as constants
from game.constants import COLOR_TEXT, COLOR_TEXT_HIGHLIGHT


class SaveDialog:
    """Modal dialog prompting the user to save the scoreboard before quitting."""

    def __init__(self, renderer):
        self.renderer = renderer
        self.filepath = ""
        self._error = ""
        self.save_quit_btn = None
        self.quit_btn = None
        self.cancel_btn = None
        self._panel_x = 0
        self._panel_y = 0
        self._panel_w = 0

    def reset(self):
        self.filepath = ""
        self._error = ""

    def _create_buttons(self):
        w = constants.WINDOW_WIDTH
        h = constants.WINDOW_HEIGHT
        btn_h = constants.MENU_BUTTON_HEIGHT
        small_w = int(constants.MENU_BUTTON_WIDTH * 0.65)
        panel_w = int(w * 0.56)
        panel_x = w // 2 - panel_w // 2
        panel_y = int(h * 0.22)
        mid = panel_x + panel_w // 2
        btn_y = panel_y + int(h * 0.34)
        self.save_quit_btn = pygame.Rect(mid - small_w - 8, btn_y, small_w, btn_h)
        self.quit_btn = pygame.Rect(mid + 8, btn_y, small_w, btn_h)
        self.cancel_btn = pygame.Rect(mid - 60, btn_y + btn_h + 12, 120, btn_h)
        self._panel_x = panel_x
        self._panel_y = panel_y
        self._panel_w = panel_w

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Returns 'save_quit', 'quit', 'cancel', or None."""
        self._create_buttons()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.filepath = self.filepath[:-1]
                self._error = ""
            elif event.key == pygame.K_ESCAPE:
                return "cancel"
            elif len(event.unicode) == 1 and event.unicode.isprintable():
                self.filepath += event.unicode
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = pygame.mouse.get_pos()
            if self.save_quit_btn and self.save_quit_btn.collidepoint(mp):
                return "save_quit"
            if self.quit_btn and self.quit_btn.collidepoint(mp):
                return "quit"
            if self.cancel_btn and self.cancel_btn.collidepoint(mp):
                return "cancel"
        return None

    def draw(self, current_time: int):
        """Draw the save dialog as an overlay."""
        self._create_buttons()
        w = constants.WINDOW_WIDTH
        h = constants.WINDOW_HEIGHT

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.renderer.screen.blit(overlay, (0, 0))

        panel_h = int(h * 0.54)
        panel_surf = pygame.Surface((self._panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((238, 238, 243, 250))
        self.renderer.screen.blit(panel_surf, (self._panel_x, self._panel_y))
        pygame.draw.rect(
            self.renderer.screen, (160, 160, 190),
            (self._panel_x, self._panel_y, self._panel_w, panel_h),
            2, border_radius=10
        )

        cx = self._panel_x + self._panel_w // 2

        # Cascade text positions using actual font heights to prevent overlap
        self.renderer._update_fonts()
        hl_h = self.renderer.font_large.get_height()
        sm_h = self.renderer.font_small.get_height()
        y = self._panel_y + 18 + hl_h // 2
        self.renderer.draw_text(
            "Save Scoreboard?", (cx, y),
            COLOR_TEXT_HIGHLIGHT, font_size="large", center=True
        )
        y += hl_h // 2 + 10 + sm_h // 2
        self.renderer.draw_text(
            "You have scores recorded this session.",
            (cx, y), COLOR_TEXT, font_size="small", center=True
        )
        y += sm_h + 8
        self.renderer.draw_text(
            "Enter file path to save (e.g. scores.json):",
            (cx, y), COLOR_TEXT, font_size="small", center=True
        )
        y += sm_h // 2 + 16

        box_w = int(self._panel_w * 0.82)
        box_h = max(38, int(h * 0.06))
        box_x = cx - box_w // 2
        box_y = y
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.renderer.screen, (245, 245, 250), box_rect, border_radius=6)
        pygame.draw.rect(self.renderer.screen, (100, 110, 160), box_rect, 2, border_radius=6)

        cursor = "|" if (current_time // 500) % 2 == 0 else " "
        text_h = self.renderer.font_small.get_height()
        self.renderer.draw_text(
            self.filepath + cursor,
            (box_x + 10, box_y + (box_h - text_h) // 2),
            (30, 30, 50), font_size="small"
        )

        if self._error:
            self.renderer.draw_text(
                self._error, (cx, self._panel_y + int(h * 0.30)),
                (180, 60, 60), font_size="small", center=True
            )

        mp = pygame.mouse.get_pos()
        self.renderer.draw_button(
            self.save_quit_btn, "Save & Quit",
            self.save_quit_btn.collidepoint(mp),
            color=(60, 120, 80), hover_color=(80, 150, 100)
        )
        self.renderer.draw_button(
            self.quit_btn, "Quit",
            self.quit_btn.collidepoint(mp),
            color=(140, 60, 60), hover_color=(170, 80, 80)
        )
        self.renderer.draw_button(
            self.cancel_btn, "Cancel",
            self.cancel_btn.collidepoint(mp)
        )


class LoadDialog:
    """Modal dialog for loading a scoreboard from a JSON file."""

    def __init__(self, renderer):
        self.renderer = renderer
        self.filepath = ""
        self._error = ""
        self._success = ""
        self.load_btn = None
        self.cancel_btn = None
        self._panel_x = 0
        self._panel_y = 0
        self._panel_w = 0

    def reset(self):
        self.filepath = ""
        self._error = ""
        self._success = ""

    def set_error(self, msg: str):
        self._error = msg
        self._success = ""

    def set_success(self, msg: str):
        self._success = msg
        self._error = ""

    def _create_buttons(self):
        w = constants.WINDOW_WIDTH
        h = constants.WINDOW_HEIGHT
        btn_h = constants.MENU_BUTTON_HEIGHT
        small_w = int(constants.MENU_BUTTON_WIDTH * 0.65)
        panel_w = int(w * 0.56)
        panel_x = w // 2 - panel_w // 2
        panel_y = int(h * 0.28)
        mid = panel_x + panel_w // 2
        btn_y = panel_y + int(h * 0.28)
        self.load_btn = pygame.Rect(mid - small_w - 8, btn_y, small_w, btn_h)
        self.cancel_btn = pygame.Rect(mid + 8, btn_y, small_w, btn_h)
        self._panel_x = panel_x
        self._panel_y = panel_y
        self._panel_w = panel_w

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Returns 'load', 'cancel', or None."""
        self._create_buttons()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.filepath = self.filepath[:-1]
                self._error = ""
                self._success = ""
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return "load"
            elif event.key == pygame.K_ESCAPE:
                return "cancel"
            elif len(event.unicode) == 1 and event.unicode.isprintable():
                self.filepath += event.unicode
                self._error = ""
                self._success = ""
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = pygame.mouse.get_pos()
            if self.load_btn and self.load_btn.collidepoint(mp):
                return "load"
            if self.cancel_btn and self.cancel_btn.collidepoint(mp):
                return "cancel"
        return None

    def draw(self, current_time: int):
        """Draw the load dialog as an overlay."""
        self._create_buttons()
        w = constants.WINDOW_WIDTH
        h = constants.WINDOW_HEIGHT

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.renderer.screen.blit(overlay, (0, 0))

        panel_h = int(h * 0.44)
        panel_surf = pygame.Surface((self._panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((238, 238, 243, 250))
        self.renderer.screen.blit(panel_surf, (self._panel_x, self._panel_y))
        pygame.draw.rect(
            self.renderer.screen, (160, 160, 190),
            (self._panel_x, self._panel_y, self._panel_w, panel_h),
            2, border_radius=10
        )

        cx = self._panel_x + self._panel_w // 2

        self.renderer._update_fonts()
        hl_h = self.renderer.font_large.get_height()
        sm_h = self.renderer.font_small.get_height()
        y = self._panel_y + 18 + hl_h // 2
        self.renderer.draw_text(
            "Load Scoreboard", (cx, y),
            COLOR_TEXT_HIGHLIGHT, font_size="large", center=True
        )
        y += hl_h // 2 + 10 + sm_h // 2
        self.renderer.draw_text(
            "Enter path to a saved scoreboard JSON file:",
            (cx, y), COLOR_TEXT, font_size="small", center=True
        )
        y += sm_h // 2 + 16

        box_w = int(self._panel_w * 0.82)
        box_h = max(38, int(h * 0.06))
        box_x = cx - box_w // 2
        box_y = y
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        pygame.draw.rect(self.renderer.screen, (245, 245, 250), box_rect, border_radius=6)
        pygame.draw.rect(self.renderer.screen, (100, 110, 160), box_rect, 2, border_radius=6)

        cursor = "|" if (current_time // 500) % 2 == 0 else " "
        text_h = self.renderer.font_small.get_height()
        self.renderer.draw_text(
            self.filepath + cursor,
            (box_x + 10, box_y + (box_h - text_h) // 2),
            (30, 30, 50), font_size="small"
        )

        if self._error:
            self.renderer.draw_text(
                self._error, (cx, self._panel_y + int(h * 0.26)),
                (180, 60, 60), font_size="small", center=True
            )
        if self._success:
            self.renderer.draw_text(
                self._success, (cx, self._panel_y + int(h * 0.26)),
                (60, 140, 60), font_size="small", center=True
            )

        mp = pygame.mouse.get_pos()
        self.renderer.draw_button(
            self.load_btn, "Load",
            self.load_btn.collidepoint(mp),
            color=(60, 120, 80), hover_color=(80, 150, 100)
        )
        self.renderer.draw_button(
            self.cancel_btn, "Cancel",
            self.cancel_btn.collidepoint(mp)
        )
