"""Pre-game calibration: demo annihilation, explanation modal, then 10 interactive rounds.

State flow:
  _DEMO_PLAY  — full animated annihilation (source visible, photons, LOR, detectors)
  _DEMO_INFO  — frozen LOR + modal panel with explanation + Start / Skip buttons
  _INTRO      — brief "get ready" pause before the first calibration blink
  _FIRING     — emission fired, only detector blinks visible (no source, no LOR)
  _WAITING    — blink settled, waiting for player to click their guess
  _REVEALED   — true position + guess shown with feedback
"""

import math
import pygame
from typing import Tuple, List, Optional

import game.constants as constants
from game.constants import COLOR_TEXT, COLOR_TEXT_HIGHLIGHT, COLOR_LOR_LINE

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_NUM_EMISSIONS   = 10
_GOLDEN_ANGLE    = math.pi * (3 - math.sqrt(5))   # ≈ 137.5° sunflower spiral

# Demo animation timings
_DEMO_INTRO_MS  = 900    # ms to show source before photons depart
_DEMO_PHOTON_MS = 1600   # ms for the longer-path photon to complete travel
_DEMO_LOR_MS    = 1800   # ms to hold the LOR before showing the info modal
_DEMO_ANGLE     = math.radians(30)
_DEMO_ROW_FRAC  = 0.30   # demo source: clearly off-centre so TOF is obvious
_DEMO_COL_FRAC  = 0.35

# Calibration round timings
_INTRO_MS        = 2500   # "get ready" pause before first blink
_BLINK_SETTLE_MS = 1800   # wait after firing before asking for a guess
_REVEAL_MS       = 3000   # auto-advance after this long on the reveal screen


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ray_intersect(src: Tuple, ctr: Tuple, r: float, angle: float) -> Tuple:
    """Intersection of a ray from src in direction angle with circle (ctr, r)."""
    dx, dy = src[0] - ctr[0], src[1] - ctr[1]
    ux, uy = math.cos(angle), math.sin(angle)
    b = 2.0 * (dx * ux + dy * uy)
    c = dx * dx + dy * dy - r * r
    t = (-b + math.sqrt(max(0.0, b * b - 4.0 * c))) / 2.0
    return (src[0] + t * ux, src[1] + t * uy)


def _closest_det(ring, pos: Tuple) -> int:
    """Index of the detector whose arc-centre is nearest to pos."""
    angle = math.atan2(pos[1] - ring.center[1], pos[0] - ring.center[0])
    n = len(ring.detectors)
    return round((angle % (2 * math.pi)) / (2 * math.pi) * n) % n


def _spiral_fracs(n: int) -> List[Tuple[float, float]]:
    """Return n (row_frac, col_frac) values spiraling from centre outward."""
    out = []
    for i in range(n):
        r     = (i / max(1, n - 1)) * 0.80
        theta = i * _GOLDEN_ANGLE
        rf    = max(0.06, min(0.94, 0.5 + r * math.sin(theta)))
        cf    = max(0.06, min(0.94, 0.5 + r * math.cos(theta)))
        out.append((rf, cf))
    return out


# ---------------------------------------------------------------------------
# Demo animation
# ---------------------------------------------------------------------------

