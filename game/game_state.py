"""Main game state machine and game logic."""

import pygame
import numpy as np
import random
from enum import Enum, auto
from typing import Optional, Tuple, List

import game.constants as constants
from game.constants import (
    FPS, DIFFICULTY_SETTINGS,
    DETECTOR_RING_RADIUS_RATIO, MATRIX_SIZE_RATIO,
    EMISSION_INTERVAL, WINDOW_SCALE
)
from game.renderer import Renderer
from game.detector_ring import DetectorRing
from game.image_matrix import ImageMatrix
from game.shape_generator import generate_shape, find_edge_pixels, get_edge_pixel_positions
from game.physics import PETPhysics, PhotonEmission, calculate_dice_score
from scipy.ndimage import binary_fill_holes
from game.ui.menu import MainMenu, DifficultySelect
from game.ui.tutorial import Tutorial
from game.ui.hud import HUD
from game.ui.end_screen import EndScreen, CorrectionPhase
from game.ui.calibration import CalibrationPhase


class GameState(Enum):
    """Game state enumeration."""
    MENU = auto()
    DIFFICULTY_SELECT = auto()
    TUTORIAL = auto()
    TRANSITIONING = auto()
    CALIBRATION = auto()
    COUNTDOWN = auto()
    PLAYING = auto()
    CORRECTION = auto()
    RESULTS = auto()


