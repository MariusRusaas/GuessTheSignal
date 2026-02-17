"""Tutorial screens with PET imaging explanations and interactive animations."""

import pygame
import math
from typing import Optional, Tuple, List
import game.constants as constants
from game.constants import (
    COLOR_TEXT, COLOR_TEXT_HIGHLIGHT, COLOR_BACKGROUND,
    COLOR_DETECTOR_IDLE, COLOR_DETECTOR_HIT, COLOR_GRID
)


# Tutorial page configurations
TUTORIAL_PAGES = [
    {
        "title": "What is PET Imaging?",
        "content": [
            "PET is a medical imaging technique that shows",
            "how tissues and organs function in the body.",
            "",
            "A radioactive tracer (like FDG) is injected,",
            "which distributes through the body."
        ],
        "animation": "injection"
    },
    {
        "title": "Radioactive Decay",
        "content": [
            "Let's zoom in on one of the tracer molecules.",
            "",
            "The tracer contains a radioactive atom (F-18)",
            "which undergoes radioactive decay.",
            "",
            "During decay, a positron (e+) is emitted",
            "from the nucleus at high speed."
        ],
        "animation": "decay"
    },
    {
        "title": "Positron Annihilation",
        "content": [
            "When a positron meets an electron, they annihilate each other.",
            "",
            "This produces TWO gamma photons that travel in OPPOSITE directions",
            "(180 degrees apart) at the speed of light.",
            "",
            "In this game, the hidden shape represents regions with radioactive",
            "tracer. Positrons are emitted from the edges of these regions."
        ],
        "animation": "annihilation"
    },
    {
        "title": "Lines of Response (LOR)",
        "content": [
            "Watch the detector ring: an annihilation event occurs,",
            "and two photons travel to opposite detectors.",
            "",
            "The line connecting the hit detectors is called",
            "the Line of Response (LOR).",
            "",
            "The true emission position is somewhere on this line!"
        ],
        "animation": "lor"
    },
    {
        "title": "Time of Flight (TOF)",
        "content": [
            "Now watch an OFF-CENTER annihilation.",
            "",
            "The photon traveling to the CLOSER detector arrives FIRST!",
            "This timing difference helps narrow down the position.",
            "",
            "The colored region shows likely positions based on timing.",
            "Use this to estimate where the emission occurred!"
        ],
        "animation": "tof"
    },
    {
        "title": "How to Play",
        "content": [
            "1. Watch the detector ring - two detectors will blink",
            "   (the closer one first due to TOF)",
            "",
            "2. Use the timing difference to estimate the position",
            "",
            "3. Click on the grid to mark your guesses",
            "",
            "4. After all emissions, refine your guesses",
            "",
            "5. Your score is based on how well your guess",
            "   matches the true shape (DICE coefficient)"
        ],
        "animation": None
    }
]


