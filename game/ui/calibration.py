"""Pre-game calibration: 8 known-location emissions with visible photons and TOF."""

import pygame
import math
from typing import Tuple, List, Optional

import game.constants as constants
from game.constants import COLOR_TEXT, COLOR_TEXT_HIGHLIGHT, COLOR_LOR_LINE

# 8 calibration positions as (row_frac, col_frac, label).
# Fractions of (grid_size - 1), so they scale with any difficulty.
CALIBRATION_POSITIONS = [
    (0.10, 0.10, "Top-Left Corner"),
    (0.10, 0.90, "Top-Right Corner"),
    (0.90, 0.10, "Bottom-Left Corner"),
    (0.90, 0.90, "Bottom-Right Corner"),
    (0.50, 0.50, "Center"),
    (0.20, 0.50, "Upper Edge"),
    (0.50, 0.15, "Left Edge"),
    (0.70, 0.75, "Lower-Right Region"),
]

# All 8 emissions use the same LOR direction so the student can compare how
# POSITION (not angle) changes which detector fires first.
_ANGLE = math.radians(30)   # ~lower-right / upper-left LOR direction

# Animation timing
_INTRO_MS  = 700    # ms to show source marker before photons depart
_PHOTON_MS = 1600   # ms for the longer-path photon to travel the full distance
_LOR_MS    = 2400   # ms to hold the LOR + TOF message before auto-advancing


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ray_intersect(src: Tuple, ctr: Tuple, r: float, angle: float) -> Tuple:
    """Intersection of ray from src in direction angle with circle (ctr, r)."""
    dx, dy = src[0] - ctr[0], src[1] - ctr[1]
    ux, uy = math.cos(angle), math.sin(angle)
    b = 2.0 * (dx * ux + dy * uy)
    c = dx * dx + dy * dy - r * r
    t = (-b + math.sqrt(max(0.0, b * b - 4.0 * c))) / 2.0
    return (src[0] + t * ux, src[1] + t * uy)


def _dir_label(angle_rad: float) -> str:
    """Compass direction for a screen-space angle (y increases downward)."""
    d = math.degrees(angle_rad) % 360
    if d < 22.5 or d >= 337.5:  return "right"
    if d < 67.5:                 return "lower-right"
    if d < 112.5:                return "bottom"
    if d < 157.5:                return "lower-left"
    if d < 202.5:                return "left"
    if d < 247.5:                return "upper-left"
    if d < 292.5:                return "top"
    return "upper-right"


# ---------------------------------------------------------------------------
# Single emission animation
# ---------------------------------------------------------------------------

class _Emission:
    INTRO, PHOTONS, LOR, DONE = 0, 1, 2, 3

    def __init__(self, src: Tuple, center: Tuple, ring_r: float, label: str):
        self.src    = src
        self.center = center
        self.label  = label

        # Hit positions via ray-circle intersection from source
        self.d1 = _ray_intersect(src, center, ring_r, _ANGLE)
        self.d2 = _ray_intersect(src, center, ring_r, _ANGLE + math.pi)

        self.dist1    = math.dist(src, self.d1)
        self.dist2    = math.dist(src, self.d2)
        self.max_dist = max(self.dist1, self.dist2)

        # Arrival times in animation-ms
        self.arr1 = _PHOTON_MS * self.dist1 / self.max_dist
        self.arr2 = _PHOTON_MS * self.dist2 / self.max_dist
        self.tof_diff_ms = int(abs(self.arr2 - self.arr1))
        self.d1_first    = self.dist1 <= self.dist2

        # State
        self.ph1: Tuple = src
        self.ph2: Tuple = src
        self.hit1 = False
        self.hit2 = False
        self.hit1_time = 0
        self.hit2_time = 0
        self.phase   = self.INTRO
        self._t0     = 0
        self.started = False

    # ------------------------------------------------------------------

    def start(self, now: int) -> None:
        self._t0     = now
        self.phase   = self.INTRO
        self.started = True
        self.ph1     = self.src
        self.ph2     = self.src
        self.hit1    = False
        self.hit2    = False

    def update(self, now: int, ring) -> None:
        if not self.started:
            return
        e = now - self._t0

        if self.phase == self.INTRO:
            if e >= _INTRO_MS:
                self.phase = self.PHOTONS
                self._t0   = now
            return

        if self.phase == self.PHOTONS:
            e2 = now - self._t0
            t1 = min(1.0, e2 / self.arr1)
            t2 = min(1.0, e2 / self.arr2)
            self.ph1 = (self.src[0] + (self.d1[0] - self.src[0]) * t1,
                        self.src[1] + (self.d1[1] - self.src[1]) * t1)
            self.ph2 = (self.src[0] + (self.d2[0] - self.src[0]) * t2,
                        self.src[1] + (self.d2[1] - self.src[1]) * t2)

            if t1 >= 1.0 and not self.hit1:
                self.hit1 = True
                self.hit1_time = now
                idx = ring.find_closest_detector(self.d1)
                ring.detectors[idx].trigger_hit(now)

            if t2 >= 1.0 and not self.hit2:
                self.hit2 = True
                self.hit2_time = now
                idx = ring.find_closest_detector(self.d2)
                ring.detectors[idx].trigger_hit(now)

            if self.hit1 and self.hit2 and e2 >= _PHOTON_MS + 300:
                self.phase = self.LOR
                self._t0   = now
            return

        if self.phase == self.LOR:
            if now - self._t0 >= _LOR_MS:
                self.phase = self.DONE

    def done(self) -> bool:
        return self.phase == self.DONE

    def tof_message(self) -> str:
        if self.tof_diff_ms < 25:
            return ("Both detectors lit up at the same time  "
                    "\u2192  emission was near the center of the LOR")
        first_det = self.d1 if self.d1_first else self.d2
        angle = math.atan2(first_det[1] - self.center[1],
                           first_det[0] - self.center[0])
        side = _dir_label(angle)
        return (f"{side.title()} detector lit up {self.tof_diff_ms} ms sooner  "
                f"\u2192  emission was closer to the {side}")