class Game:
    """Main game class managing state and game loop."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("GuessTheSignal - PET Educational Game")

        # Calculate window size based on screen resolution
        display_info = pygame.display.Info()
        screen_w, screen_h = display_info.current_w, display_info.current_h

        # Scale to percentage of screen, maintaining 4:3 aspect ratio
        max_width = int(screen_w * WINDOW_SCALE)
        max_height = int(screen_h * WINDOW_SCALE)

        # Use 4:3 aspect ratio
        if max_width / max_height > 4 / 3:
            window_height = max_height
            window_width = int(window_height * 4 / 3)
        else:
            window_width = max_width
            window_height = int(window_width * 3 / 4)

        # Update constants module so UI components use correct sizes
        constants.WINDOW_WIDTH = window_width
        constants.WINDOW_HEIGHT = window_height
        constants.HUD_HEIGHT = int(window_height * 0.09)
        constants.HUD_PADDING = int(window_height * 0.02)
        constants.MENU_BUTTON_WIDTH = int(window_width * 0.25)
        constants.MENU_BUTTON_HEIGHT = int(window_height * 0.065)
        constants.MENU_BUTTON_SPACING = int(window_height * 0.02)

        self.screen = pygame.display.set_mode((window_width, window_height))
        self.clock = pygame.time.Clock()
        self.running = True

        # Store dimensions for easy access
        self.window_width = window_width
        self.window_height = window_height

        # Initialize renderer
        self.renderer = Renderer(self.screen)

        # Initialize UI components
        self.main_menu = MainMenu(self.renderer)
        self.difficulty_select = DifficultySelect(self.renderer)
        self.tutorial = Tutorial(self.renderer)
        self.calibration = CalibrationPhase(self.renderer)
        self.hud = HUD(self.renderer)
        self.end_screen = EndScreen(self.renderer)
        self.correction_ui = CorrectionPhase(self.renderer)

        # Game state
        self.state = GameState.MENU
        self.current_difficulty: Optional[str] = None
        self.from_tutorial = False

        # Game objects (initialized when game starts)
        self.detector_ring: Optional[DetectorRing] = None
        self.image_matrix: Optional[ImageMatrix] = None
        self.physics: Optional[PETPhysics] = None
        self.true_shape: Optional[np.ndarray] = None
        self.edge_pixels: List[Tuple[int, int]] = []
        self.emission_queue: List[Tuple[int, int]] = []

        # Current emission state
        self.current_emission: Optional[PhotonEmission] = None
        self.current_lor: Optional[Tuple[int, int]] = None  # (det1, det2)
        self.lor_display_time = 0
        self.emission_source_pos: Optional[Tuple[float, float]] = None

        # Timing
        self.last_emission_time = 0
        self.emissions_fired = 0
        self._countdown_start = 0
        self._transition_start = 0
        self._transition_difficulty: Optional[str] = None

        # For tutorial mode probability visualization
        self.show_probability_zone = False
        self.probability_pixels: List[Tuple[int, int]] = []
        self.probability_intensities: List[float] = []

    def start_game(self, difficulty: str):
        """Initialize a new game with the given difficulty."""
        self.current_difficulty = difficulty
        settings = DIFFICULTY_SETTINGS[difficulty]

        grid_size = settings["grid_size"]
        num_detectors = settings["detectors"]
        shape_type = settings["shape_type"]

        # Calculate layout
        hud_height = constants.HUD_HEIGHT
        game_area_center = (self.window_width // 2, (self.window_height + hud_height) // 2)
        game_area_size = min(self.window_width, self.window_height - hud_height) - 40

        ring_radius = game_area_size * DETECTOR_RING_RADIUS_RATIO
        matrix_size = game_area_size * MATRIX_SIZE_RATIO
        pixel_size = matrix_size / grid_size

        # Create game objects
        self.detector_ring = DetectorRing(num_detectors, game_area_center, ring_radius)
        self.image_matrix = ImageMatrix(grid_size, game_area_center, pixel_size)
        self.physics = PETPhysics(game_area_center, ring_radius)

        # Generate shape
        self.true_shape = generate_shape(shape_type, grid_size)
        self.image_matrix.set_true_shape(self.true_shape)

        # Find edge pixels and create emission queue
        edge_mask = find_edge_pixels(self.true_shape)
        self.edge_pixels = get_edge_pixel_positions(edge_mask)

        # Fallback: degenerate shapes can yield zero edge pixels; use all shape pixels
        if not self.edge_pixels:
            positions = np.argwhere(self.true_shape)
            self.edge_pixels = [(int(r), int(c)) for r, c in positions]

        # Shuffle edge pixels for random emission order
        self.emission_queue = self.edge_pixels.copy()
        random.shuffle(self.emission_queue)

        # Reset HUD completely before setting new game info
        self.hud.reset()
        self.hud.set_game_info(difficulty, len(self.emission_queue))

        # Reset all game state
        self.emissions_fired = 0
        current_time = pygame.time.get_ticks()
        self.last_emission_time = current_time
        self.lor_display_time = current_time  # Reset to prevent stale timing issues
        self.current_emission = None
        self.current_lor = None
        self.emission_source_pos = None

        # Reset tutorial visualization state
        self.show_probability_zone = False
        self.probability_pixels = []
        self.probability_intensities = []

        # Set up calibration with the freshly created game objects, then run it
        self.calibration.setup(self.image_matrix, self.detector_ring, self.physics)
        self.state = GameState.CALIBRATION

    def _finish_calibration(self):
        """Transition from calibration to the countdown, then gameplay."""
        # Clear any detector hits left over from calibration
        for d in self.detector_ring.detectors:
            d.is_hit        = False
            d.blink_progress = 0.0
        self.detector_ring.pending_hits.clear()
        self._countdown_start = pygame.time.get_ticks()
        self.state = GameState.COUNTDOWN

    def _finish_countdown(self):
        """Transition from countdown to actual gameplay."""
        self.last_emission_time = pygame.time.get_ticks()
        self.state = GameState.PLAYING

    def fire_emission(self):
        """Fire a photon emission from the next edge pixel."""
        if not self.emission_queue:
            return

        # Get next edge pixel
        row, col = self.emission_queue.pop(0)

        # Convert to screen coordinates
        source_pos = self.image_matrix.pixel_to_screen(row, col)
        self.emission_source_pos = source_pos

        # Create emission
        self.current_emission = self.physics.emit_from_pixel(source_pos)

        # Find detector hits
        det1, det2, dist1, dist2 = self.physics.find_detector_hits(
            self.current_emission, self.detector_ring
        )

        # Calculate TOF delays
        max_dist = self.detector_ring.radius * 2
        delay1, delay2 = self.physics.calculate_tof_delays(dist1, dist2, max_dist)

        # Schedule detector hits
        current_time = pygame.time.get_ticks()
        self.detector_ring.schedule_hit(det1, delay1, current_time)
        self.detector_ring.schedule_hit(det2, delay2, current_time)

        # Store LOR info
        self.current_lor = (det1, det2)
        self.lor_display_time = current_time

        # Update progress
        self.emissions_fired += 1
        self.hud.update_progress(self.emissions_fired)
        self.last_emission_time = current_time

    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if self.state == GameState.MENU:
                action = self.main_menu.handle_event(event)
                if action == "play":
                    self.from_tutorial = False
                    self.state = GameState.DIFFICULTY_SELECT
                elif action == "tutorial":
                    self.tutorial.current_page = 0
                    self.from_tutorial = True
                    self.state = GameState.TUTORIAL
                elif action == "quit":
                    self.running = False

            elif self.state == GameState.DIFFICULTY_SELECT:
                action = self.difficulty_select.handle_event(event)
                if action == "back":
                    self.state = GameState.MENU
                elif action in DIFFICULTY_SETTINGS:
                    self._transition_start = pygame.time.get_ticks()
                    self._transition_difficulty = action
                    self.state = GameState.TRANSITIONING

            elif self.state == GameState.TUTORIAL:
                action = self.tutorial.handle_event(event)
                if action == "done":
                    if self.from_tutorial:
                        self.state = GameState.DIFFICULTY_SELECT
                    else:
                        self.state = GameState.MENU

            elif self.state == GameState.CALIBRATION:
                action = self.calibration.handle_event(event, pygame.time.get_ticks())
                if action == "done":
                    self._finish_calibration()

            elif self.state == GameState.PLAYING:
                # HUD pause button - check first
                if self.hud.handle_event(event):
                    self.state = GameState.MENU
                # Grid clicks (only if HUD didn't handle the event)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    pixel = self.image_matrix.screen_to_pixel(mouse_pos[0], mouse_pos[1])
                    if pixel:
                        self.image_matrix.add_guess(pixel[0], pixel[1])
                # Space to manually trigger emission (for testing/slow play)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    if self.emission_queue:
                        self.fire_emission()

            elif self.state == GameState.CORRECTION:
                # Correction UI - check buttons first
                action = self.correction_ui.handle_event(event)
                if action == "finalize":
                    self._calculate_results()
                    self.state = GameState.RESULTS
                elif action == "clear":
                    self.image_matrix.clear_guesses()
                # HUD pause button
                elif self.hud.handle_event(event):
                    self.state = GameState.MENU
                # Grid clicks for toggling (only if no button was clicked)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    pixel = self.image_matrix.screen_to_pixel(mouse_pos[0], mouse_pos[1])
                    if pixel:
                        self.image_matrix.toggle_guess(pixel[0], pixel[1])

            elif self.state == GameState.RESULTS:
                action = self.end_screen.handle_event(event)
                if action == "play_again":
                    if self.current_difficulty:
                        self.start_game(self.current_difficulty)
                elif action == "menu":
                    # Reset tutorial flag when going back to menu
                    self.from_tutorial = False
                    self.state = GameState.MENU

    def _fill_shape_from_edges(self):
        """Fill in the shape from the user's edge guesses using flood fill."""
        grid_size = self.image_matrix.grid_size

        # Create a mask from guessed edge pixels
        edge_mask = np.zeros((grid_size, grid_size), dtype=bool)
        for row, col in self.image_matrix.guessed_pixels:
            if 0 <= row < grid_size and 0 <= col < grid_size:
                edge_mask[row, col] = True

        # Use binary_fill_holes to fill the interior
        filled_mask = binary_fill_holes(edge_mask)

        # Update guessed pixels to include filled interior
        self.image_matrix.guessed_pixels.clear()
        for row in range(grid_size):
            for col in range(grid_size):
                if filled_mask[row, col]:
                    self.image_matrix.guessed_pixels.add((row, col))

    def _calculate_results(self):
        """Calculate and set results for end screen."""
        # First fill the shape from edges
        self._fill_shape_from_edges()

        dice = calculate_dice_score(self.true_shape, self.image_matrix.guessed_pixels)

        true_pixels = int(np.sum(self.true_shape))
        guessed_pixels = len(self.image_matrix.guessed_pixels)

        # Calculate intersection (correct pixels)
        correct = 0
        for row, col in self.image_matrix.guessed_pixels:
            if 0 <= row < self.true_shape.shape[0] and 0 <= col < self.true_shape.shape[1]:
                if self.true_shape[row, col]:
                    correct += 1

        self.end_screen.set_results(dice, true_pixels, guessed_pixels, correct)

    def update(self):
        """Update game state."""
        current_time = pygame.time.get_ticks()

        if self.state == GameState.PLAYING:
            # Update detector ring
            self.detector_ring.update(current_time)

            # Auto-fire emissions at intervals
            if self.emission_queue and current_time - self.last_emission_time >= EMISSION_INTERVAL:
                self.fire_emission()

            # Check if all emissions done
            if not self.emission_queue and self.emissions_fired > 0:
                # Wait for current LOR to finish displaying
                if current_time - self.lor_display_time > 2000:
                    self.state = GameState.CORRECTION
                    self.hud.set_correction_phase(True)

        elif self.state == GameState.TRANSITIONING:
            if current_time - self._transition_start >= 2000:
                self.start_game(self._transition_difficulty)

        elif self.state == GameState.CALIBRATION:
            result = self.calibration.update(current_time)
            if result == "done":
                self._finish_calibration()

        elif self.state == GameState.COUNTDOWN:
            # 3.5 s total: "3" / "2" / "1" each for 1 s, "GO!" for 0.5 s
            if current_time - self._countdown_start >= 3500:
                self._finish_countdown()

        elif self.state == GameState.CORRECTION:
            # Update detector ring (for visual consistency)
            if self.detector_ring:
                self.detector_ring.update(current_time)

    def draw(self):
        """Draw the current game state."""
        if self.state == GameState.MENU:
            self.main_menu.draw()

        elif self.state == GameState.DIFFICULTY_SELECT:
            self.difficulty_select.draw()

        elif self.state == GameState.TUTORIAL:
            self.tutorial.draw()

        elif self.state == GameState.TRANSITIONING:
            progress = min(1.0, (pygame.time.get_ticks() - self._transition_start) / 2000.0)
            self.renderer.draw_transition_background(progress)

        elif self.state == GameState.CALIBRATION:
            self.calibration.draw(pygame.time.get_ticks())

        elif self.state == GameState.COUNTDOWN:
            self._draw_game()
            self._draw_countdown()

        elif self.state == GameState.PLAYING:
            self._draw_game()

        elif self.state == GameState.CORRECTION:
            self._draw_game(correction_phase=True)
            self.correction_ui.draw()

        elif self.state == GameState.RESULTS:
            self._draw_game(show_results=True)
            self.end_screen.draw()

        pygame.display.flip()

    def _draw_game(self, correction_phase: bool = False, show_results: bool = False):
        """Draw the main game view."""
        self.renderer.clear()
        self.renderer.draw_game_background()

        # Draw HUD
        self.hud.draw()

        # Draw detector ring outline (reference circle)
        self.renderer.draw_ring_outline(
            self.detector_ring.center,
            self.detector_ring.radius
        )

        # Draw image matrix
        self.image_matrix.draw(self.screen, show_results=show_results)

        # Draw detector ring
        self.detector_ring.draw(self.screen)

        # LOR line and emission indicator only shown in tutorial mode
        # In normal gameplay, player must rely on detector blink timing only

    def _draw_countdown(self):
        """Overlay the 3-2-1-GO! countdown on top of the game board."""
        import math as _math
        now = pygame.time.get_ticks()
        elapsed = now - self._countdown_start

        # Determine which label to show and how far through its 1-second slot we are
        if elapsed < 1000:
            label, slot_t = "3", elapsed / 1000.0
        elif elapsed < 2000:
            label, slot_t = "2", (elapsed - 1000) / 1000.0
        elif elapsed < 3000:
            label, slot_t = "1", (elapsed - 2000) / 1000.0
        else:
            label, slot_t = "GO!", (elapsed - 3000) / 500.0

        # Each number pops in large then shrinks slightly; GO! does the reverse
        if label == "GO!":
            scale = 1.0 + 0.15 * (1.0 - min(1.0, slot_t))
            alpha = int(255 * max(0.0, 1.0 - slot_t))
            color = (20, 140, 60)
        else:
            scale = 1.0 + 0.25 * _math.exp(-slot_t * 4)
            alpha = 255
            color = (180, 120, 0)

        w, h = constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT

        # Semi-transparent dark vignette so the number pops
        vignette = pygame.Surface((w, h), pygame.SRCALPHA)
        vignette.fill((0, 0, 0, 90))
        self.screen.blit(vignette, (0, 0))

        # Render number at scaled size
        font_size = max(48, int(h * 0.28 * scale))
        font = pygame.font.Font(None, font_size)
        text_surf = font.render(label, True, color)
        text_surf.set_alpha(alpha)
        rect = text_surf.get_rect(center=(w // 2, h // 2))
        self.screen.blit(text_surf, rect)

        # Small instruction line below (only during 3/2/1)
        if label != "GO!":
            hint_font = pygame.font.Font(None, max(20, int(h * 0.032)))
            hint = hint_font.render("Get ready to mark the signal source!", True, (60, 60, 70))
            hint.set_alpha(200)
            hrect = hint.get_rect(center=(w // 2, h // 2 + int(h * 0.17)))
            self.screen.blit(hint, hrect)

    def run(self):
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