class TutorialAnimation:
    """Handles animations for tutorial pages."""

    # Animation phases
    PHASE_IDLE = 0
    PHASE_SPLASH = 1
    PHASE_PHOTON_TRAVEL = 2
    PHASE_DETECTOR_HIT = 3
    PHASE_SHOW_LOR = 4
    PHASE_SHOW_TOF = 5
    PHASE_COMPLETE = 6

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset animation state."""
        self.phase = self.PHASE_IDLE
        self.start_time = 0
        self.phase_start_time = 0

        # Emission source position (screen coordinates)
        self.source_pos = (0, 0)
        self.is_centered = True

        # Photon positions and targets
        self.photon1_pos = (0, 0)
        self.photon2_pos = (0, 0)
        self.detector1_pos = (0, 0)
        self.detector2_pos = (0, 0)
        self.detector1_idx = 0
        self.detector2_idx = 0

        # Detector hit states
        self.detector1_hit = False
        self.detector2_hit = False
        self.detector1_hit_time = 0
        self.detector2_hit_time = 0

        # Animation parameters
        self.emission_angle = 0
        self.photon_speed = 0.3  # pixels per ms

    def start(self, center: Tuple[float, float], ring_radius: float,
              is_centered: bool = True, current_time: int = 0):
        """Start a new animation."""
        self.reset()
        self.start_time = current_time
        self.phase_start_time = current_time
        self.is_centered = is_centered

        # Calculate source position
        if is_centered:
            self.source_pos = center
        else:
            # Off-center position (about 40% towards edge)
            offset = ring_radius * 0.4
            angle = math.radians(30)  # 30 degrees from horizontal
            self.source_pos = (
                center[0] + offset * math.cos(angle),
                center[1] + offset * math.sin(angle)
            )

        # Random emission angle
        self.emission_angle = math.radians(45)  # Fixed for consistent demo

        # Calculate detector positions
        angle1 = self.emission_angle
        angle2 = self.emission_angle + math.pi

        self.detector1_pos = (
            center[0] + ring_radius * math.cos(angle1),
            center[1] + ring_radius * math.sin(angle1)
        )
        self.detector2_pos = (
            center[0] + ring_radius * math.cos(angle2),
            center[1] + ring_radius * math.sin(angle2)
        )

        # Calculate detector indices (for 64 detectors)
        self.detector1_idx = int((angle1 % (2 * math.pi)) / (2 * math.pi) * 64) % 64
        self.detector2_idx = int((angle2 % (2 * math.pi)) / (2 * math.pi) * 64) % 64

        # Initialize photon positions at source
        self.photon1_pos = self.source_pos
        self.photon2_pos = self.source_pos

        # Start with splash phase
        self.phase = self.PHASE_SPLASH

    def update(self, current_time: int):
        """Update animation state."""
        if self.phase == self.PHASE_IDLE:
            return

        elapsed = current_time - self.phase_start_time

        if self.phase == self.PHASE_SPLASH:
            # Splash animation lasts 500ms
            if elapsed > 500:
                self.phase = self.PHASE_PHOTON_TRAVEL
                self.phase_start_time = current_time

        elif self.phase == self.PHASE_PHOTON_TRAVEL:
            # Move photons towards detectors
            travel_time = elapsed

            # Calculate distances
            dist1 = math.sqrt(
                (self.detector1_pos[0] - self.source_pos[0])**2 +
                (self.detector1_pos[1] - self.source_pos[1])**2
            )
            dist2 = math.sqrt(
                (self.detector2_pos[0] - self.source_pos[0])**2 +
                (self.detector2_pos[1] - self.source_pos[1])**2
            )

            # Slow motion travel (1500ms total for full distance)
            travel_duration = 1500
            progress1 = min(1.0, travel_time / travel_duration)
            progress2 = min(1.0, travel_time / travel_duration)

            # For off-center, make one photon arrive earlier
            if not self.is_centered:
                # Closer detector gets hit first
                if dist1 < dist2:
                    progress1 = min(1.0, travel_time / (travel_duration * dist1 / dist2))
                else:
                    progress2 = min(1.0, travel_time / (travel_duration * dist2 / dist1))

            # Update photon positions
            self.photon1_pos = (
                self.source_pos[0] + (self.detector1_pos[0] - self.source_pos[0]) * progress1,
                self.source_pos[1] + (self.detector1_pos[1] - self.source_pos[1]) * progress1
            )
            self.photon2_pos = (
                self.source_pos[0] + (self.detector2_pos[0] - self.source_pos[0]) * progress2,
                self.source_pos[1] + (self.detector2_pos[1] - self.source_pos[1]) * progress2
            )

            # Check for detector hits
            if progress1 >= 1.0 and not self.detector1_hit:
                self.detector1_hit = True
                self.detector1_hit_time = current_time

            if progress2 >= 1.0 and not self.detector2_hit:
                self.detector2_hit = True
                self.detector2_hit_time = current_time

            # Both detectors hit -> move to next phase
            if self.detector1_hit and self.detector2_hit:
                if elapsed > travel_duration + 300:  # Wait a bit after both hit
                    self.phase = self.PHASE_SHOW_LOR
                    self.phase_start_time = current_time

        elif self.phase == self.PHASE_SHOW_LOR:
            # Show LOR for 1500ms before showing TOF (if applicable)
            if elapsed > 1500:
                if not self.is_centered:
                    self.phase = self.PHASE_SHOW_TOF
                    self.phase_start_time = current_time
                else:
                    self.phase = self.PHASE_COMPLETE

        elif self.phase == self.PHASE_SHOW_TOF:
            # TOF display stays until reset
            if elapsed > 500:
                self.phase = self.PHASE_COMPLETE

    def get_splash_radius(self, current_time: int) -> float:
        """Get current splash animation radius."""
        if self.phase != self.PHASE_SPLASH:
            return 0
        elapsed = current_time - self.phase_start_time
        # Expanding then fading splash
        progress = elapsed / 500.0
        return 20 * progress

    def get_splash_alpha(self, current_time: int) -> int:
        """Get current splash animation alpha."""
        if self.phase != self.PHASE_SPLASH:
            return 0
        elapsed = current_time - self.phase_start_time
        progress = elapsed / 500.0
        return int(255 * (1 - progress))

    def is_complete(self) -> bool:
        """Check if animation is complete."""
        return self.phase == self.PHASE_COMPLETE

    def should_show_lor(self) -> bool:
        """Check if LOR should be displayed."""
        return self.phase >= self.PHASE_SHOW_LOR

    def should_show_tof(self) -> bool:
        """Check if TOF distribution should be displayed."""
        # Only show TOF for off-center animations (TOF page)
        return self.phase >= self.PHASE_SHOW_TOF and not self.is_centered


class InjectionAnimation:
    """Handles the injection/distribution animation for the first tutorial page."""

    # Animation phases
    PHASE_IDLE = 0
    PHASE_INJECTION = 1    # Syringe injecting into arm
    PHASE_DISTRIBUTE = 2   # Molecules spreading through body via bloodstream
    PHASE_PAUSE = 3        # Pause to show distributed tracer
    PHASE_DIST_COMPLETE = 4  # Distribution complete (for split slide mode)
    PHASE_ZOOM = 5         # Zooming in on one molecule
    PHASE_VIEW = 6         # Pause to view the molecule before decay
    PHASE_DECAY = 7        # Radioactive decay, positron ejected
    PHASE_COMPLETE = 8

    # Body landmark positions (normalized coordinates)
    ARM_INJECTION = (-0.55, 0.05)    # Left forearm
    SHOULDER = (-0.32, -0.25)        # Left shoulder
    HEART = (-0.05, -0.05)           # Heart area

    # Final distribution targets (throughout body - kept inside torso/limbs)
    DISTRIBUTION_TARGETS = [
        (0.0, -0.38),    # Head/neck area
        (-0.08, -0.2),   # Upper left chest
        (0.08, -0.18),   # Upper right chest
        (-0.12, -0.02),  # Left chest near heart
        (0.10, 0.0),     # Right chest
        (0.0, 0.12),     # Center abdomen
        (-0.06, 0.22),   # Lower left abdomen
        (0.06, 0.20),    # Lower right abdomen
        (-0.12, 0.38),   # Left thigh (inside body)
        (0.10, 0.40),    # Right thigh (inside body)
        (0.28, -0.10),   # Right upper arm
    ]

    # Positron exit angle (shared with annihilation animation)
    POSITRON_EXIT_ANGLE = math.radians(-30)  # Exits toward upper-right

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset animation state."""
        self.phase = self.PHASE_IDLE
        self.phase_start_time = 0
        self.stop_after_distribution = False  # If True, stops after PHASE_PAUSE

        # Syringe state
        self.syringe_progress = 0.0
        self.plunger_progress = 0.0

        # Molecules for distribution
        self.molecules = []

        # Zoom state
        self.zoom_level = 1.0
        self.zoom_center = (0.0, 0.0)
        self.zoom_target_mol = None
        self.circle_fade_alpha = 255  # Circle overlay fades out during zoom

        # Decay state
        self.f18_flash_intensity = 0.0
        self.flash_buildup = 0.0  # Builds from 0 to 1 during decay
        self.positron_ejected = False
        self.positron_progress = 0.0
        self.decay_complete = False  # F-18 has become O-18

    def start(self, current_time: int, stop_after_distribution: bool = True):
        """Start the animation.

        Args:
            current_time: Current time in milliseconds
            stop_after_distribution: If True, animation stops after distribution completes
        """
        self.reset()
        self.stop_after_distribution = stop_after_distribution
        self.phase = self.PHASE_INJECTION
        self.phase_start_time = current_time
        self._setup_molecules()

    def _setup_molecules(self):
        """Initialize molecules for distribution."""
        self.molecules = []
        for i, target in enumerate(self.DISTRIBUTION_TARGETS):
            self.molecules.append({
                'pos': self.ARM_INJECTION,
                'path_progress': 0.0,
                'target': target,
                'alpha': 0,
                'delay': i * 350,  # Stagger release
                'at_heart': False,
                'distributing': False,
            })

        # Select one molecule to zoom into (one that ends up in a visible spot)
        self.zoom_target_mol = self.molecules[4]  # Abdomen molecule

    def _get_path_position(self, progress: float, target: tuple) -> tuple:
        """Get position along the path: injection -> shoulder -> heart -> target."""
        if progress < 0.3:
            # Injection site to shoulder
            t = progress / 0.3
            eased = t * t  # Ease in
            return (
                self.ARM_INJECTION[0] + (self.SHOULDER[0] - self.ARM_INJECTION[0]) * eased,
                self.ARM_INJECTION[1] + (self.SHOULDER[1] - self.ARM_INJECTION[1]) * eased
            )
        elif progress < 0.5:
            # Shoulder to heart
            t = (progress - 0.3) / 0.2
            return (
                self.SHOULDER[0] + (self.HEART[0] - self.SHOULDER[0]) * t,
                self.SHOULDER[1] + (self.HEART[1] - self.SHOULDER[1]) * t
            )
        else:
            # Heart to final target
            t = (progress - 0.5) / 0.5
            eased = 1 - (1 - t) ** 2  # Ease out
            return (
                self.HEART[0] + (target[0] - self.HEART[0]) * eased,
                self.HEART[1] + (target[1] - self.HEART[1]) * eased
            )

    def update(self, current_time: int):
        """Update animation state."""
        if self.phase == self.PHASE_IDLE:
            return

        elapsed = current_time - self.phase_start_time

        if self.phase == self.PHASE_INJECTION:
            # Syringe injection (1500ms)
            progress = min(1.0, elapsed / 1500.0)

            # Move syringe in first half
            self.syringe_progress = min(1.0, progress * 2.5)

            # Push plunger in second half
            if progress > 0.4:
                self.plunger_progress = (progress - 0.4) / 0.6

            if progress >= 1.0:
                self.phase = self.PHASE_DISTRIBUTE
                self.phase_start_time = current_time

        elif self.phase == self.PHASE_DISTRIBUTE:
            # Molecules spreading through bloodstream
            # Each molecule takes 4 seconds to reach its target
            # Last molecule starts at delay = 10 * 350 = 3500ms
            # So total time = 3500 + 4000 = 7500ms for all to complete

            for mol in self.molecules:
                mol_elapsed = elapsed - mol['delay']
                if mol_elapsed > 0:
                    mol['path_progress'] = min(1.0, mol_elapsed / 4000.0)
                    mol['pos'] = self._get_path_position(mol['path_progress'], mol['target'])
                    mol['alpha'] = min(255, int(min(mol['path_progress'] * 3, 1.0) * 255))

            # Check if ALL molecules have reached their destinations
            all_complete = all(mol['path_progress'] >= 1.0 for mol in self.molecules)
            if all_complete:
                self.phase = self.PHASE_PAUSE
                self.phase_start_time = current_time

        elif self.phase == self.PHASE_PAUSE:
            # Short pause to show distributed tracer (1200ms)
            if elapsed >= 1200:
                if self.stop_after_distribution:
                    # Stop here for split slide mode
                    self.phase = self.PHASE_DIST_COMPLETE
                else:
                    # Continue to zoom for combined mode
                    self.phase = self.PHASE_ZOOM
                    self.phase_start_time = current_time
                    self.zoom_center = self.zoom_target_mol['pos']
                    self.circle_fade_alpha = 255

        elif self.phase == self.PHASE_ZOOM:
            # Zooming in (4000ms) - smooth zoom keeping body visible
            progress = min(1.0, elapsed / 4000.0)
            # Very smooth S-curve easing
            eased = progress * progress * progress * (progress * (6 * progress - 15) + 10)

            self.zoom_level = 1.0 + 19.0 * eased  # Zoom to 20x

            # Fade out circle overlay during first half of zoom
            fade_progress = min(1.0, progress * 2.0)  # Fade completes at 50% zoom
            self.circle_fade_alpha = int(255 * (1.0 - fade_progress))

            if progress >= 1.0:
                self.phase = self.PHASE_VIEW
                self.phase_start_time = current_time

        elif self.phase == self.PHASE_VIEW:
            # Brief pause to view molecule before decay (800ms)
            if elapsed >= 800:
                self.phase = self.PHASE_DECAY
                self.phase_start_time = current_time
                self.positron_ejected = False
                self.decay_complete = False
                self.flash_buildup = 0.0

        elif self.phase == self.PHASE_DECAY:
            # Radioactive decay: 4 flashes then positron at peak of 4th
            # Flash peaks at: 250, 750, 1250, 1750ms
            # Positron ejected slightly before visual peak (1720ms) for better sync
            # Total duration: 1720ms flash + 2000ms travel = 3720ms
            total_duration = 3720.0
            progress = min(1.0, elapsed / total_duration)

            flash_period = 500.0  # ms between peaks
            eject_time = 1720.0  # Slightly before calculated peak for visual sync

            if elapsed < eject_time + 150:  # Keep flash visible briefly after eject
                # 4 flashes at 500ms intervals, building in intensity
                flash_num = min(3, int(elapsed / flash_period))  # 0, 1, 2, 3
                time_in_flash = (elapsed % flash_period) / flash_period  # 0-1 within period

                # Intensity builds: 25%, 50%, 75%, 100%
                base_intensity = (flash_num + 1) / 4.0

                # Smooth pulse shape (sine wave, peak at 0.5)
                pulse = 0.5 + 0.5 * math.sin((time_in_flash - 0.25) * math.pi * 2)
                self.f18_flash_intensity = base_intensity * pulse
                self.flash_buildup = base_intensity
            else:
                self.f18_flash_intensity = 0.0

            # Positron ejected at peak of 4th flash
            if elapsed >= eject_time and not self.positron_ejected:
                self.positron_ejected = True
                self.decay_complete = True  # F-18 becomes O-18

            # Positron travels slower (2000ms to exit screen)
            if self.positron_ejected:
                self.positron_progress = min(1.0, (elapsed - eject_time) / 2000.0)

            if progress >= 1.0:
                self.phase = self.PHASE_COMPLETE

    def is_complete(self) -> bool:
        """Check if animation is complete."""
        return self.phase in (self.PHASE_COMPLETE, self.PHASE_DIST_COMPLETE)

    def start_decay(self, current_time: int):
        """Start the decay animation (zoom and decay phases only)."""
        # Set up molecules as if distribution just completed
        self._setup_molecules()
        for mol in self.molecules:
            mol['path_progress'] = 1.0
            mol['pos'] = mol['target']
            mol['alpha'] = 255

        # Select zoom target
        self.zoom_target_mol = self.molecules[5]  # Center abdomen molecule

        # Start at zoom phase
        self.phase = self.PHASE_ZOOM
        self.phase_start_time = current_time
        self.zoom_center = self.zoom_target_mol['pos']
        self.zoom_level = 1.0
        self.circle_fade_alpha = 255
        self.stop_after_distribution = False