class _DemoAnim:
    """Single full-visibility annihilation animation (source → photons → LOR)."""

    INTRO, PHOTONS, LOR, DONE = 0, 1, 2, 3

    def __init__(self, src: Tuple, center: Tuple, ring_r: float):
        self.src    = src
        self.center = center
        self.d1 = _ray_intersect(src, center, ring_r, _DEMO_ANGLE)
        self.d2 = _ray_intersect(src, center, ring_r, _DEMO_ANGLE + math.pi)
        dist1 = math.dist(src, self.d1)
        dist2 = math.dist(src, self.d2)
        max_d = max(dist1, dist2)
        # Arrival times relative to photons-phase start (ms)
        self.arr1 = _DEMO_PHOTON_MS * dist1 / max_d
        self.arr2 = _DEMO_PHOTON_MS * dist2 / max_d
        # Live state
        self.phase          = self.INTRO
        self._t0            = 0
        self._photons_start = 0
        self.ph1_pos        = src
        self.ph2_pos        = src
        self.hit1           = False
        self.hit2           = False

    def start(self, now: int, ring) -> None:
        self._t0            = now
        self.phase          = self.INTRO
        self.ph1_pos        = self.src
        self.ph2_pos        = self.src
        self.hit1           = False
        self.hit2           = False
        # Pre-schedule detector blinks to coincide with visual photon arrivals
        photons_at = now + _DEMO_INTRO_MS
        ring.schedule_hit(_closest_det(ring, self.d1), int(self.arr1), photons_at)
        ring.schedule_hit(_closest_det(ring, self.d2), int(self.arr2), photons_at)

    def update(self, now: int) -> None:
        e = now - self._t0

        if self.phase == self.INTRO:
            if e >= _DEMO_INTRO_MS:
                self.phase          = self.PHOTONS
                self._photons_start = now
            return

        if self.phase == self.PHOTONS:
            t  = now - self._photons_start
            t1 = min(1.0, t / self.arr1)
            t2 = min(1.0, t / self.arr2)
            self.ph1_pos = (self.src[0] + (self.d1[0] - self.src[0]) * t1,
                            self.src[1] + (self.d1[1] - self.src[1]) * t1)
            self.ph2_pos = (self.src[0] + (self.d2[0] - self.src[0]) * t2,
                            self.src[1] + (self.d2[1] - self.src[1]) * t2)
            if t1 >= 1.0: self.hit1 = True
            if t2 >= 1.0: self.hit2 = True
            if self.hit1 and self.hit2 and t >= _DEMO_PHOTON_MS + 300:
                self.phase = self.LOR
                self._t0   = now
            return

        if self.phase == self.LOR:
            if now - self._t0 >= _DEMO_LOR_MS:
                self.phase = self.DONE


# ---------------------------------------------------------------------------
# CalibrationPhase
# ---------------------------------------------------------------------------

