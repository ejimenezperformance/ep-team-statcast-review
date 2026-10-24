"""
sim.py -- synthetic leagues with KNOWN truth, to test the pipeline in both directions.

Each team has a true gap (results minus contact quality).
  persist = 1 -> the gap is a stable team trait (nothing changes year to year)
  persist = 0 -> the gap is pure luck, redrawn each season
Observed season gaps carry sampling noise like a real ~6,200-PA season.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np
import pandas as pd

TEAMS = [f"T{i:02d}" for i in range(30)]
SD_TRUE_GAP = 0.008
SD_NOISE_GAP = 0.007
SD_SKILL = 0.012


def _gap_pair(rng, persist):
    base = rng.normal(0, SD_TRUE_GAP, 30)
    g1 = np.sqrt(persist) * base + np.sqrt(1 - persist) * rng.normal(0, SD_TRUE_GAP, 30)
    g2 = np.sqrt(persist) * base + np.sqrt(1 - persist) * rng.normal(0, SD_TRUE_GAP, 30)
    return g1, g2


def make_gap_arrays(seed, persist):
    """(observed gap year 1, observed gap year 2) for one side, 30 teams."""
    rng = np.random.default_rng(seed)
    g1, g2 = _gap_pair(rng, persist)
    return g1 + rng.normal(0, SD_NOISE_GAP, 30), g2 + rng.normal(0, SD_NOISE_GAP, 30)


def _table(skill, gap_true, rng):
    xw = 0.315 + skill
    gap = gap_true + rng.normal(0, SD_NOISE_GAP, 30)
    return pd.DataFrame({"xwoba": xw, "woba": xw + gap, "gap": gap}, index=TEAMS)


def make_team_tables(seed, persist):
    """off_prior, off_cur, pit_prior, pit_cur as the real pipeline would produce them."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(2):                                   # offense, pitching
        skill = rng.normal(0, SD_SKILL, 30)
        g1, g2 = _gap_pair(rng, persist)
        s2 = 0.7 * skill + 0.3 * rng.normal(0, SD_SKILL, 30)
        out.append((_table(skill, g1, rng), _table(s2, g2, rng)))
    return out[0][0], out[0][1], out[1][0], out[1][1]


def make_raw(seed, start, end, persist_gap_off=None, n_pa=30000, n_other=15000):
    """Pitch-level rows with the Statcast columns the loader keeps. Returns (df, truth)."""
    rng = np.random.default_rng(seed)
    gap_off = rng.normal(0, SD_TRUE_GAP, 30) if persist_gap_off is None else persist_gap_off
    gap_pit = rng.normal(0, SD_TRUE_GAP, 30)
    skill_off, skill_pit = rng.normal(0, SD_SKILL, 30), rng.normal(0, SD_SKILL, 30)
    span = (pd.Timestamp(end) - pd.Timestamp(start)).days + 1
    b = rng.integers(0, 30, n_pa)
    f = (b + rng.integers(1, 30, n_pa)) % 30
    top = rng.random(n_pa) < 0.5
    t = np.array(TEAMS)
    home = np.where(top, t[f], t[b]); away = np.where(top, t[b], t[f])
    xw_true = 0.315 + skill_off[b] - skill_pit[f] * 0.0
    woba_v = xw_true + gap_off[b] + gap_pit[f] + rng.normal(0, 0.5, n_pa)
    xw_v = xw_true + rng.normal(0, 0.3, n_pa)
    pa = pd.DataFrame({
        "game_date": pd.Timestamp(start) + pd.to_timedelta(rng.integers(0, span, n_pa), unit="D"),
        "game_type": "R", "home_team": home, "away_team": away,
        "inning_topbot": np.where(top, "Top", "Bot"),
        "pitch_type": "FF", "release_speed": 94 + rng.normal(0, 2, n_pa), "description": "hit_into_play",
        "zone": rng.integers(1, 15, n_pa), "events": rng.choice(["single", "strikeout", "walk", "field_out"], n_pa),
        "bat_speed": np.nan, "swing_length": np.nan,
        "launch_speed": 88 + rng.normal(0, 12, n_pa), "launch_speed_angle": rng.integers(1, 7, n_pa),
        "woba_value": woba_v, "woba_denom": 1.0, "estimated_woba_using_speedangle": xw_v})
    n = n_other
    bo = rng.integers(0, 30, n); fo = (bo + rng.integers(1, 30, n)) % 30
    topo = rng.random(n) < 0.5
    other = pd.DataFrame({
        "game_date": pd.Timestamp(start) + pd.to_timedelta(rng.integers(0, span, n), unit="D"),
        "game_type": "R", "home_team": np.where(topo, t[fo], t[bo]), "away_team": np.where(topo, t[bo], t[fo]),
        "inning_topbot": np.where(topo, "Top", "Bot"), "pitch_type": "FF",
        "release_speed": 94 + rng.normal(0, 2, n),
        "description": rng.choice(["foul", "swinging_strike", "ball", "called_strike"], n),
        "zone": rng.integers(1, 15, n), "events": None,
        "bat_speed": 71 + rng.normal(0, 4, n), "swing_length": 7.2 + rng.normal(0, 0.4, n),
        "launch_speed": np.nan, "launch_speed_angle": np.nan,
        "woba_value": np.nan, "woba_denom": np.nan, "estimated_woba_using_speedangle": np.nan})
    return pd.concat([pa, other], ignore_index=True), {"gap_off": gap_off, "gap_pit": gap_pit}