# ---------------------------------------------------------------------------
# Calibration phase (manages the sequence of 8 emissions)
# ---------------------------------------------------------------------------

class CalibrationPhase:
    """Shows 8 demo emissions (corners + sensible extras) before the game.

    Each emission shows:
      - The exact annihilation pixel (red/orange dot on the grid)
      - Two gamma photons traveling in opposite directions
      - Detector ring lighting up with TOF timing
      - The LOR line with a plain-English TOF explanation
    """

    def __init__(self, renderer):
        self.renderer = renderer
        self.emissions: List[_Emission] = []
        self.idx = 0
        self.image_matrix = None
        self.detector_ring = None
        self._skip_btn: Optional[pygame.Rect] = None
        self._next_btn: Optional[pygame.Rect] = None

    # ------------------------------------------------------------------

    def setup(self, image_matrix, detector_ring) -> None:
        """Call after game objects are created (start_game)."""
        self.image_matrix  = image_matrix
        self.detector_ring = detector_ring
        self.idx           = 0
        self.emissions     = []

        gs     = image_matrix.grid_size
        center = detector_ring.center
        r      = detector_ring.radius

        for rf, cf, label in CALIBRATION_POSITIONS:
            row = max(0, min(gs - 1, round(rf * (gs - 1))))
            col = max(0, min(gs - 1, round(cf * (gs - 1))))
            src = image_matrix.pixel_to_screen(row, col)
            self.emissions.append(_Emission(src, center, r, label))

    # ------------------------------------------------------------------

    def _make_buttons(self) -> None:
        w, h = constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT
        self._skip_btn = pygame.Rect(w - 130, h - 52, 115, 36)
        self._next_btn = pygame.Rect(w - 258, h - 52, 115, 36)

    def _clear_ring(self) -> None:
        for d in self.detector_ring.detectors:
            d.is_hit       = False
            d.blink_progress = 0.0
        self.detector_ring.pending_hits.clear()

    def _advance(self, now: int) -> Optional[str]:
        self._clear_ring()
        self.idx += 1
        if self.idx >= len(self.emissions):
            return "done"
        self.emissions[self.idx].start(now)
        return None

    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event, now: int) -> Optional[str]:
        self._make_buttons()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mp = pygame.mouse.get_pos()
            if self._skip_btn and self._skip_btn.collidepoint(mp):
                self._clear_ring()
                return "done"
            if self._next_btn and self._next_btn.collidepoint(mp):
                return self._advance(now)
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
            return self._advance(now)
        return None

    def update(self, now: int) -> Optional[str]:
        if not self.emissions or self.idx >= len(self.emissions):
            return "done"

        em = self.emissions[self.idx]
        if not em.started:
            em.start(now)

        em.update(now, self.detector_ring)
        self.detector_ring.update(now)

        if em.done():
            return self._advance(now)
        return None

    # ------------------------------------------------------------------

    def draw(self, now: int) -> None:
        screen      = self.renderer.screen
        w, h        = constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT
        hud_h       = constants.HUD_HEIGHT

        self.renderer.clear()
        self.renderer.draw_game_background()
        self.image_matrix.draw(screen)
        self.detector_ring.draw(screen)

        if self.idx >= len(self.emissions):
            return
        em = self.emissions[self.idx]
        if not em.started:
            return

        src = (int(em.src[0]), int(em.src[1]))

        # ── Pulsing source marker ──────────────────────────────────────
        pulse  = 0.5 + 0.5 * math.sin(now * 0.006)
        glow_r = int(14 + 4 * pulse)
        glow_s = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (220, 80, 40, 90), (glow_r, glow_r), glow_r)
        screen.blit(glow_s, (src[0] - glow_r, src[1] - glow_r))
        pygame.draw.circle(screen, (210, 55, 25), src, 7)
        pygame.draw.circle(screen, (255, 120, 80), src, 4)
        pygame.draw.circle(screen, (255, 230, 210), src, 2)

        # ── Photons ────────────────────────────────────────────────────
        if em.phase == _Emission.PHOTONS:
            for ph, hit in ((em.ph1, em.hit1), (em.ph2, em.hit2)):
                if not hit:
                    px, py = int(ph[0]), int(ph[1])
                    glow = pygame.Surface((22, 22), pygame.SRCALPHA)
                    pygame.draw.circle(glow, (100, 200, 255, 90), (11, 11), 11)
                    screen.blit(glow, (px - 11, py - 11))
                    pygame.draw.circle(screen, (160, 225, 255), (px, py), 6)
                    pygame.draw.circle(screen, (255, 255, 255), (px, py), 3)

        # ── LOR line ──────────────────────────────────────────────────
        if em.phase >= _Emission.LOR:
            lor_s = pygame.Surface((w, h), pygame.SRCALPHA)
            d1i = (int(em.d1[0]), int(em.d1[1]))
            d2i = (int(em.d2[0]), int(em.d2[1]))
            pygame.draw.line(lor_s, (*COLOR_LOR_LINE[:3], 210), d1i, d2i, 3)
            screen.blit(lor_s, (0, 0))
            # Redraw source on top of the LOR line
            pygame.draw.circle(screen, (210, 55, 25), src, 7)
            pygame.draw.circle(screen, (255, 120, 80), src, 4)

        # ── HUD bar ────────────────────────────────────────────────────
        pygame.draw.rect(screen, (235, 235, 240), (0, 0, w, hud_h))
        pygame.draw.line(screen, (200, 200, 210), (0, hud_h), (w, hud_h), 2)
        self.renderer.draw_text(
            f"Calibration  {self.idx + 1} / {len(self.emissions)}  \u2014  {em.label}",
            (w // 2, hud_h // 2),
            COLOR_TEXT_HIGHLIGHT, font_size="medium", center=True,
        )

        # ── Bottom instruction bar ────────────────────────────────────
        bar_h = 58
        pygame.draw.rect(screen, (235, 235, 240), (0, h - bar_h, w, bar_h))
        pygame.draw.line(screen, (200, 200, 210), (0, h - bar_h), (w, h - bar_h), 2)

        if em.phase == _Emission.INTRO:
            msg   = (f"Annihilation at {em.label}  \u2014  "
                     "watch the two detectors: which one lights up first?")
            color = COLOR_TEXT
        elif em.phase == _Emission.PHOTONS:
            msg   = ("Two gamma photons emitted in exactly opposite directions  \u2014  "
                     "the closer detector will light up first!")
            color = COLOR_TEXT
        else:
            msg   = em.tof_message()
            color = (145, 95, 0) if em.tof_diff_ms >= 25 else (20, 135, 65)

        self.renderer.draw_text(msg, (16, h - bar_h + 11), color, font_size="small")

        # ── Navigation buttons ────────────────────────────────────────
        self._make_buttons()
        mp = pygame.mouse.get_pos()
        self.renderer.draw_button(
            self._next_btn, "Next  \u2192", self._next_btn.collidepoint(mp))
        self.renderer.draw_button(
            self._skip_btn, "Skip All", self._skip_btn.collidepoint(mp),
            color=(140, 75, 55), hover_color=(170, 95, 70))
