import os

# ── Tesseract ────────────────────────────────────────────────────────────────
# Override with TESSERACT_PATH env var, otherwise fall back to the default
# Windows install location.
TESSERACT_PATH = os.environ.get(
    "TESSERACT_PATH",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# ── Database ─────────────────────────────────────────────────────────────────
# Set DATABASE_URL in a .env file next to this script (or in your shell).
# Example: postgresql://user:pass@localhost:5432/dnd_market
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# ── Screen layout ─────────────────────────────────────────────────────────────
# Column regions (x offset from screen left, width in pixels).
# Run option 1 (calibrate) from main.py to update these for your resolution.
COLUMNS = {
    "item_name":       {"x": 53,   "width": 265},
    "rarity":          {"x": 318,  "width": 187},
    "slot":            {"x": 505,  "width": 191},
    "type":            {"x": 696,  "width": 189},
    "static_attribute":{"x": 885,  "width": 190},
    "random_attribute":{"x": 1075, "width": 187},
    "expires":         {"x": 1262, "width": 188},
    "price":           {"x": 1450, "width": 116},
    "quantity":        {"x": 1556, "width": 150},
}

FIRST_ROW_Y    = 328
ROW_HEIGHT     = 59
NUM_VISIBLE_ROWS = 10

# Refresh button screen coordinates
REFRESH_BUTTON_X = 1791
REFRESH_BUTTON_Y = 30

# ── Rarity color map (BGR) ────────────────────────────────────────────────────
RARITY_COLORS = {
    "Poor":      (128, 128, 128),
    "Common":    (255, 255, 255),
    "Uncommon":  (0,   255, 0),
    "Rare":      (255, 120, 0),
    "Epic":      (128, 0,   128),
    "Legendary": (0,   165, 255),
}

OCR_CONFIDENCE_THRESHOLD = 40
DEBUG_FOLDER = "debug_images"
