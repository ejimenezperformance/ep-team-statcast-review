"""
metrics.py
Team-season tables from pitch-level Statcast rows.

Statcast has no "batting team" column. It is derived from the half-inning:
  top of the inning    -> the AWAY team bats, the HOME team fields
  bottom of the inning -> the HOME team bats, the AWAY team fields
"""
import numpy as np
import pandas as pd

from config import (SWING_DESCRIPTIONS, WHIFF_DESCRIPTIONS, FASTBALL_TYPES, STRIKEOUT_EVENTS,
                    WALK_EVENTS, HARD_HIT_MPH, BARREL_CODE, COMPETITIVE_QUANTILE, TEAM_ALIASES)


def add_teams(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    top = d["inning_topbot"].astype(str).str.lower().str.startswith("top")
    d["batting_team"] = np.where(top, d["away_team"], d["home_team"])
    d["fielding_team"] = np.where(top, d["home_team"], d["away_team"])
    for c in ("batting_team", "fielding_team"):
        d[c] = d[c].replace(TEAM_ALIASES)
    return d


def _side_metrics(g: pd.DataFrame, side: str) -> dict:
    pa = g[g["woba_denom"].fillna(0) > 0]
    n_pa = len(pa)
    out = {"pa": n_pa}
    if n_pa == 0:
        return out
    out["woba"] = float(pa["woba_value"].sum() / pa["woba_denom"].sum())
    xw = pa["estimated_woba_using_speedangle"].where(pa["estimated_woba_using_speedangle"].notna(), pa["woba_value"])
    out["xwoba"] = float(xw.mean())
    out["gap"] = out["woba"] - out["xwoba"]
    ev = pa["events"].astype(str)
    out["k_pct"] = float(ev.isin(STRIKEOUT_EVENTS).mean())
    out["bb_pct"] = float(ev.isin(WALK_EVENTS).mean())

    bbe = g[g["launch_speed"].notna()]
    out["bbe"] = len(bbe)
    if len(bbe):
        out["barrel_pct"] = float((bbe["launch_speed_angle"] == BARREL_CODE).mean())
        out["hard_hit_pct"] = float((bbe["launch_speed"] >= HARD_HIT_MPH).mean())

    swings = g["description"].isin(SWING_DESCRIPTIONS)
    if swings.sum():
        out["whiff_pct"] = float(g.loc[swings, "description"].isin(WHIFF_DESCRIPTIONS).mean())
    outside = g["zone"].notna() & (g["zone"] >= 11)
    if outside.sum():
        out["chase_pct"] = float(swings[outside].mean())

    if side == "offense":
        sw = g[g["bat_speed"].notna() & swings]
        if len(sw):
            sw = sw[sw["bat_speed"] >= sw["bat_speed"].quantile(COMPETITIVE_QUANTILE)]
            out["bat_speed"] = float(sw["bat_speed"].mean())
            out["swing_length"] = float(sw["swing_length"].mean())
    else:
        ff = g[(g["pitch_type"] == "FF") & g["release_speed"].notna()]
        if len(ff):
            out["ff_velo"] = float(ff["release_speed"].mean())
    return out


def team_table(df: pd.DataFrame, side: str) -> pd.DataFrame:
    """One row per team. side = 'offense' (grouped by batting team) or 'pitching' (by fielding team)."""
    col = "batting_team" if side == "offense" else "fielding_team"
    rows = {team: _side_metrics(g, side) for team, g in df.groupby(col)}
    return pd.DataFrame(rows).T.rename_axis("team")


def halves(df: pd.DataFrame):
    """Split a season at the median game date (first half, second half)."""
    cut = df["game_date"].sort_values().iloc[len(df) // 2]
    return df[df["game_date"] < cut], df[df["game_date"] >= cut]


def by_venue(df: pd.DataFrame, side: str, venue: str) -> pd.DataFrame:
    """Keep only pitches where the team of interest plays at HOME or on the ROAD.
    offense: a team bats at home in the bottom of the inning; pitching: it fields at home in the top."""
    top = df["inning_topbot"].astype(str).str.lower().str.startswith("top")
    team_at_home = (~top) if side == "offense" else top
    return df[team_at_home] if venue == "home" else df[~team_at_home]
