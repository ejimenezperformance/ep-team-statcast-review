"""
run_team_analysis.py
Runs the frozen test on real data (after data_loader.py for 2025 and 2026).

Run:  python src/run_team_analysis.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

import config as C
from data_loader import load_season
from metrics import add_teams, team_table, halves, by_venue
from persistence import persistence, confirmed, compare_predictors
from plots import persistence_chart, park_chart
from cards import build_cards, cards_markdown


def analyze(off_prior, off_cur, pit_prior, pit_cur) -> dict:
    """The frozen year-to-year test on four team tables (used on real and synthetic data)."""
    out = {}
    for side, a, b in (("offense", off_prior, off_cur), ("pitching", pit_prior, pit_cur)):
        teams = a.index.intersection(b.index)
        a, b = a.loc[teams], b.loc[teams]
        gap = persistence(a["gap"], b["gap"])
        out[side] = {"teams": list(teams), "x": a["gap"].to_numpy(float), "y": b["gap"].to_numpy(float),
                     "gap": gap, "confirmed": confirmed(gap),
                     "xwoba_r": persistence(a["xwoba"], b["xwoba"])["r"],
                     "woba_r": persistence(a["woba"], b["woba"])["r"],
                     "predictor": compare_predictors(a["woba"], a["xwoba"], b["woba"])}
    return out


def split_half(df: pd.DataFrame) -> dict:
    """First half vs second half of ONE season (same rosters, mostly)."""
    d = add_teams(df)
    h1, h2 = halves(d)
    res = {}
    for side in ("offense", "pitching"):
        a, b = team_table(h1, side), team_table(h2, side)
        res[side] = persistence(a["gap"], b["gap"])
    return res


def park_check(raw_prior: pd.DataFrame, raw_cur: pd.DataFrame, drop=("COL", "ATH")) -> dict:
    """EXPLORATORY (decided after seeing the main result). Is the persistent gap a ballpark effect?
    Road games are played in other teams' parks, so a team's own park drops out of its road gap.
    Home-only and road-only use the same number of games, so they are comparable."""
    out = {}
    for side in ("offense", "pitching"):
        row = {}
        for venue in ("home", "road"):
            a = team_table(add_teams(by_venue(raw_prior, side, venue)), side)
            b = team_table(add_teams(by_venue(raw_cur, side, venue)), side)
            teams = a.index.intersection(b.index)
            row[venue] = persistence(a.loc[teams, "gap"], b.loc[teams, "gap"])
        a = team_table(add_teams(raw_prior), side); b = team_table(add_teams(raw_cur), side)
        teams = [t for t in a.index.intersection(b.index) if t not in drop]
        row["without_" + "_".join(drop)] = persistence(a.loc[teams, "gap"], b.loc[teams, "gap"])
        out[side] = row
    return out


def main():
    C.OUT_DIR.mkdir(exist_ok=True)
    raw = {y: load_season(y) for y in (C.PRIOR_YEAR, C.CURRENT_YEAR)}
    tabs = {}
    for y in raw:
        d = add_teams(raw[y])
        for side in ("offense", "pitching"):
            t = team_table(d, side)
            t.to_csv(C.OUT_DIR / f"team_{side}_{y}.csv", encoding="utf-8")
            tabs[(side, y)] = t
    res = analyze(tabs[("offense", C.PRIOR_YEAR)], tabs[("offense", C.CURRENT_YEAR)],
                  tabs[("pitching", C.PRIOR_YEAR)], tabs[("pitching", C.CURRENT_YEAR)])

    lines = [f"=== Teams: {len(res['offense']['teams'])} offense, {len(res['pitching']['teams'])} pitching ==="]
    for side in ("offense", "pitching"):
        r = res[side]; g = r["gap"]
        lines.append(f"--- {side.upper()} ---")
        lines.append(f"gap persistence {C.PRIOR_YEAR}->{C.CURRENT_YEAR}: r={g['r']:+.2f} [95% CI {g['ci_low']:+.2f}, {g['ci_high']:+.2f}] "
                     f"spearman={g['spearman']:+.2f} slope={g['slope']:+.2f} [{g['slope_low']:+.2f}, {g['slope_high']:+.2f}]")
        lines.append(f"benchmarks: xwOBA r={r['xwoba_r']:+.2f}   wOBA r={r['woba_r']:+.2f}")
        p = r["predictor"]
        lines.append(f"predict {C.CURRENT_YEAR} wOBA: RMSE from last wOBA={p['rmse_woba_pred']:.4f}, from last xwOBA={p['rmse_xwoba_pred']:.4f}, "
                     f"gain={p['gain_xwoba_over_woba']:+.4f} [{p['ci_low']:+.4f}, {p['ci_high']:+.4f}]")
        lines.append(f"VERDICT ({side}): {'CONFIRMED' if r['confirmed'] else 'NOT CONFIRMED (null result)'}")
    lines.append("=== Split-half inside each season (secondary, descriptive) ===")
    for y in raw:
        sh = split_half(raw[y])
        for side in ("offense", "pitching"):
            g = sh[side]
            lines.append(f"{y} {side}: r={g['r']:+.2f} [{g['ci_low']:+.2f}, {g['ci_high']:+.2f}]")
    lines.append("=== EXPLORATORY (decided after seeing the main result): is the gap a ballpark effect? ===")
    pc = park_check(raw[C.PRIOR_YEAR], raw[C.CURRENT_YEAR])
    for side in ("offense", "pitching"):
        for k, g in pc[side].items():
            lines.append(f"{side} {k}: r={g['r']:+.2f} [{g['ci_low']:+.2f}, {g['ci_high']:+.2f}] spearman={g['spearman']:+.2f} n={g['n']}")
    text = "\n".join(lines)
    (C.OUT_DIR / "summary.txt").write_text(text + "\n", encoding="utf-8")

    panels = {s: (res[s]["teams"], res[s]["x"], res[s]["y"], res[s]["gap"], res[s]["confirmed"])
              for s in ("offense", "pitching")}
    for lang in ("en", "es"):
        persistence_chart(panels, C.OUT_DIR / f"team_gap_persistence_{lang.upper()}.png", lang)

    for lang in ("en", "es"):
        park_chart(pc, C.OUT_DIR / f"team_gap_home_vs_road_{lang.upper()}.png", lang)

    cards = build_cards(tabs[("offense", C.CURRENT_YEAR)], tabs[("pitching", C.CURRENT_YEAR)])
    cards.to_csv(C.OUT_DIR / f"team_cards_{C.CURRENT_YEAR}.csv", encoding="utf-8")
    ro, rp = res["offense"]["gap"], res["pitching"]["gap"]
    note_en = (f"Year-to-year persistence of the results-minus-contact-quality gap: offense r={ro['r']:+.2f}, pitching r={rp['r']:+.2f} "
               f"(see README before reading a gap as a skill).")
    note_es = (f"Persistencia año a año de la diferencia entre resultados y calidad de contacto: ofensiva r={ro['r']:+.2f}, pitcheo r={rp['r']:+.2f} "
               f"(lee el README antes de interpretar una diferencia como habilidad).")
    (C.OUT_DIR / f"team_cards_{C.CURRENT_YEAR}.md").write_text(
        cards_markdown(cards, C.CURRENT_YEAR, note_en, note_es), encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
