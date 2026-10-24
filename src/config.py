"""
config.py
EP Team Statcast Review -- rules FROZEN before looking at results.

Decision question
    Which teams scored (or allowed) more or fewer runs-value than the quality of
    their contact says they should, and does that gap repeat the next season?
    gap = wOBA - xwOBA   (offense)        gap = wOBA against - xwOBA against   (pitching)

CONFIRMED rule (per side, offense and pitching, evaluated separately)
    Pearson r between the 2025 gap and the 2026 gap across the 30 teams must be
    at least MIN_R, and the 95% bootstrap CI (resampling teams) must be above zero.
    Otherwise: NOT CONFIRMED (a null result), published anyway.
Secondary, descriptive only: split-half persistence inside each season; which of
last year's wOBA or xwOBA predicts this year's wOBA better.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "outputs"

SEASONS = {
    2025: {"start": "2025-03-27", "end": "2025-09-28"},
    2026: {"start": "2026-03-26", "end": "2026-09-27"},
}
PRIOR_YEAR, CURRENT_YEAR = 2025, 2026
CHUNK_DAYS = 10

NEEDED_COLUMNS = [
    "game_date", "game_type", "home_team", "away_team", "inning_topbot",
    "pitch_type", "release_speed", "description", "zone", "events",
    "bat_speed", "swing_length", "launch_speed", "launch_speed_angle",
    "woba_value", "woba_denom", "estimated_woba_using_speedangle",
]

SWING_DESCRIPTIONS = {"swinging_strike", "swinging_strike_blocked", "foul", "foul_tip", "hit_into_play"}
WHIFF_DESCRIPTIONS = {"swinging_strike", "swinging_strike_blocked"}
FASTBALL_TYPES = {"FF", "SI", "FC"}
STRIKEOUT_EVENTS = {"strikeout", "strikeout_double_play"}
WALK_EVENTS = {"walk", "intent_walk"}
HARD_HIT_MPH = 95.0
BARREL_CODE = 6
COMPETITIVE_QUANTILE = 0.10      # bat speed: drop the slowest 10% of swings of the team-season

TEAM_ALIASES = {"OAK": "ATH"}    # same franchise, different code across seasons

MIN_R = 0.30                     # practical floor for CONFIRMED
BOOTSTRAP_B = 2000
SEED = 2026
