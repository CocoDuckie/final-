"""
config.py — Constants and theme for the bias simulation game (v9 plan).

All thresholds, capital, colors, and scoring caps live here.
Variable names follow "Key.Common variables" in PROJECT_PLAN_NHA408E-v9.xlsx.
"""

from pathlib import Path

# ──────────────────────────────────────────────────────────────────────
# GAME PARAMETERS
# ──────────────────────────────────────────────────────────────────────
GAME_NAME = "FOMOPOLY"
COURSE_CODE = "NHA408E"
STARTING_CAPITAL = 100_000          # 100,000 USD
STARTING_PRICE = 100.0
NUM_ROUNDS = 8
ASSET_NAME = "STEELSTOX"
CURRENCY = "USD"
SKIP_ROUND_QUESTIONS = False        # testing shortcut; set True to skip quizzes

# ──────────────────────────────────────────────────────────────────────
# TRADE SIZE — categorical → numeric mapping
# ──────────────────────────────────────────────────────────────────────
# (size_level, percentage commitment)
# BUY uses % of cash; SELL uses % of holdings; HOLD has no size (trade_size = "none")
TRADE_SIZE_MAP = {
    "none":   (0, 0.00),
    "small":  (1, 0.25),
    "medium": (2, 0.50),
    "high":   (3, 0.75),
    "all_in": (4, 1.00),
}

TRADE_SIZE_LABELS = {
    "small":  "Small (25%)",
    "medium": "Medium (50%)",
    "high":   "High (75%)",
    "all_in": "All-in (100%)",
}

# ──────────────────────────────────────────────────────────────────────
# BIAS SCORING — v2 anti-double-counting architecture
# ──────────────────────────────────────────────────────────────────────
ROUND_SCORE_CAP = 3                 # max per bias per round
GAME_SCORE_CAP = 8                  # max per bias for whole game
DISPOSITION_GAME_CAP = 3            # special cap per "4. Bias Detection Logic" sheet

# Severity tier — (min_score, max_score, label)
BIAS_TIERS = [
    (0, 0, "None"),
    (1, 2, "Mild"),
    (3, 4, "Moderate"),
    (5, 6, "Strong"),
    (7, GAME_SCORE_CAP, "Very Strong"),
]

BIAS_NAMES = [
    "Overconfidence",
    "Herding",
    "Availability",
    "Framing",
    "Loss Aversion",
    "Disposition Effect",
]

# Plan-final scoring: avg_size_level is mean over all 8 rounds, with hold = 0.
OC_AVG_SIZE_THRESHOLD = 1.8
OC_NUM_TRADES_THRESHOLD = 6

# ──────────────────────────────────────────────────────────────────────
# FILE PATHS
# ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

SCENARIO_CSV = DATA_DIR / "scenarios.csv"
LEADERBOARD_CSV = LOGS_DIR / "leaderboard.csv"

# ──────────────────────────────────────────────────────────────────────
# CHART OPTIONS — TradingView-style animated candlestick
# ──────────────────────────────────────────────────────────────────────
CANDLES_PER_ROUND = 7               # one daily candle per trading day in each week
FRAME_DURATION_MS = 360             # ~2.5s per weekly animation
CANDLE_VOLATILITY = 0.7             # body swing magnitude
CANDLE_WICK_RANGE = 0.5             # wick extension
# Per-round volatility scaling based on media_intensity (1..5)
VOLATILITY_BY_INTENSITY = {1: 0.5, 2: 0.7, 3: 1.0, 4: 1.4, 5: 1.8}
CANDLE_GREEN = "#10B981"
CANDLE_RED = "#EF4444"
RANDOM_SEED = 42                    # default chart seed

# ──────────────────────────────────────────────────────────────────────
# UI THEME
# ──────────────────────────────────────────────────────────────────────
COLOR_PRIMARY = "#1A3558"
COLOR_ACCENT = "#5C3399"
COLOR_SUCCESS = "#10B981"
COLOR_DANGER = "#EF4444"
COLOR_WARNING = "#F59E0B"
COLOR_NEUTRAL = "#6B7280"
COLOR_BG = "#F9FAFB"


def tier_for(score: int) -> str:
    """Map a final bias score to a severity tier label."""
    for lo, hi, label in BIAS_TIERS:
        if lo <= score <= hi:
            return label
    return "Very Strong"