class AnnihilationAnimation:
    """Handles the zoomed-in annihilation animation showing electron-positron collision."""

    # Animation phases
    PHASE_IDLE = 0
    PHASE_POSITRON_APPROACH = 1  # Positron moves in, electron stationary
    PHASE_FINAL_APPROACH = 2     # Both particles accelerate together
    PHASE_FLASH = 3              # Annihilation flash
    PHASE_PHOTONS = 4            # Photons shoot out
    PHASE_COMPLETE = 5

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset animation state."""
        self.phase = self.PHASE_IDLE
        self.phase_start_time = 0

        # Positron enters from bottom-left, traveling in same direction it exited (toward top-right)
        # Start position is OPPOSITE of exit angle (where it's coming FROM)
        entry_angle = InjectionAnimation.POSITRON_EXIT_ANGLE + math.pi
        self.positron_start = (
            0.9 * math.cos(entry_angle),
            0.9 * math.sin(entry_angle)
        )

        # Electron stationary position (slightly left of center)
        self.electron_start = (-0.25, 0.05)
        self.electron_pos = self.electron_start

        # Meeting point (slightly toward electron)
        self.meeting_point = (-0.05, 0.02)

        # Current positions
        self.positron_pos = self.positron_start

        # Spline control point for positron curve (creates arc motion from bottom-left)
        self.positron_control = (-0.2, 0.35)

        # Photon positions (emerge from center)
        self.photon1_pos = (0, 0)
        self.photon2_pos = (0, 0)
        self.photon_angle = math.radians(35)  # Angle photons travel at

        # Flash effect
        self.flash_radius = 0
        self.flash_alpha = 0

    def _bezier_point(self, t, p0, p1, p2):
        """Calculate point on quadratic bezier curve."""
        x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
        y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
        return (x, y)

    def start(self, current_time: int):
        """Start the animation."""
        self.reset()
        self.phase = self.PHASE_POSITRON_APPROACH
        self.phase_start_time = current_time

    def update(self, current_time: int):
        """Update animation state."""
        if self.phase == self.PHASE_IDLE:
            return

        elapsed = current_time - self.phase_start_time

        if self.phase == self.PHASE_POSITRON_APPROACH:
            # Positron moves along spline toward electron (2500ms)
            # Electron stays stationary
            progress = min(1.0, elapsed / 2500.0)

            # Ease slightly - not too fast
            eased = progress * (2 - progress)  # Ease out

            # Positron follows bezier curve from start, through control, to approach point
            # Keep some distance from electron until final approach phase
            approach_end = (self.electron_start[0] + 0.45, self.electron_start[1] + 0.05)
            self.positron_pos = self._bezier_point(eased, self.positron_start,
                                                   self.positron_control, approach_end)

            # Electron stays still
            self.electron_pos = self.electron_start

            if progress >= 1.0:
                self.phase = self.PHASE_FINAL_APPROACH
                self.phase_start_time = current_time

        elif self.phase == self.PHASE_FINAL_APPROACH:
            # Both particles accelerate toward each other (800ms)
            progress = min(1.0, elapsed / 800.0)
            # Cubic ease-in for acceleration feel
            eased = progress * progress * progress

            # Positron continues from approach point to meeting point
            positron_approach_start = (self.electron_start[0] + 0.45, self.electron_start[1] + 0.05)
            self.positron_pos = (
                positron_approach_start[0] + (self.meeting_point[0] - positron_approach_start[0]) * eased,
                positron_approach_start[1] + (self.meeting_point[1] - positron_approach_start[1]) * eased
            )

            # Electron moves toward meeting point
            self.electron_pos = (
                self.electron_start[0] + (self.meeting_point[0] - self.electron_start[0]) * eased,
                self.electron_start[1] + (self.meeting_point[1] - self.electron_start[1]) * eased
            )

            if progress >= 1.0:
                self.phase = self.PHASE_FLASH
                self.phase_start_time = current_time
                self.flash_radius = 0
                self.flash_alpha = 255

        elif self.phase == self.PHASE_FLASH:
            # Annihilation flash (400ms)
            progress = min(1.0, elapsed / 400.0)

            # Flash expands then fades
            self.flash_radius = 20 * progress
            self.flash_alpha = int(255 * (1 - progress * 0.7))

            # Both particles at meeting point (about to annihilate)
            self.electron_pos = self.meeting_point
            self.positron_pos = self.meeting_point

            if progress >= 1.0:
                self.phase = self.PHASE_PHOTONS
                self.phase_start_time = current_time
                # Photons emerge from meeting point
                self.photon1_pos = self.meeting_point
                self.photon2_pos = self.meeting_point

        elif self.phase == self.PHASE_PHOTONS:
            # Photons shoot out (1200ms)
            progress = min(1.0, elapsed / 1200.0)
            # Start fast then maintain speed
            eased = 1 - (1 - progress) * (1 - progress)

            # Photons travel in opposite directions from meeting point
            travel_dist = 1.2 * eased
            self.photon1_pos = (
                self.meeting_point[0] + travel_dist * math.cos(self.photon_angle),
                self.meeting_point[1] + travel_dist * math.sin(self.photon_angle)
            )
            self.photon2_pos = (
                self.meeting_point[0] - travel_dist * math.cos(self.photon_angle),
                self.meeting_point[1] - travel_dist * math.sin(self.photon_angle)
            )

            # Flash continues fading
            self.flash_alpha = max(0, int(255 * 0.3 * (1 - progress)))

            if progress >= 1.0:
                self.phase = self.PHASE_COMPLETE

    def is_complete(self) -> bool:
        """Check if animation is complete."""
        return self.phase == self.PHASE_COMPLETE


class Tutorial:
    """Tutorial screen sequence with interactive animations."""

    def __init__(self, renderer):
        self.renderer = renderer
        self.current_page = 0
        self.total_pages = len(TUTORIAL_PAGES)

        # Animation state
        self.animation = TutorialAnimation()
        self.annihilation_anim = AnnihilationAnimation()
        self.injection_anim = InjectionAnimation()
        self.animation_started = False
        self.last_page = -1

        # Buttons will be created dynamically
        self.prev_button = None
        self.next_button = None
        self.skip_button = None
        self.start_button = None
        self.replay_button = None

    def _create_buttons(self):
        """Create navigation buttons based on current window size."""
        w = constants.WINDOW_WIDTH
        h = constants.WINDOW_HEIGHT
        btn_w = constants.MENU_BUTTON_WIDTH
        btn_h = constants.MENU_BUTTON_HEIGHT

        button_y = h - 80

        self.prev_button = pygame.Rect(
            w // 2 - btn_w - 20,
            button_y,
            btn_w // 2,
            btn_h
        )

        self.next_button = pygame.Rect(
            w // 2 + 20 + btn_w // 2,
            button_y,
            btn_w // 2,
            btn_h
        )

        self.skip_button = pygame.Rect(
            w - 140,
            20,
            120,
            40
        )

        self.start_button = pygame.Rect(
            w // 2 - btn_w // 2,
            button_y,
            btn_w,
            btn_h
        )

        # Replay button for animation pages
        self.replay_button = pygame.Rect(
            20,
            h - 80,
            100,
            btn_h
        )

    def _get_animation_layout(self) -> Tuple[Tuple[float, float], float, float]:
        """Get layout parameters for animation area."""
        w = constants.WINDOW_WIDTH
        h = constants.WINDOW_HEIGHT

        # Animation area is on the right side of the screen
        anim_center_x = w * 0.65
        anim_center_y = h * 0.52

        # Size based on available space
        anim_size = min(w * 0.35, h * 0.45)
        ring_radius = anim_size * 0.42

        return (anim_center_x, anim_center_y), ring_radius, anim_size

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle input events. Returns 'done' when tutorial is finished."""
        self._create_buttons()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()

            # Skip button
            if self.skip_button.collidepoint(mouse_pos):
                return "done"

            # On last page, check start button
            if self.current_page == self.total_pages - 1:
                if self.start_button.collidepoint(mouse_pos):
                    return "done"
            else:
                # Replay button for animation pages
                page = TUTORIAL_PAGES[self.current_page]
                if page.get("animation") and self.replay_button.collidepoint(mouse_pos):
                    self._start_animation()
                    return None

                # Previous button
                if self.current_page > 0 and self.prev_button.collidepoint(mouse_pos):
                    self.current_page -= 1
                    self.animation_started = False

                # Next button
                if self.next_button.collidepoint(mouse_pos):
                    self.current_page += 1
                    self.animation_started = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT and self.current_page > 0:
                self.current_page -= 1
                self.animation_started = False
            elif event.key == pygame.K_RIGHT and self.current_page < self.total_pages - 1:
                self.current_page += 1
                self.animation_started = False
            elif event.key == pygame.K_ESCAPE:
                return "done"
            elif event.key == pygame.K_SPACE:
                # Space to replay animation
                page = TUTORIAL_PAGES[self.current_page]
                if page.get("animation"):
                    self._start_animation()

        return None

    def _start_animation(self):
        """Start or restart the animation for current page."""
        page = TUTORIAL_PAGES[self.current_page]
        anim_type = page.get("animation")

        if anim_type:
            current_time = pygame.time.get_ticks()

            if anim_type == "injection":
                self.injection_anim.start(current_time, stop_after_distribution=True)
            elif anim_type == "decay":
                self.injection_anim.start_decay(current_time)
            elif anim_type == "annihilation":
                self.annihilation_anim.start(current_time)
            else:
                center, ring_radius, _ = self._get_animation_layout()
                is_centered = (anim_type == "lor")
                self.animation.start(center, ring_radius, is_centered, current_time)

            self.animation_started = True

    def draw(self):
        """Draw the current tutorial page."""
        self._create_buttons()
        self.renderer.clear()

        w = constants.WINDOW_WIDTH
        h = constants.WINDOW_HEIGHT
        current_time = pygame.time.get_ticks()

        page = TUTORIAL_PAGES[self.current_page]
        has_animation = page.get("animation") is not None

        # Start animation automatically when entering an animation page
        if has_animation and not self.animation_started:
            self._start_animation()

        # Update animation
        anim_type = page.get("animation")
        if has_animation and self.animation_started:
            if anim_type in ("injection", "decay"):
                self.injection_anim.update(current_time)
            elif anim_type == "annihilation":
                self.annihilation_anim.update(current_time)
            else:
                self.animation.update(current_time)

        # Title
        self.renderer.draw_text(
            page["title"],
            (w // 2, int(h * 0.06)),
            COLOR_TEXT_HIGHLIGHT,
            font_size="large",
            center=True
        )

        # Page indicator
        self.renderer.draw_text(
            f"Page {self.current_page + 1} of {self.total_pages}",
            (w // 2, int(h * 0.11)),
            (120, 120, 130),
            font_size="small",
            center=True
        )

        # Draw animation area for pages with animations
        if has_animation:
            if anim_type in ("injection", "decay"):
                self._draw_injection_animation(current_time)
            elif anim_type == "annihilation":
                self._draw_annihilation_animation(current_time)
            else:
                self._draw_animation(current_time)

            # Content on the left side for animation pages
            content_x = int(w * 0.03)
            start_y = int(h * 0.18)
            line_height = int(h * 0.038)

            for i, line in enumerate(page["content"]):
                self.renderer.draw_text(
                    line,
                    (content_x, start_y + i * line_height),
                    COLOR_TEXT,
                    font_size="small",
                    center=False
                )
        else:
            # Standard centered content for non-animation pages
            start_y = int(h * 0.20)
            line_height = int(h * 0.04)
            for i, line in enumerate(page["content"]):
                self.renderer.draw_text(
                    line,
                    (w // 2, start_y + i * line_height),
                    COLOR_TEXT,
                    font_size="small",
                    center=True
                )

        # Navigation buttons
        mouse_pos = pygame.mouse.get_pos()

        # Skip button (always visible)
        hovered = self.skip_button.collidepoint(mouse_pos)
        self.renderer.draw_button(self.skip_button, "Skip", hovered)

        if self.current_page == self.total_pages - 1:
            # Start button on last page
            hovered = self.start_button.collidepoint(mouse_pos)
            self.renderer.draw_button(
                self.start_button, "Start Game", hovered,
                color=(60, 120, 80),
                hover_color=(80, 150, 100)
            )
        else:
            # Previous button
            if self.current_page > 0:
                hovered = self.prev_button.collidepoint(mouse_pos)
                self.renderer.draw_button(self.prev_button, "< Prev", hovered)

            # Next button
            hovered = self.next_button.collidepoint(mouse_pos)
            self.renderer.draw_button(self.next_button, "Next >", hovered)

            # Replay button for animation pages
            if has_animation:
                hovered = self.replay_button.collidepoint(mouse_pos)
                self.renderer.draw_button(self.replay_button, "Replay", hovered)

    def _draw_animation(self, current_time: int):
        """Draw the animation area with detector ring and effects."""
        screen = self.renderer.screen
        center, ring_radius, anim_size = self._get_animation_layout()

        # Draw detector ring background circle
        pygame.draw.circle(screen, (40, 40, 50),
                          (int(center[0]), int(center[1])),
                          int(ring_radius + 20), 2)

        # Draw grid area (simplified)
        grid_size = ring_radius * 1.2
        grid_rect = pygame.Rect(
            center[0] - grid_size/2,
            center[1] - grid_size/2,
            grid_size,
            grid_size
        )
        pygame.draw.rect(screen, COLOR_GRID, grid_rect)
        pygame.draw.rect(screen, (60, 60, 70), grid_rect, 1)

        # Draw detectors (64 detectors)
        num_detectors = 64
        arc_angle = math.radians(4)
        inner_radius = ring_radius - 12
        outer_radius = ring_radius + 12

        for i in range(num_detectors):
            angle = i * (2 * math.pi / num_detectors)

            # Check if this detector is hit
            is_hit = False
            hit_progress = 0

            if i == self.animation.detector1_idx and self.animation.detector1_hit:
                elapsed = current_time - self.animation.detector1_hit_time
                if elapsed < 600:
                    is_hit = True
                    hit_progress = 1.0 - (elapsed / 600.0)

            if i == self.animation.detector2_idx and self.animation.detector2_hit:
                elapsed = current_time - self.animation.detector2_hit_time
                if elapsed < 600:
                    is_hit = True
                    hit_progress = max(hit_progress, 1.0 - (elapsed / 600.0))

            # Determine color
            if is_hit:
                color = (
                    int(COLOR_DETECTOR_IDLE[0] + (COLOR_DETECTOR_HIT[0] - COLOR_DETECTOR_IDLE[0]) * hit_progress),
                    int(COLOR_DETECTOR_IDLE[1] + (COLOR_DETECTOR_HIT[1] - COLOR_DETECTOR_IDLE[1]) * hit_progress),
                    int(COLOR_DETECTOR_IDLE[2] + (COLOR_DETECTOR_HIT[2] - COLOR_DETECTOR_IDLE[2]) * hit_progress)
                )
            else:
                color = COLOR_DETECTOR_IDLE

            # Draw detector arc
            start_angle = angle - arc_angle / 2
            end_angle = angle + arc_angle / 2

            points = []
            for j in range(5):
                t = j / 4
                a = start_angle + t * (end_angle - start_angle)
                points.append((
                    center[0] + outer_radius * math.cos(a),
                    center[1] + outer_radius * math.sin(a)
                ))
            for j in range(4, -1, -1):
                t = j / 4
                a = start_angle + t * (end_angle - start_angle)
                points.append((
                    center[0] + inner_radius * math.cos(a),
                    center[1] + inner_radius * math.sin(a)
                ))

            if len(points) >= 3:
                pygame.draw.polygon(screen, color, points)

        # Draw splash effect
        if self.animation.phase == TutorialAnimation.PHASE_SPLASH:
            splash_radius = self.animation.get_splash_radius(current_time)
            splash_alpha = self.animation.get_splash_alpha(current_time)
            if splash_radius > 0 and splash_alpha > 0:
                splash_surface = pygame.Surface((int(splash_radius*2)+4, int(splash_radius*2)+4), pygame.SRCALPHA)
                pygame.draw.circle(splash_surface, (255, 200, 50, splash_alpha),
                                 (int(splash_radius)+2, int(splash_radius)+2), int(splash_radius))
                screen.blit(splash_surface,
                           (self.animation.source_pos[0] - splash_radius - 2,
                            self.animation.source_pos[1] - splash_radius - 2))

                # Draw source point
                pygame.draw.circle(screen, (255, 255, 100),
                                 (int(self.animation.source_pos[0]), int(self.animation.source_pos[1])), 5)

        # Draw photons during travel
        if self.animation.phase == TutorialAnimation.PHASE_PHOTON_TRAVEL:
            # Draw source point
            pygame.draw.circle(screen, (255, 200, 50),
                             (int(self.animation.source_pos[0]), int(self.animation.source_pos[1])), 4)

            # Draw photon 1 (if not yet hit)
            if not self.animation.detector1_hit:
                pygame.draw.circle(screen, (100, 200, 255),
                                 (int(self.animation.photon1_pos[0]), int(self.animation.photon1_pos[1])), 6)
                # Trail effect
                trail_surface = pygame.Surface((14, 14), pygame.SRCALPHA)
                pygame.draw.circle(trail_surface, (100, 200, 255, 100), (7, 7), 7)
                screen.blit(trail_surface,
                           (self.animation.photon1_pos[0] - 7, self.animation.photon1_pos[1] - 7))

            # Draw photon 2 (if not yet hit)
            if not self.animation.detector2_hit:
                pygame.draw.circle(screen, (100, 200, 255),
                                 (int(self.animation.photon2_pos[0]), int(self.animation.photon2_pos[1])), 6)
                trail_surface = pygame.Surface((14, 14), pygame.SRCALPHA)
                pygame.draw.circle(trail_surface, (100, 200, 255, 100), (7, 7), 7)
                screen.blit(trail_surface,
                           (self.animation.photon2_pos[0] - 7, self.animation.photon2_pos[1] - 7))

        # Draw LOR line when showing LOR
        if self.animation.should_show_lor():
            # Draw source point
            pygame.draw.circle(screen, (255, 200, 50),
                             (int(self.animation.source_pos[0]), int(self.animation.source_pos[1])), 5)

            # Draw LOR line
            pygame.draw.line(screen, (255, 200, 50),
                           (int(self.animation.detector1_pos[0]), int(self.animation.detector1_pos[1])),
                           (int(self.animation.detector2_pos[0]), int(self.animation.detector2_pos[1])),
                           3)

            # Draw "Line of Response" label with arrow
            lor_mid_x = (self.animation.detector1_pos[0] + self.animation.detector2_pos[0]) / 2
            lor_mid_y = (self.animation.detector1_pos[1] + self.animation.detector2_pos[1]) / 2

            # Offset label to the side
            label_offset = 60
            label_x = lor_mid_x + label_offset
            label_y = lor_mid_y - 30

            # Draw arrow pointing to LOR
            pygame.draw.line(screen, (255, 255, 100),
                           (label_x - 10, label_y + 15),
                           (lor_mid_x + 5, lor_mid_y - 5), 2)

            # Draw label
            self.renderer.draw_text(
                "Line of Response",
                (label_x + 50, label_y),
                (255, 255, 100),
                font_size="small",
                center=True
            )

        # Draw TOF probability distribution
        if self.animation.should_show_tof():
            self._draw_tof_distribution(screen, center, ring_radius)

    def _draw_tof_distribution(self, screen, center, ring_radius):
        """Draw TOF probability distribution as a violin plot along the LOR."""
        det1 = self.animation.detector1_pos
        det2 = self.animation.detector2_pos
        source = self.animation.source_pos

        # Calculate LOR direction
        lor_dx = det2[0] - det1[0]
        lor_dy = det2[1] - det1[1]
        lor_length = math.sqrt(lor_dx**2 + lor_dy**2)

        if lor_length == 0:
            return

        # Normalize direction
        dir_x = lor_dx / lor_length
        dir_y = lor_dy / lor_length

        # Perpendicular direction for violin width
        perp_x = -dir_y
        perp_y = dir_x

        # Calculate where source is along LOR (0 to 1)
        source_t = ((source[0] - det1[0]) * dir_x + (source[1] - det1[1]) * dir_y) / lor_length

        # Create violin shape points
        # The distribution is Gaussian centered on the estimated position
        # Width varies to show uncertainty
        sigma = 0.08  # Standard deviation as fraction of LOR length (sharper = better TOF resolution)
        max_width = 30  # Maximum width of violin in pixels

        num_points = 30
        left_points = []
        right_points = []

        for i in range(num_points):
            t = i / (num_points - 1)

            # Position along LOR
            pos_x = det1[0] + lor_dx * t
            pos_y = det1[1] + lor_dy * t

            # Gaussian probability
            dist_from_source = abs(t - source_t)
            probability = math.exp(-(dist_from_source ** 2) / (2 * sigma ** 2))

            # Width based on probability
            width = max_width * probability

            # Add points on both sides
            left_points.append((
                pos_x + perp_x * width,
                pos_y + perp_y * width
            ))
            right_points.append((
                pos_x - perp_x * width,
                pos_y - perp_y * width
            ))

        # Combine into closed polygon
        polygon_points = left_points + list(reversed(right_points))

        if len(polygon_points) >= 3:
            # Draw filled violin with transparency
            violin_surface = pygame.Surface((constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(violin_surface, (100, 255, 150, 80), polygon_points)
            pygame.draw.polygon(violin_surface, (100, 255, 150, 150), polygon_points, 2)
            screen.blit(violin_surface, (0, 0))

        # Draw label for TOF
        label_x = center[0] + ring_radius + 40
        label_y = center[1] + 50

        self.renderer.draw_text(
            "TOF Probability",
            (label_x, label_y),
            (100, 255, 150),
            font_size="small",
            center=False
        )
        self.renderer.draw_text(
            "Distribution",
            (label_x, label_y + 20),
            (100, 255, 150),
            font_size="small",
            center=False
        )

    def _draw_annihilation_animation(self, current_time: int):
        """Draw the zoomed-in annihilation animation."""
        screen = self.renderer.screen
        w = constants.WINDOW_WIDTH
        h = constants.WINDOW_HEIGHT

        # Animation area center (right side of screen)
        center_x = w * 0.65
        center_y = h * 0.52
        scale = min(w * 0.28, h * 0.35)  # Scale for converting normalized coords to screen

        # Draw background box for the "zoomed view"
        box_size = scale * 2.2
        box_rect = pygame.Rect(
            center_x - box_size / 2,
            center_y - box_size / 2,
            box_size,
            box_size
        )
        # Draw dark red gradient background (inside body tissue)
        self._draw_body_gradient_fast(screen, box_rect)
        pygame.draw.rect(screen, (120, 60, 70), box_rect, 2)  # Visible red border

        # Draw subtle grid lines in background (reddish tint)
        grid_color = (75, 40, 48)
        grid_spacing = box_size / 8
        for i in range(1, 8):
            # Vertical lines
            x = box_rect.left + i * grid_spacing
            pygame.draw.line(screen, grid_color, (x, box_rect.top), (x, box_rect.bottom), 1)
            # Horizontal lines
            y = box_rect.top + i * grid_spacing
            pygame.draw.line(screen, grid_color, (box_rect.left, y), (box_rect.right, y), 1)

        anim = self.annihilation_anim

        # Helper to convert normalized coords to screen
        def to_screen(nx, ny):
            return (
                int(center_x + nx * scale),
                int(center_y + ny * scale)
            )

        # Draw flash effect (behind particles)
        if anim.phase >= AnnihilationAnimation.PHASE_FLASH and anim.flash_alpha > 0:
            # Multiple concentric circles for flash effect
            flash_surface = pygame.Surface((int(box_size), int(box_size)), pygame.SRCALPHA)
            flash_center = (int(box_size / 2), int(box_size / 2))

            # Outer glow
            for r_mult in [1.0, 0.7, 0.4]:
                radius = int(anim.flash_radius * r_mult * scale / 80)
                alpha = int(anim.flash_alpha * r_mult * 0.5)
                if radius > 0 and alpha > 0:
                    pygame.draw.circle(flash_surface, (255, 255, 200, alpha),
                                     flash_center, radius)

            # Core flash
            core_radius = int(anim.flash_radius * 0.3 * scale / 80)
            if core_radius > 0:
                pygame.draw.circle(flash_surface, (255, 255, 255, min(255, anim.flash_alpha)),
                                 flash_center, max(1, core_radius))

            screen.blit(flash_surface, (box_rect.left, box_rect.top))

        # Draw particles (electron and positron) during approach phases
        if anim.phase in (AnnihilationAnimation.PHASE_POSITRON_APPROACH,
                          AnnihilationAnimation.PHASE_FINAL_APPROACH):
            # Electron (blue)
            electron_screen = to_screen(*anim.electron_pos)

            # Glow effect
            glow_surface = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (50, 100, 255, 60), (30, 30), 25)
            pygame.draw.circle(glow_surface, (80, 150, 255, 100), (30, 30), 18)
            screen.blit(glow_surface, (electron_screen[0] - 30, electron_screen[1] - 30))

            # Core
            pygame.draw.circle(screen, (100, 180, 255), electron_screen, 12)
            pygame.draw.circle(screen, (180, 220, 255), electron_screen, 6)

            # Label
            self.renderer.draw_text(
                "e-",
                (electron_screen[0], electron_screen[1] - 25),
                (150, 200, 255),
                font_size="small",
                center=True
            )

            # Positron (red)
            positron_screen = to_screen(*anim.positron_pos)

            # Glow effect
            glow_surface = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (255, 80, 80, 60), (30, 30), 25)
            pygame.draw.circle(glow_surface, (255, 120, 100, 100), (30, 30), 18)
            screen.blit(glow_surface, (positron_screen[0] - 30, positron_screen[1] - 30))

            # Core
            pygame.draw.circle(screen, (255, 100, 100), positron_screen, 12)
            pygame.draw.circle(screen, (255, 180, 180), positron_screen, 6)

            # Label
            self.renderer.draw_text(
                "e+",
                (positron_screen[0], positron_screen[1] - 25),
                (255, 150, 150),
                font_size="small",
                center=True
            )

        # Draw photons during emission phase
        if anim.phase >= AnnihilationAnimation.PHASE_PHOTONS:
            photon1_screen = to_screen(*anim.photon1_pos)
            photon2_screen = to_screen(*anim.photon2_pos)

            # Only draw if within visible area
            for photon_pos in [photon1_screen, photon2_screen]:
                if box_rect.collidepoint(photon_pos):
                    # Photon glow (yellow/gold for gamma rays)
                    glow_surface = pygame.Surface((50, 50), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surface, (255, 220, 100, 80), (25, 25), 20)
                    pygame.draw.circle(glow_surface, (255, 240, 150, 120), (25, 25), 12)
                    screen.blit(glow_surface, (photon_pos[0] - 25, photon_pos[1] - 25))

                    # Photon core
                    pygame.draw.circle(screen, (255, 255, 200), photon_pos, 8)
                    pygame.draw.circle(screen, (255, 255, 255), photon_pos, 4)

            # Draw direction arrows/trails
            angle = anim.photon_angle
            center_screen = to_screen(0, 0)

            # Draw fading trail lines
            trail_length = 40
            for photon_pos, direction in [(photon1_screen, 1), (photon2_screen, -1)]:
                if box_rect.collidepoint(photon_pos):
                    trail_end = (
                        photon_pos[0] - direction * trail_length * math.cos(angle),
                        photon_pos[1] - direction * trail_length * math.sin(angle)
                    )
                    # Gradient trail effect
                    trail_surface = pygame.Surface((int(box_size), int(box_size)), pygame.SRCALPHA)
                    pygame.draw.line(trail_surface, (255, 240, 150, 100),
                                   (photon_pos[0] - box_rect.left, photon_pos[1] - box_rect.top),
                                   (trail_end[0] - box_rect.left, trail_end[1] - box_rect.top), 4)
                    screen.blit(trail_surface, (box_rect.left, box_rect.top))

        # Draw "Zoom" label
        self.renderer.draw_text(
            "Zoomed View",
            (center_x, box_rect.top - 15),
            (120, 120, 140),
            font_size="small",
            center=True
        )

        # Draw phase label
        phase_labels = {
            AnnihilationAnimation.PHASE_POSITRON_APPROACH: "Positron approaching electron...",
            AnnihilationAnimation.PHASE_FINAL_APPROACH: "Particles attracting!",
            AnnihilationAnimation.PHASE_FLASH: "ANNIHILATION!",
            AnnihilationAnimation.PHASE_PHOTONS: "Two gamma photons emitted!",
            AnnihilationAnimation.PHASE_COMPLETE: "Two gamma photons emitted!"
        }
        if anim.phase in phase_labels:
            label_color = (255, 255, 100) if anim.phase == AnnihilationAnimation.PHASE_FLASH else (180, 180, 200)
            self.renderer.draw_text(
                phase_labels[anim.phase],
                (center_x, box_rect.bottom + 25),
                label_color,
                font_size="small",
                center=True
            )

    def _draw_injection_animation(self, current_time: int):
        """Draw the injection/distribution/decay animation."""
        screen = self.renderer.screen
        w = constants.WINDOW_WIDTH
        h = constants.WINDOW_HEIGHT

        anim = self.injection_anim

        # Animation area (right side of screen)
        center_x = w * 0.65
        center_y = h * 0.52
        box_size = min(w * 0.32, h * 0.55)

        # Draw background box
        box_rect = pygame.Rect(
            center_x - box_size / 2,
            center_y - box_size / 2,
            box_size,
            box_size
        )
        pygame.draw.rect(screen, (245, 245, 248), box_rect)  # Match main background
        pygame.draw.rect(screen, (200, 200, 210), box_rect, 2)  # Subtle border

        # Base scale for converting normalized coords
        base_scale = box_size * 0.4

        # During zoom phase, draw zooming body then fade to molecule
        if anim.phase == InjectionAnimation.PHASE_ZOOM:
            zoom_progress = (anim.zoom_level - 1.0) / 19.0  # 0 to 1

            # Create a clipped surface for the zoomed body view
            clip_surface = pygame.Surface((int(box_size), int(box_size)), pygame.SRCALPHA)
            clip_surface.fill((245, 245, 248))  # Match main background

            # Calculate zoomed view parameters
            zoom_factor = anim.zoom_level
            target_x, target_y = anim.zoom_center
            current_scale = base_scale * zoom_factor

            # The view center shifts so the target molecule moves to screen center
            clip_center_x = box_size / 2 - target_x * current_scale
            clip_center_y = box_size / 2 - target_y * current_scale

            def to_clip(nx, ny):
                return (
                    int(clip_center_x + nx * current_scale),
                    int(clip_center_y + ny * current_scale)
                )

            # Draw body and molecules on the clipped surface (fading out slowly)
            body_alpha = max(0, int(255 * (1 - zoom_progress * 1.1)))
            self._draw_body_on_surface(clip_surface, anim, current_scale, to_clip, body_alpha)

            # Blit clipped surface
            screen.blit(clip_surface, (center_x - box_size/2, center_y - box_size/2))

            # Molecule view fades in during late zoom (starts at 65%)
            if zoom_progress > 0.65:
                mol_alpha = int(255 * (zoom_progress - 0.65) / 0.35)
                self._draw_molecule_view(screen, anim, center_x, center_y, box_size, base_scale, current_time, mol_alpha)

        elif anim.phase in [InjectionAnimation.PHASE_INJECTION, InjectionAnimation.PHASE_DISTRIBUTE,
                            InjectionAnimation.PHASE_PAUSE, InjectionAnimation.PHASE_DIST_COMPLETE]:
            def to_screen(nx, ny):
                return (
                    int(center_x + nx * base_scale),
                    int(center_y + ny * base_scale)
                )
            self._draw_body_view(screen, anim, center_x, center_y, box_size, base_scale, to_screen)
        elif anim.phase in [InjectionAnimation.PHASE_VIEW, InjectionAnimation.PHASE_DECAY, InjectionAnimation.PHASE_COMPLETE]:
            self._draw_molecule_view(screen, anim, center_x, center_y, box_size, base_scale, current_time)

        # Draw phase label
        phase_labels = {
            InjectionAnimation.PHASE_INJECTION: "Injecting radiotracer...",
            InjectionAnimation.PHASE_DISTRIBUTE: "Tracer distributing in body...",
            InjectionAnimation.PHASE_PAUSE: "Tracer distributed throughout body",
            InjectionAnimation.PHASE_DIST_COMPLETE: "Tracer distributed throughout body",
            InjectionAnimation.PHASE_ZOOM: "Zooming in on FDG molecule...",
            InjectionAnimation.PHASE_VIEW: "FDG molecule with F-18 isotope",
            InjectionAnimation.PHASE_DECAY: "Radioactive decay!",
            InjectionAnimation.PHASE_COMPLETE: "Positron emitted!"
        }
        if anim.phase in phase_labels:
            label_color = (255, 255, 100) if anim.phase == InjectionAnimation.PHASE_DECAY else (180, 180, 200)
            self.renderer.draw_text(
                phase_labels[anim.phase],
                (center_x, box_rect.bottom + 25),
                label_color,
                font_size="small",
                center=True
            )

    def _draw_body_view(self, screen, anim, center_x, center_y, box_size, scale, to_screen):
        """Draw the anatomical body silhouette with injection and molecule distribution."""
        body_color = (90, 45, 55)  # Dark red for body tissue
        outline_color = (110, 60, 70)
        line_width = 2

        # Head
        head_pos = to_screen(0, -0.55)
        pygame.draw.ellipse(screen, body_color,
                           (head_pos[0] - scale*0.1, head_pos[1] - scale*0.12,
                            scale*0.2, scale*0.24))
        pygame.draw.ellipse(screen, outline_color,
                           (head_pos[0] - scale*0.1, head_pos[1] - scale*0.12,
                            scale*0.2, scale*0.24), line_width)

        # Neck
        neck_points = [
            to_screen(-0.06, -0.42), to_screen(0.06, -0.42),
            to_screen(0.08, -0.32), to_screen(-0.08, -0.32)
        ]
        pygame.draw.polygon(screen, body_color, neck_points)

        # Torso
        torso_points = [
            to_screen(-0.22, -0.32),  # Left shoulder
            to_screen(0.22, -0.32),   # Right shoulder
            to_screen(0.18, 0.25),    # Right hip
            to_screen(0.08, 0.32),    # Right groin
            to_screen(-0.08, 0.32),   # Left groin
            to_screen(-0.18, 0.25),   # Left hip
        ]
        pygame.draw.polygon(screen, body_color, torso_points)
        pygame.draw.polygon(screen, outline_color, torso_points, line_width)

        # Left arm (where injection happens)
        left_upper_arm = [
            to_screen(-0.22, -0.32), to_screen(-0.32, -0.28),
            to_screen(-0.42, -0.08), to_screen(-0.35, -0.05),
            to_screen(-0.28, -0.22), to_screen(-0.22, -0.25)
        ]
        pygame.draw.polygon(screen, body_color, left_upper_arm)
        pygame.draw.polygon(screen, outline_color, left_upper_arm, line_width)

        # Left forearm (extended for injection)
        left_forearm = [
            to_screen(-0.42, -0.08), to_screen(-0.35, -0.05),
            to_screen(-0.50, 0.12), to_screen(-0.58, 0.08)
        ]
        pygame.draw.polygon(screen, body_color, left_forearm)
        pygame.draw.polygon(screen, outline_color, left_forearm, line_width)

        # Left hand
        hand_pos = to_screen(-0.56, 0.12)
        pygame.draw.circle(screen, body_color, hand_pos, int(scale*0.05))
        pygame.draw.circle(screen, outline_color, hand_pos, int(scale*0.05), line_width)

        # Right arm
        right_upper_arm = [
            to_screen(0.22, -0.32), to_screen(0.32, -0.28),
            to_screen(0.38, -0.05), to_screen(0.30, -0.02),
            to_screen(0.26, -0.22), to_screen(0.22, -0.25)
        ]
        pygame.draw.polygon(screen, body_color, right_upper_arm)
        pygame.draw.polygon(screen, outline_color, right_upper_arm, line_width)

        # Right forearm
        right_forearm = [
            to_screen(0.38, -0.05), to_screen(0.30, -0.02),
            to_screen(0.35, 0.18), to_screen(0.42, 0.15)
        ]
        pygame.draw.polygon(screen, body_color, right_forearm)
        pygame.draw.polygon(screen, outline_color, right_forearm, line_width)

        # Right hand
        rhand_pos = to_screen(0.40, 0.20)
        pygame.draw.circle(screen, body_color, rhand_pos, int(scale*0.05))
        pygame.draw.circle(screen, outline_color, rhand_pos, int(scale*0.05), line_width)

        # Left leg
        left_leg = [
            to_screen(-0.18, 0.25), to_screen(-0.08, 0.32),
            to_screen(-0.10, 0.70), to_screen(-0.20, 0.70)
        ]
        pygame.draw.polygon(screen, body_color, left_leg)
        pygame.draw.polygon(screen, outline_color, left_leg, line_width)

        # Left foot
        lfoot = [to_screen(-0.22, 0.70), to_screen(-0.08, 0.70),
                 to_screen(-0.06, 0.76), to_screen(-0.24, 0.76)]
        pygame.draw.polygon(screen, body_color, lfoot)
        pygame.draw.polygon(screen, outline_color, lfoot, line_width)

        # Right leg
        right_leg = [
            to_screen(0.18, 0.25), to_screen(0.08, 0.32),
            to_screen(0.10, 0.70), to_screen(0.20, 0.70)
        ]
        pygame.draw.polygon(screen, body_color, right_leg)
        pygame.draw.polygon(screen, outline_color, right_leg, line_width)

        # Right foot
        rfoot = [to_screen(0.22, 0.70), to_screen(0.08, 0.70),
                 to_screen(0.06, 0.76), to_screen(0.24, 0.76)]
        pygame.draw.polygon(screen, body_color, rfoot)
        pygame.draw.polygon(screen, outline_color, rfoot, line_width)

        # Draw heart shape (actual heart)
        heart_cx, heart_cy = to_screen(-0.05, -0.05)
        heart_size = scale * 0.09

        # Create heart shape using parametric curve
        heart_points = []
        for i in range(30):
            t = i / 30 * 2 * math.pi
            # Heart parametric equations
            x = 16 * (math.sin(t) ** 3)
            y = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
            # Scale and position
            hx = heart_cx + x * heart_size / 18
            hy = heart_cy + y * heart_size / 18
            heart_points.append((hx, hy))

        pygame.draw.polygon(screen, (180, 50, 60), heart_points)  # Brighter red heart
        pygame.draw.polygon(screen, (220, 80, 90), heart_points, 2)  # Heart outline

        # Draw syringe at the left forearm during injection and distribution phases
        if anim.phase in (InjectionAnimation.PHASE_INJECTION, InjectionAnimation.PHASE_DISTRIBUTE):
            # Syringe positioned at the forearm
            inj_site = InjectionAnimation.ARM_INJECTION
            syringe_offset = -0.18 + 0.12 * anim.syringe_progress

            # Needle
            needle_start = to_screen(inj_site[0] + syringe_offset, inj_site[1])
            needle_end = to_screen(inj_site[0], inj_site[1])
            pygame.draw.line(screen, (180, 180, 190), needle_start, needle_end, 3)

            # Syringe barrel
            barrel_len = 0.18
            barrel_start = to_screen(inj_site[0] + syringe_offset, inj_site[1])
            barrel_end = to_screen(inj_site[0] + syringe_offset - barrel_len, inj_site[1])

            # Barrel body (rectangle)
            barrel_rect_points = [
                to_screen(inj_site[0] + syringe_offset - 0.02, inj_site[1] - 0.04),
                to_screen(inj_site[0] + syringe_offset - 0.02, inj_site[1] + 0.04),
                to_screen(inj_site[0] + syringe_offset - barrel_len, inj_site[1] + 0.04),
                to_screen(inj_site[0] + syringe_offset - barrel_len, inj_site[1] - 0.04),
            ]
            pygame.draw.polygon(screen, (200, 220, 240), barrel_rect_points)
            pygame.draw.polygon(screen, (150, 170, 190), barrel_rect_points, 2)

            # Liquid inside (green, decreases as plunger pushes)
            if anim.plunger_progress < 0.95:
                liquid_len = barrel_len * 0.8 * (1 - anim.plunger_progress)
                liquid_points = [
                    to_screen(inj_site[0] + syringe_offset - 0.03, inj_site[1] - 0.025),
                    to_screen(inj_site[0] + syringe_offset - 0.03, inj_site[1] + 0.025),
                    to_screen(inj_site[0] + syringe_offset - 0.03 - liquid_len, inj_site[1] + 0.025),
                    to_screen(inj_site[0] + syringe_offset - 0.03 - liquid_len, inj_site[1] - 0.025),
                ]
                pygame.draw.polygon(screen, (100, 220, 100), liquid_points)

            # Plunger
            plunger_x = inj_site[0] + syringe_offset - barrel_len + (barrel_len * 0.85 * anim.plunger_progress)
            plunger_pos = to_screen(plunger_x, inj_site[1])
            plunger_handle = to_screen(inj_site[0] + syringe_offset - barrel_len - 0.08, inj_site[1])
            pygame.draw.line(screen, (120, 120, 130), plunger_handle, plunger_pos, 5)

            # Plunger handle
            handle_rect = [
                to_screen(inj_site[0] + syringe_offset - barrel_len - 0.12, inj_site[1] - 0.03),
                to_screen(inj_site[0] + syringe_offset - barrel_len - 0.12, inj_site[1] + 0.03),
                to_screen(inj_site[0] + syringe_offset - barrel_len - 0.08, inj_site[1] + 0.03),
                to_screen(inj_site[0] + syringe_offset - barrel_len - 0.08, inj_site[1] - 0.03),
            ]
            pygame.draw.polygon(screen, (150, 150, 160), handle_rect)

        # Draw molecules following their paths
        for mol in anim.molecules:
            if mol['alpha'] > 0:
                mol_pos = to_screen(*mol['pos'])
                # All molecules shown as circles (FDG reveal happens during zoom)
                # Molecule glow
                glow_surface = pygame.Surface((24, 24), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (100, 255, 100, mol['alpha'] // 3), (12, 12), 10)
                screen.blit(glow_surface, (mol_pos[0] - 12, mol_pos[1] - 12))
                # Molecule core
                pygame.draw.circle(screen, (80, 200, 80), mol_pos, 5)
                pygame.draw.circle(screen, (150, 255, 150), mol_pos, 2)

    def _draw_body_on_surface(self, surface, anim, scale, to_screen, alpha=255):
        """Draw full body and molecules on a surface (for zoom effect)."""
        body_color = (90, 45, 55)  # Dark red for body tissue
        outline_color = (110, 60, 70)

        # Head
        head_pos = to_screen(0, -0.55)
        pygame.draw.ellipse(surface, body_color,
                           (head_pos[0] - scale*0.1, head_pos[1] - scale*0.12,
                            scale*0.2, scale*0.24))

        # Neck
        neck_points = [
            to_screen(-0.06, -0.42), to_screen(0.06, -0.42),
            to_screen(0.08, -0.32), to_screen(-0.08, -0.32)
        ]
        pygame.draw.polygon(surface, body_color, neck_points)

        # Torso
        torso_points = [
            to_screen(-0.22, -0.32), to_screen(0.22, -0.32),
            to_screen(0.18, 0.25), to_screen(0.08, 0.32),
            to_screen(-0.08, 0.32), to_screen(-0.18, 0.25),
        ]
        pygame.draw.polygon(surface, body_color, torso_points)

        # Left arm
        left_upper_arm = [
            to_screen(-0.22, -0.32), to_screen(-0.32, -0.28),
            to_screen(-0.42, -0.08), to_screen(-0.35, -0.05),
            to_screen(-0.28, -0.22), to_screen(-0.22, -0.25)
        ]
        pygame.draw.polygon(surface, body_color, left_upper_arm)
        left_forearm = [
            to_screen(-0.42, -0.08), to_screen(-0.35, -0.05),
            to_screen(-0.50, 0.12), to_screen(-0.58, 0.08)
        ]
        pygame.draw.polygon(surface, body_color, left_forearm)

        # Right arm
        right_upper_arm = [
            to_screen(0.22, -0.32), to_screen(0.32, -0.28),
            to_screen(0.38, -0.05), to_screen(0.30, -0.02),
            to_screen(0.26, -0.22), to_screen(0.22, -0.25)
        ]
        pygame.draw.polygon(surface, body_color, right_upper_arm)
        right_forearm = [
            to_screen(0.38, -0.05), to_screen(0.30, -0.02),
            to_screen(0.35, 0.18), to_screen(0.42, 0.15)
        ]
        pygame.draw.polygon(surface, body_color, right_forearm)

        # Legs
        left_leg = [
            to_screen(-0.18, 0.25), to_screen(-0.08, 0.32),
            to_screen(-0.10, 0.70), to_screen(-0.20, 0.70)
        ]
        pygame.draw.polygon(surface, body_color, left_leg)
        right_leg = [
            to_screen(0.18, 0.25), to_screen(0.08, 0.32),
            to_screen(0.10, 0.70), to_screen(0.20, 0.70)
        ]
        pygame.draw.polygon(surface, body_color, right_leg)

        # Heart
        heart_cx, heart_cy = to_screen(-0.05, -0.05)
        heart_size = scale * 0.09
        heart_points = []
        for i in range(30):
            t = i / 30 * 2 * math.pi
            x = 16 * (math.sin(t) ** 3)
            y = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
            hx = heart_cx + x * heart_size / 18
            hy = heart_cy + y * heart_size / 18
            heart_points.append((hx, hy))
        pygame.draw.polygon(surface, (180, 50, 60), heart_points)  # Brighter red heart

        # Draw molecules
        for mol in anim.molecules:
            if mol['alpha'] > 0:
                mol_pos = to_screen(*mol['pos'])
                is_target = (mol == anim.zoom_target_mol)
                mol_alpha = int(mol['alpha'] * alpha / 255)

                # All molecules drawn as circles (FDG appears when molecule view fades in)
                # Scale circle size with zoom
                circle_size = max(6, int(scale * 0.015))
                glow_size = int(circle_size * 2.5)

                glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (100, 255, 100, mol_alpha // 2),
                                   (glow_size, glow_size), glow_size)
                surface.blit(glow_surface, (mol_pos[0] - glow_size, mol_pos[1] - glow_size))
                pygame.draw.circle(surface, (80, 200, 80), mol_pos, circle_size)
                pygame.draw.circle(surface, (150, 255, 150), mol_pos, max(2, circle_size // 2))

    def _draw_body_gradient_background(self, surface, rect, alpha=255):
        """Draw a dark red gradient background representing inside the body."""
        x, y, w, h = rect.x, rect.y, rect.width, rect.height

        # Base dark red color
        base_r, base_g, base_b = 25, 12, 15

        # Create gradient with slight variations
        for i in range(int(h)):
            # Vertical gradient - slightly lighter at top
            vert_factor = 1.0 - (i / h) * 0.3

            # Add some horizontal variation using sin wave
            for j in range(int(w)):
                # Diagonal gradient component
                diag_factor = 1.0 + 0.15 * math.sin((i + j) * 0.02)
                # Radial darkening from center
                cx, cy = w / 2, h / 2
                dist = math.sqrt((j - cx)**2 + (i - cy)**2) / math.sqrt(cx**2 + cy**2)
                radial_factor = 1.0 - dist * 0.2

                factor = vert_factor * diag_factor * radial_factor
                r = max(0, min(255, int(base_r * factor)))
                g = max(0, min(255, int(base_g * factor)))
                b = max(0, min(255, int(base_b * factor)))

                if alpha < 255:
                    # For transparent drawing, we need per-pixel alpha
                    surface.set_at((int(x + j), int(y + i)), (r, g, b, alpha))
                else:
                    surface.set_at((int(x + j), int(y + i)), (r, g, b))

    def _draw_body_gradient_fast(self, surface, rect, alpha=255):
        """Draw a subtle wavy gradient representing inside body tissue."""
        x, y, w, h = int(rect.x), int(rect.y), int(rect.width), int(rect.height)

        # Create gradient surface
        grad_surf = pygame.Surface((w, h), pygame.SRCALPHA)

        # Draw wavy gradient with large color range (almost black to medium red)
        # Color range: from (12, 5, 8) to (70, 35, 42)
        for row in range(h):
            # Normalized position
            ny = row / h

            # Wavy effect using multiple sine waves
            wave1 = math.sin(ny * 3.5 + 0.5) * 0.15
            wave2 = math.sin(ny * 7.2 + 1.2) * 0.08
            wave3 = math.sin(ny * 1.8) * 0.12

            # Combined wave factor (0 to 1 range, adds variation)
            wave_factor = 0.5 + wave1 + wave2 + wave3

            # Vertical gradient base (darker at bottom)
            vert_factor = 1.0 - ny * 0.4

            # Combined factor
            factor = max(0.15, min(1.0, wave_factor * vert_factor))

            # Interpolate color from dark (12, 5, 8) to light (70, 35, 42)
            r = int(12 + (70 - 12) * factor)
            g = int(5 + (35 - 5) * factor)
            b = int(8 + (42 - 8) * factor)

            if alpha < 255:
                pygame.draw.line(grad_surf, (r, g, b, alpha), (0, row), (w, row), 1)
            else:
                pygame.draw.line(grad_surf, (r, g, b), (0, row), (w, row), 1)

        # Add subtle horizontal wave variation
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        for col in range(0, w, 3):
            nx = col / w
            # Horizontal waves
            h_wave = math.sin(nx * 5.5) * 0.5 + math.sin(nx * 2.3 + 0.7) * 0.3
            brightness = int(12 * (0.5 + h_wave * 0.5))
            pygame.draw.line(overlay, (brightness, brightness // 2, brightness // 2, 15),
                           (col, 0), (col, h), 3)

        grad_surf.blit(overlay, (0, 0))
        surface.blit(grad_surf, (int(rect.x), int(rect.y)))

    def _draw_mini_fdg(self, surface, center, size, alpha=255):
        """Draw a small FDG molecule representation."""
        cx, cy = int(center[0]), int(center[1])

        # Small hexagon
        hex_points = []
        for i in range(6):
            angle = i * math.pi / 3 - math.pi / 6
            hx = cx + size * math.cos(angle)
            hy = cy + size * math.sin(angle)
            hex_points.append((hx, hy))

        pygame.draw.polygon(surface, (50, 70, 50), hex_points)
        pygame.draw.polygon(surface, (80, 120, 80), hex_points, 1)

        # F-18 atom (green dot)
        f18_x = cx + size * 1.3 * math.cos(-math.pi / 6)
        f18_y = cy + size * 1.3 * math.sin(-math.pi / 6)

        glow_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (100, 255, 100, alpha // 2), (10, 10), 8)
        surface.blit(glow_surf, (int(f18_x) - 10, int(f18_y) - 10))
        pygame.draw.circle(surface, (50, 200, 50), (int(f18_x), int(f18_y)), 4)
        pygame.draw.circle(surface, (150, 255, 150), (int(f18_x), int(f18_y)), 2)

    def _draw_molecule_view(self, screen, anim, center_x, center_y, box_size, scale, current_time, alpha=255):
        """Draw the zoomed-in molecule view with decay."""
        # Draw dark red gradient background (inside body tissue)
        bg_rect = pygame.Rect(center_x - box_size/2, center_y - box_size/2, box_size, box_size)
        self._draw_body_gradient_fast(screen, bg_rect, alpha)

        # Molecule scale based on zoom level
        mol_scale = scale * min(anim.zoom_level / 5.0, 1.5)

        # Draw FDG-like molecule structure (simplified glucose ring)
        ring_radius = mol_scale * 0.3
        ring_center = (center_x, center_y)

        # Draw hexagonal ring (glucose backbone)
        hex_points = []
        for i in range(6):
            angle = i * math.pi / 3 - math.pi / 6
            hx = ring_center[0] + ring_radius * math.cos(angle)
            hy = ring_center[1] + ring_radius * math.sin(angle)
            hex_points.append((hx, hy))

        # Fill and outline
        pygame.draw.polygon(screen, (50, 70, 50), hex_points)
        pygame.draw.polygon(screen, (80, 120, 80), hex_points, 2)

        # Draw carbon atoms at vertices
        atom_radius = max(4, int(mol_scale * 0.06))
        for point in hex_points:
            pygame.draw.circle(screen, (60, 60, 60), (int(point[0]), int(point[1])), atom_radius)
            pygame.draw.circle(screen, (100, 100, 100), (int(point[0]), int(point[1])), atom_radius // 2)

        # Draw bonds between carbons
        for i in range(6):
            pygame.draw.line(screen, (80, 120, 80), hex_points[i], hex_points[(i+1) % 6], 2)

        # F-18 / O-18 atom position (attached to one carbon)
        f18_angle = -math.pi / 6  # Position at top-right
        f18_dist = ring_radius * 1.4
        f18_x = ring_center[0] + f18_dist * math.cos(f18_angle)
        f18_y = ring_center[1] + f18_dist * math.sin(f18_angle)

        # Bond line from ring to F-18/O-18
        bond_start = hex_points[0]  # First carbon
        pygame.draw.line(screen, (80, 120, 80), bond_start, (int(f18_x), int(f18_y)), 2)

        # Determine atom color and label based on decay state
        if anim.decay_complete:
            # O-18 (oxygen) - red/orange color
            atom_color = (200, 80, 50)
            atom_highlight = (255, 150, 120)
            atom_label = "O-18"
            label_color = (255, 150, 120)
            glow_color = (255, 100, 80)
        else:
            # F-18 (fluorine) - green color
            atom_color = (50, 200, 50)
            atom_highlight = (150, 255, 150)
            atom_label = "F-18"
            label_color = (150, 255, 150)
            glow_color = (100, 255, 100)

        # Glow effect - intensified during flashing
        base_glow = 80
        if anim.f18_flash_intensity > 0:
            glow_alpha = int(base_glow + 175 * anim.f18_flash_intensity)
        else:
            glow_alpha = base_glow

        glow_size = int(mol_scale * 0.35)
        glow_surface = pygame.Surface((glow_size*2, glow_size*2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (*glow_color, glow_alpha), (glow_size, glow_size), glow_size)
        screen.blit(glow_surface, (f18_x - glow_size, f18_y - glow_size))

        # Draw the F-18 or O-18 atom
        atom_size = max(8, int(mol_scale * 0.12))
        pygame.draw.circle(screen, atom_color, (int(f18_x), int(f18_y)), atom_size)
        pygame.draw.circle(screen, atom_highlight, (int(f18_x), int(f18_y)), atom_size // 2)

        # Label
        self.renderer.draw_text(
            atom_label,
            (f18_x, f18_y - atom_size - 12),
            label_color,
            font_size="small",
            center=True
        )

        # Draw positron being ejected
        if anim.positron_ejected:
            # Use shared exit angle to connect with annihilation animation
            eject_angle = InjectionAnimation.POSITRON_EXIT_ANGLE
            # Travel distance increases to exit screen (box_size ensures off-screen)
            eject_dist = anim.positron_progress * box_size * 1.5

            positron_x = f18_x + eject_dist * math.cos(eject_angle)
            positron_y = f18_y + eject_dist * math.sin(eject_angle)

            # Positron glow
            p_glow_size = int(mol_scale * 0.2)
            glow_surface = pygame.Surface((p_glow_size*2, p_glow_size*2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (255, 80, 80, 120), (p_glow_size, p_glow_size), p_glow_size)
            screen.blit(glow_surface, (positron_x - p_glow_size, positron_y - p_glow_size))

            # Positron core
            p_size = max(6, int(mol_scale * 0.08))
            pygame.draw.circle(screen, (255, 100, 100), (int(positron_x), int(positron_y)), p_size)
            pygame.draw.circle(screen, (255, 180, 180), (int(positron_x), int(positron_y)), p_size // 2)

            # Label
            self.renderer.draw_text(
                "e+",
                (positron_x, positron_y - p_size - 10),
                (255, 150, 150),
                font_size="small",
                center=True
            )

            # Trail effect
            for i in range(3):
                trail_dist = eject_dist - (i + 1) * 15
                if trail_dist > 0:
                    tx = f18_x + trail_dist * math.cos(eject_angle)
                    ty = f18_y + trail_dist * math.sin(eject_angle)
                    trail_alpha = max(0, min(255, 80 - i * 25))
                    trail_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
                    pygame.draw.circle(trail_surf, (255, 100, 100, trail_alpha), (8, 8), max(1, 6 - i))
                    screen.blit(trail_surf, (int(tx) - 8, int(ty) - 8))

            # Small flash at emission point
            if anim.positron_progress < 0.3:
                flash_alpha = max(0, min(255, int(200 * (1 - anim.positron_progress / 0.3))))
                flash_surface = pygame.Surface((40, 40), pygame.SRCALPHA)
                pygame.draw.circle(flash_surface, (255, 255, 200, flash_alpha), (20, 20), 15)
                screen.blit(flash_surface, (int(f18_x) - 20, int(f18_y) - 20))
