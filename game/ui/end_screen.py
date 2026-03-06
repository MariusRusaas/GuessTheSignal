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
        self._scoreboard_scores = []  # list of {name, dice}
        self._player_name = ""
        self._player_dice = -1.0

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

    def set_scoreboard(self, scores: list, player_name: str = "", player_dice: float = -1.0):
        """Set the scoreboard entries to display (list of {name, dice}).

        player_name / player_dice identify the current player's entry so it
        can be highlighted in green.
        """
        self._scoreboard_scores = scores
        self._player_name = player_name
        self._player_dice = player_dice

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
            return "Excellent!", (20, 140, 20)
        elif self.dice_score >= 0.75:
            return "Great!", (60, 140, 20)
        elif self.dice_score >= 0.6:
            return "Good", (140, 120, 0)
        elif self.dice_score >= 0.4:
            return "Fair", (160, 90, 0)
        else:
            return "Keep Practicing", (160, 50, 20)

    def _truncate_name(self, name: str, max_width: int, font) -> str:
        """Truncate name to fit max_width pixels, appending '...' if cut."""
        if font.size(name)[0] <= max_width:
            return name
        suffix = "..."
        suffix_w = font.size(suffix)[0]
        for i in range(len(name), 0, -1):
            if font.size(name[:i])[0] + suffix_w <= max_width:
                return name[:i] + suffix
        return suffix

    # Rank colour palette (readable on light background)
    _RANK_COLORS = {
        1: (175, 135, 0),    # gold
        2: (105, 110, 130),  # silver
        3: (155, 95, 35),    # bronze
    }
    _PLAYER_COLOR  = (20, 120, 50)   # dark green — current player
    _ELLIPSIS_COLOR = (150, 150, 170)

    def _find_player_index(self) -> int:
        """Return 0-based index of the current player in _scoreboard_scores, or -1."""
        for i, e in enumerate(self._scoreboard_scores):
            if e["name"] == self._player_name and abs(e["dice"] - self._player_dice) < 1e-9:
                return i
        return -1

    def _build_display_indices(self, player_idx: int) -> list:
        """Return list of integer indices (or None for '…') to render."""
        n = len(self._scoreboard_scores)
        if n == 0:
            return []

        if player_idx < 0 or player_idx < 8:
            # Player is in top 8 (or unknown) — show all top 8
            return list(range(min(8, n)))

        # Player is outside top 10: top 3 + "…" + player ±1
        top = list(range(min(3, n)))
        start = max(player_idx - 1, 0)
        end   = min(player_idx + 1, n - 1)
        near  = [i for i in range(start, end + 1) if i not in top]
        return top + ([None] + near if near else [])

    def _draw_scoreboard_table(self, panel_x: int, panel_width: int, top_y: int):
        """Draw the scoreboard as a column-aligned table."""
        self.renderer._update_fonts()
        font = self.renderer.font_small
        screen = self.renderer.screen

        margin = 15
        row_h = font.get_height() + 8

        # Column layout
        rank_w = 26
        score_col_w = 72
        inner_gap = 8
        name_col_w = panel_width - 2 * margin - rank_w - score_col_w - inner_gap * 2

        x_rank  = panel_x + margin + rank_w // 2        # centre of rank col
        x_name  = panel_x + margin + rank_w + inner_gap  # left of name col
        x_score = panel_x + panel_width - margin          # right edge of score col

        # Section title
        title_surf = font.render("Top Scores", True, COLOR_TEXT_HIGHLIGHT)
        screen.blit(title_surf, (panel_x + panel_width // 2 - title_surf.get_width() // 2, top_y))
        top_y += title_surf.get_height() + 5

        # Column headers
        hdr_color = (120, 120, 140)
        for text, x, align in [
            ("#",     x_rank,  "center"),
            ("Name",  x_name,  "left"),
            ("Score", x_score, "right"),
        ]:
            s = font.render(text, True, hdr_color)
            if align == "center":
                screen.blit(s, (x - s.get_width() // 2, top_y))
            elif align == "left":
                screen.blit(s, (x, top_y))
            else:
                screen.blit(s, (x - s.get_width(), top_y))
        top_y += font.get_height() + 2

        # Thin divider under headers
        pygame.draw.line(screen, (190, 190, 210),
                         (panel_x + margin, top_y),
                         (panel_x + panel_width - margin, top_y), 1)
        top_y += 5

        player_idx  = self._find_player_index()
        display_idx = self._build_display_indices(player_idx)

        for slot, idx in enumerate(display_idx):
            row_y = top_y + slot * row_h

            if idx is None:
                # Ellipsis separator row
                s = font.render("· · ·", True, self._ELLIPSIS_COLOR)
                screen.blit(s, (x_name, row_y))
                continue

            entry  = self._scoreboard_scores[idx]
            rank   = idx + 1  # 1-based

            if idx == player_idx:
                color = self._PLAYER_COLOR
            elif rank in self._RANK_COLORS:
                color = self._RANK_COLORS[rank]
            else:
                color = COLOR_TEXT

            rank_s = font.render(f"{rank}.", True, color)
            screen.blit(rank_s, (x_rank - rank_s.get_width() // 2, row_y))

            truncated = self._truncate_name(entry["name"], name_col_w, font)
            name_s = font.render(truncated, True, color)
            screen.blit(name_s, (x_name, row_y))

            score_str = f"{entry['dice'] * 100:.2f}%"
            score_s = font.render(score_str, True, color)
            screen.blit(score_s, (x_score - score_s.get_width(), row_y))

    def draw(self):
        """Draw the end screen as an overlay panel on the right side."""
        w = constants.WINDOW_WIDTH
        h = constants.WINDOW_HEIGHT

        panel_width = int(w * 0.32)
        panel_x = w - panel_width - 20
        panel_y = int(h * 0.11)
        panel_height = h - int(h * 0.22)

        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill((238, 238, 243, 245))
        self.renderer.screen.blit(panel_surface, (panel_x, panel_y))

        pygame.draw.rect(
            self.renderer.screen,
            (180, 180, 200),
            (panel_x, panel_y, panel_width, panel_height),
            2,
            border_radius=8
        )

        text_center_x = panel_x + panel_width // 2

        # Title
        self.renderer.draw_text(
            "Results",
            (text_center_x, panel_y + 28),
            COLOR_TEXT_HIGHLIGHT,
            font_size="large",
            center=True
        )

        # DICE Score
        score_pct = self.dice_score * 100
        grade, grade_color = self._get_score_grade()

        self.renderer.draw_text(
            f"DICE Score: {score_pct:.1f}%",
            (text_center_x, panel_y + 82),
            grade_color,
            font_size="large",
            center=True
        )

        self.renderer.draw_text(
            grade,
            (text_center_x, panel_y + 120),
            grade_color,
            font_size="medium",
            center=True
        )

        # Separator
        sep1_y = panel_y + 145
        pygame.draw.line(self.renderer.screen, (190, 190, 210),
                         (panel_x + 15, sep1_y), (panel_x + panel_width - 15, sep1_y), 1)

        # Legend
        legend_y = sep1_y + 14
        self.renderer.draw_text(
            "Legend:",
            (text_center_x, legend_y),
            COLOR_TEXT_HIGHLIGHT,
            font_size="small",
            center=True
        )

        legend_items = [
            ("Green = Correct",    (100, 200, 100)),
            ("Red = Wrong guess",  (200, 100, 100)),
            ("Blue = Missed",      (100, 100, 200)),
        ]
        for i, (text, color) in enumerate(legend_items):
            self.renderer.draw_text(
                text,
                (text_center_x, legend_y + 22 + i * 22),
                color,
                font_size="small",
                center=True
            )

        # Separator
        sep2_y = legend_y + 22 + len(legend_items) * 22 + 10
        pygame.draw.line(self.renderer.screen, (190, 190, 210),
                         (panel_x + 15, sep2_y), (panel_x + panel_width - 15, sep2_y), 1)

        # Scoreboard table
        if self._scoreboard_scores:
            self._draw_scoreboard_table(panel_x, panel_width, sep2_y + 14)

        # Buttons at bottom of panel
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