class CalibrationPhase:
    """Full calibration sequence: demo → info modal → 10 interactive rounds."""

    _DEMO_PLAY = -3
    _DEMO_INFO = -2
    _INTRO     = -1
    _FIRING    =  0
    _WAITING   =  1
    _REVEALED  =  2

    def __init__(self, renderer):
        self.renderer      = renderer
        self.image_matrix  = None
        self.detector_ring = None
        self.physics       = None

        self._demo: Optional[_DemoAnim] = None
        self._screen_pos: List[Tuple[float, float]] = []
        self._idx          = 0
        self._started      = False
        self._state        = self._DEMO_PLAY
        self._intro_time   = 0
        self._fire_time    = 0
        self._guess_screen: Optional[Tuple[float, float]] = None
        self._reveal_time  = 0

        # Button rects — computed fresh in handle_event and draw
        self._start_cal_btn: Optional[pygame.Rect] = None
        self._skip_game_btn: Optional[pygame.Rect] = None
        self._jump_btn:      Optional[pygame.Rect] = None

    # ------------------------------------------------------------------

    def setup(self, image_matrix, detector_ring, physics) -> None:
        """Initialise with live game objects. Call once per game start."""
        self.image_matrix  = image_matrix
        self.detector_ring = detector_ring
        self.physics       = physics

        self._idx          = 0
        self._started      = False
        self._state        = self._DEMO_PLAY
        self._guess_screen = None
        self._screen_pos   = []

        gs = image_matrix.grid_size
        for rf, cf in _spiral_fracs(_NUM_EMISSIONS):
            row = max(0, min(gs - 1, round(rf * (gs - 1))))
            col = max(0, min(gs - 1, round(cf * (gs - 1))))
            self._screen_pos.append(image_matrix.pixel_to_screen(row, col))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _clear_ring(self) -> None:
        for d in self.detector_ring.detectors:
            d.is_hit         = False
            d.blink_progress = 0.0
        self.detector_ring.pending_hits.clear()

    def _fire(self, now: int) -> None:
        self._clear_ring()
        src      = self._screen_pos[self._idx]
        emission = self.physics.emit_from_pixel(src)
        det1, det2, dist1, dist2 = self.physics.find_detector_hits(
            emission, self.detector_ring)
        max_dist       = self.detector_ring.radius * 2
        delay1, delay2 = self.physics.calculate_tof_delays(dist1, dist2, max_dist)
        self.detector_ring.schedule_hit(det1, delay1, now)
        self.detector_ring.schedule_hit(det2, delay2, now)
        self._fire_time = now
        self._state     = self._FIRING

    def _advance(self, now: int) -> Optional[str]:
        self._guess_screen = None
        self._idx += 1
        if self._idx >= _NUM_EMISSIONS:
            self._clear_ring()
            return "done"
        self._fire(now)
        return None

    def _compute_modal_rects(self) -> pygame.Rect:
        """Compute the info-modal panel rect and set the two button rects."""
        w, h  = constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT
        pw    = int(w * 0.64)
        ph    = int(h * 0.58)
        px    = (w - pw) // 2
        py    = (h - ph) // 2
        btn_w = int(pw * 0.37)
        btn_h = int(h  * 0.058)
        gap   = int(pw * 0.06)
        by    = py + ph - btn_h - int(h * 0.04)
        cx    = px + pw // 2
        self._start_cal_btn = pygame.Rect(cx + gap // 2,           by, btn_w, btn_h)
        self._skip_game_btn = pygame.Rect(cx - gap // 2 - btn_w,   by, btn_w, btn_h)
        return pygame.Rect(px, py, pw, ph)

    def _compute_jump_btn(self) -> None:
        w, h = constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT
        self._jump_btn = pygame.Rect(w - 180, h - 52, 165, 36)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event, now: int) -> Optional[str]:
        # Always recompute button rects so clicks work before the first draw
        self._compute_modal_rects()
        self._compute_jump_btn()

        # Keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                if self._state == self._DEMO_INFO:
                    self._clear_ring()
                    self._intro_time = now
                    self._state      = self._INTRO
                elif self._state == self._REVEALED:
                    return self._advance(now)
            return None

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        mp = pygame.mouse.get_pos()

        # Jump to Game — visible during all calibration rounds
        if self._state >= self._INTRO:
            if self._jump_btn and self._jump_btn.collidepoint(mp):
                self._clear_ring()
                return "done"

        if self._state == self._DEMO_INFO:
            if self._start_cal_btn and self._start_cal_btn.collidepoint(mp):
                self._clear_ring()
                self._intro_time = now
                self._state      = self._INTRO
            elif self._skip_game_btn and self._skip_game_btn.collidepoint(mp):
                self._clear_ring()
                return "done"

        elif self._state == self._WAITING:
            pixel = self.image_matrix.screen_to_pixel(mp[0], mp[1])
            if pixel:
                row, col           = pixel
                self._guess_screen = self.image_matrix.pixel_to_screen(row, col)
                self._reveal_time  = now
                self._state        = self._REVEALED

        elif self._state == self._REVEALED:
            return self._advance(now)

        return None

    def update(self, now: int) -> Optional[str]:
        if not self._screen_pos:
            return "done"

        # Lazy start: kick off demo animation on the first update tick
        if not self._started:
            gs  = self.image_matrix.grid_size
            row = max(0, min(gs - 1, round(_DEMO_ROW_FRAC * (gs - 1))))
            col = max(0, min(gs - 1, round(_DEMO_COL_FRAC * (gs - 1))))
            src = self.image_matrix.pixel_to_screen(row, col)
            self._clear_ring()
            self._demo = _DemoAnim(src, self.detector_ring.center,
                                   self.detector_ring.radius)
            self._demo.start(now, self.detector_ring)
            self._started = True

        self.detector_ring.update(now)

        if self._state == self._DEMO_PLAY:
            self._demo.update(now)
            if self._demo.phase == _DemoAnim.DONE:
                self._state = self._DEMO_INFO

        elif self._state == self._INTRO:
            if now - self._intro_time >= _INTRO_MS:
                self._fire(now)

        elif self._state == self._FIRING:
            if now - self._fire_time >= _BLINK_SETTLE_MS:
                self._state = self._WAITING

        elif self._state == self._REVEALED:
            if now - self._reveal_time >= _REVEAL_MS:
                return self._advance(now)

        return None

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, now: int) -> None:
        screen = self.renderer.screen
        w, h   = constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT
        hud_h  = constants.HUD_HEIGHT

        self.renderer.clear()
        self.renderer.draw_game_background()
        self.image_matrix.draw(screen)
        self.detector_ring.draw(screen)

        mp = pygame.mouse.get_pos()

        # ── Demo overlay (source, photons, LOR) ───────────────────────
        if self._state in (self._DEMO_PLAY, self._DEMO_INFO) and self._demo:
            dm  = self._demo
            src = (int(dm.src[0]), int(dm.src[1]))

            # Pulsing source marker
            pulse  = 0.5 + 0.5 * math.sin(now * 0.006)
            glow_r = int(14 + 4 * pulse)
            gs_sf  = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(gs_sf, (220, 80, 40, 90), (glow_r, glow_r), glow_r)
            screen.blit(gs_sf, (src[0] - glow_r, src[1] - glow_r))
            pygame.draw.circle(screen, (210, 55, 25), src, 7)
            pygame.draw.circle(screen, (255, 120, 80), src, 4)
            pygame.draw.circle(screen, (255, 230, 210), src, 2)

            # Photons (only while travelling, only in _DEMO_PLAY)
            if self._state == self._DEMO_PLAY and dm.phase == _DemoAnim.PHOTONS:
                for ph, hit in ((dm.ph1_pos, dm.hit1), (dm.ph2_pos, dm.hit2)):
                    if not hit:
                        px2, py2 = int(ph[0]), int(ph[1])
                        glow = pygame.Surface((22, 22), pygame.SRCALPHA)
                        pygame.draw.circle(glow, (100, 200, 255, 90), (11, 11), 11)
                        screen.blit(glow, (px2 - 11, py2 - 11))
                        pygame.draw.circle(screen, (160, 225, 255), (px2, py2), 6)
                        pygame.draw.circle(screen, (255, 255, 255),  (px2, py2), 3)

            # LOR line (once photons have arrived)
            if dm.phase >= _DemoAnim.LOR:
                lor_s = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.line(lor_s, (*COLOR_LOR_LINE[:3], 210),
                                 (int(dm.d1[0]), int(dm.d1[1])),
                                 (int(dm.d2[0]), int(dm.d2[1])), 3)
                screen.blit(lor_s, (0, 0))
                # Redraw source on top of the LOR
                pygame.draw.circle(screen, (210, 55, 25), src, 7)
                pygame.draw.circle(screen, (255, 120, 80), src, 4)

        # ── Info modal (shown after demo) ─────────────────────────────
        if self._state == self._DEMO_INFO:
            panel_rect = self._compute_modal_rects()
            px, py2    = panel_rect.x, panel_rect.y
            pw, ph2    = panel_rect.width, panel_rect.height

            # Dark overlay behind the modal
            ov = pygame.Surface((w, h), pygame.SRCALPHA)
            ov.fill((15, 15, 30, 155))
            screen.blit(ov, (0, 0))

            # White panel
            panel_s = pygame.Surface((pw, ph2), pygame.SRCALPHA)
            panel_s.fill((245, 245, 248, 248))
            screen.blit(panel_s, (px, py2))
            pygame.draw.rect(screen, (185, 185, 205), panel_rect, 2, border_radius=10)

            cx  = px + pw // 2
            lh  = int(ph2 * 0.075)   # line height

            # Title
            self.renderer.draw_text(
                "What you just saw",
                (cx, py2 + int(ph2 * 0.10)),
                COLOR_TEXT_HIGHLIGHT, font_size="medium", center=True)

            # First text block
            lines1 = [
                "Two gamma photons flew in opposite directions and lit up two detectors.",
                "The orange line is the Line of Response (LOR) — the true emission",
                "position is somewhere along it.",
            ]
            ty = py2 + int(ph2 * 0.20)
            for line in lines1:
                self.renderer.draw_text(line, (cx, ty), COLOR_TEXT,
                                        font_size="small", center=True)
                ty += lh

            # Divider
            div_y = ty + int(lh * 0.35)
            pygame.draw.line(screen, (200, 200, 212),
                             (px + int(pw * 0.08), div_y),
                             (px + int(pw * 0.92), div_y), 1)
            ty = div_y + int(lh * 0.55)

            # Second text block
            lines2 = [
                "In the calibration you will only see the detector blinks — no photons,",
                "no LOR. The detector closest to the source always blinks first.",
                "Use that timing to guess where each emission happened!",
            ]
            for line in lines2:
                self.renderer.draw_text(line, (cx, ty), COLOR_TEXT,
                                        font_size="small", center=True)
                ty += lh

            # Buttons
            self.renderer.draw_button(
                self._skip_game_btn, "Skip to Game",
                self._skip_game_btn.collidepoint(mp),
                color=(120, 100, 85), hover_color=(148, 125, 105))
            self.renderer.draw_button(
                self._start_cal_btn, "Start Calibration",
                self._start_cal_btn.collidepoint(mp),
                color=(55, 105, 170), hover_color=(75, 130, 210))

        # ── Calibration rounds ────────────────────────────────────────
        if self._state >= self._INTRO and self._screen_pos and self._idx < _NUM_EMISSIONS:

            # Waiting: pulse the grid blue to invite a click
            if self._state == self._WAITING:
                bx, by3, bw, bh3 = self.image_matrix.get_grid_bounds()
                pulse = 0.35 + 0.15 * math.sin(now * 0.004)
                hl_s  = pygame.Surface((int(bw), int(bh3)), pygame.SRCALPHA)
                hl_s.fill((60, 100, 220, int(pulse * 80)))
                screen.blit(hl_s, (int(bx), int(by3)))

            # Revealed: true position + player guess + feedback
            feedback, fb_color = "", (120, 120, 130)
            if self._state == self._REVEALED:
                tx = int(self._screen_pos[self._idx][0])
                ty4 = int(self._screen_pos[self._idx][1])
                pulse  = 0.5 + 0.5 * math.sin(now * 0.008)
                glow_r = int(14 + 4 * pulse)
                glow_s = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_s, (220, 80, 40, 110), (glow_r, glow_r), glow_r)
                screen.blit(glow_s, (tx - glow_r, ty4 - glow_r))
                pygame.draw.circle(screen, (210, 55, 25), (tx, ty4), 8)
                pygame.draw.circle(screen, (255, 120, 80), (tx, ty4), 4)
                pygame.draw.circle(screen, (255, 230, 210), (tx, ty4), 2)

                if self._guess_screen:
                    gx = int(self._guess_screen[0])
                    gy = int(self._guess_screen[1])
                    pygame.draw.circle(screen, (40, 100, 220), (gx, gy), 9)
                    pygame.draw.circle(screen, (130, 175, 255), (gx, gy), 5)
                    ln_s = pygame.Surface((w, h), pygame.SRCALPHA)
                    pygame.draw.line(ln_s, (100, 100, 200, 130), (tx, ty4), (gx, gy), 2)
                    screen.blit(ln_s, (0, 0))
                    dx = self._guess_screen[0] - self._screen_pos[self._idx][0]
                    dy = self._guess_screen[1] - self._screen_pos[self._idx][1]
                    cd = math.sqrt(dx * dx + dy * dy) / self.image_matrix.pixel_size
                    if cd < 1.5:   feedback, fb_color = "Spot on!",          (20, 140, 60)
                    elif cd < 3.0: feedback, fb_color = "Very close!",       (60, 160, 40)
                    elif cd < 5.0: feedback, fb_color = "Not bad",           (150, 120, 0)
                    else:          feedback, fb_color = "Keep practicing!",  (180, 70, 40)

            # HUD
            pygame.draw.rect(screen, (235, 235, 240), (0, 0, w, hud_h))
            pygame.draw.line(screen, (200, 200, 210), (0, hud_h), (w, hud_h), 2)
            self.renderer.draw_text(
                f"Calibration  \u2014  {self._idx + 1} / {_NUM_EMISSIONS}",
                (w // 2, hud_h // 2),
                COLOR_TEXT_HIGHLIGHT, font_size="medium", center=True)

            # Bottom instruction bar
            bar_h = 58
            pygame.draw.rect(screen, (235, 235, 240), (0, h - bar_h, w, bar_h))
            pygame.draw.line(screen, (200, 200, 210), (0, h - bar_h), (w, h - bar_h), 2)

            if self._state == self._INTRO:
                msg, color = ("Get ready \u2014 watch the detector ring carefully.  "
                              "Two detectors will blink: the closer one lights up first!"), COLOR_TEXT
            elif self._state == self._FIRING:
                msg, color = ("Watch the detector ring \u2014 two detectors will blink.  "
                              "Which one lit up first?"), COLOR_TEXT
            elif self._state == self._WAITING:
                msg, color = ("Detectors done.  Click on the grid where you think "
                              "the annihilation occurred."), (40, 100, 200)
            else:
                if self._guess_screen:
                    msg = (f"{feedback}   \u2014   \u25cf Orange = true position   "
                           "\u25cf Blue = your guess   [click or Space to continue]")
                else:
                    msg = ("\u25cf Orange dot = true annihilation position.   "
                           "[click or Space to continue]")
                color = fb_color

            self.renderer.draw_text(msg, (16, h - bar_h + 11), color, font_size="small")

            # Jump to Game button
            self._compute_jump_btn()
            self.renderer.draw_button(
                self._jump_btn, "Jump to Game \u2192",
                self._jump_btn.collidepoint(mp),
                color=(140, 75, 55), hover_color=(170, 95, 70))

        # ── Demo HUD + bottom bar ──────────────────────────────────────
        elif self._state == self._DEMO_PLAY:
            pygame.draw.rect(screen, (235, 235, 240), (0, 0, w, hud_h))
            pygame.draw.line(screen, (200, 200, 210), (0, hud_h), (w, hud_h), 2)
            self.renderer.draw_text(
                "Calibration \u2014 Example Annihilation",
                (w // 2, hud_h // 2),
                COLOR_TEXT_HIGHLIGHT, font_size="medium", center=True)

            bar_h = 58
            pygame.draw.rect(screen, (235, 235, 240), (0, h - bar_h, w, bar_h))
            pygame.draw.line(screen, (200, 200, 210), (0, h - bar_h), (w, h - bar_h), 2)

            if self._demo is None or self._demo.phase == _DemoAnim.INTRO:
                msg = ("A positron is about to annihilate with an electron \u2014 "
                       "watch what happens!")
            elif self._demo.phase == _DemoAnim.PHOTONS:
                msg = ("Two gamma photons travel in exactly opposite directions "
                       "toward the detector ring\u2026")
            else:
                msg = ("The orange line (LOR) shows where the emission must lie.  "
                       "In the real game you only get the detector blinks!")
            self.renderer.draw_text(msg, (16, h - bar_h + 11), COLOR_TEXT, font_size="small")
