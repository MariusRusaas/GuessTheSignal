"""Game constants and configuration."""

# Window settings
# These are default/fallback values - actual size is calculated from screen
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 900
WINDOW_SCALE = 0.80  # Use 80% of screen size
FPS = 60

# Colors - Light theme
COLOR_BACKGROUND = (245, 245, 248)  # Almost white with hint of grey
COLOR_GRID = (40, 40, 50)  # Original dark grid
COLOR_DETECTOR_IDLE = (80, 80, 90)  # Original dark detectors
COLOR_DETECTOR_HIT = (0, 200, 80)  # Green hit
COLOR_SHAPE_TRUE = (70, 130, 180)  # Steel blue
COLOR_SHAPE_GUESSED = (200, 100, 100, 150)
COLOR_SHAPE_CORRECT = (80, 180, 80, 200)
COLOR_SHAPE_WRONG = (200, 50, 50, 150)
COLOR_LOR_LINE = (230, 160, 30, 200)  # Orange-gold
COLOR_PROBABILITY_ZONE = (255, 220, 80, 100)
COLOR_TEXT = (40, 40, 50)  # Dark text
COLOR_TEXT_HIGHLIGHT = (180, 120, 0)  # Dark gold/amber for highlights
COLOR_BUTTON = (100, 130, 180)  # Blue-grey buttons
COLOR_BUTTON_HOVER = (120, 150, 200)
COLOR_BUTTON_TEXT = (255, 255, 255)  # White button text

# Difficulty presets - all use 64 detectors, only matrix size varies
DIFFICULTY_SETTINGS = {
    "Very Easy": {
        "grid_size": 10,
        "detectors": 64,
        "shape_type": "blob",
        "description": "Simple blob shape, 10x10 grid"
    },
    "Easy": {
        "grid_size": 14,
        "detectors": 64,
        "shape_type": "kidney",
        "description": "Kidney shape, 14x14 grid"
    },
    "Medium": {
        "grid_size": 18,
        "detectors": 64,
        "shape_type": "liver",
        "description": "Liver shape, 18x18 grid"
    },
    "Hard": {
        "grid_size": 24,
        "detectors": 64,
        "shape_type": "heart",
        "description": "Heart shape, 24x24 grid"
    },
    "Expert": {
        "grid_size": 32,
        "detectors": 64,
        "shape_type": "multi",
        "description": "Multiple regions, 32x32 grid"
    }
}

DIFFICULTY_ORDER = ["Very Easy", "Easy", "Medium", "Hard", "Expert"]

# Game mechanics
DETECTOR_RING_RADIUS_RATIO = 0.42  # Ratio of game area
MATRIX_SIZE_RATIO = 0.55  # Ratio of game area for matrix
DETECTOR_ARC_ANGLE = 4  # Degrees per detector arc (smaller for 64 detectors)
DETECTOR_BLINK_DURATION = 600  # ms
TOF_TIMING_SCALE = 400  # ms per unit distance difference
TOF_MIN_DELAY = 50  # Minimum delay between blinks (ms) - small for center signals
TOF_MAX_DELAY = 500  # Maximum delay between blinks (ms) - faster overall

# Animation
BLINK_FADE_STEPS = 10
LOR_LINE_WIDTH = 2
EMISSION_INTERVAL = 2500  # ms between automatic emissions

# UI Layout
MENU_BUTTON_WIDTH = 300
MENU_BUTTON_HEIGHT = 60
MENU_BUTTON_SPACING = 20
HUD_HEIGHT = 80
HUD_PADDING = 20
