"""
test_team_review.py -- run with:  python tests/test_team_review.py
Plain checks (no pytest needed). Everything runs on synthetic data with known truth.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

import numpy as np
import pandas as pd

import config as C
from data_loader import chunk_ranges, slim
from metrics import add_teams, team_table, halves, by_venue
from persistence import persistence, confirmed, compare_predictors
from run_team_analysis import analyze, split_half, park_check
from cards import build_cards
import sim

PASSED, FAILED = 0, []


def check(name, cond, detail=""):
    global PASSED
    if cond:
        PASSED += 1
        print(f"  ok   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} {detail}")


print("1. loader")
check("1a chunks cover the range", chunk_ranges("2026-03-26", "2026-04-14", 10) ==
      [("2026-03-26", "2026-04-04"), ("2026-04-05", "2026-04-14")])
tiny = pd.DataFrame({c: [1, 1] for c in C.NEEDED_COLUMNS}); tiny["game_type"] = ["R", "S"]
check("1b slim keeps regular season only", len(slim(tiny)) == 1)

print("2. batting and fielding team")
d = pd.DataFrame({"home_team": ["NYY", "OAK"], "away_team": ["BOS", "SEA"], "inning_topbot": ["Top", "Bot"]})
d = add_teams(d)
check("2a top of the inning: away bats, home fields", (d.loc[0, "batting_team"], d.loc[0, "fielding_team"]) == ("BOS", "NYY"))
check("2b bottom: home bats, away fields; OAK mapped to ATH", (d.loc[1, "batting_team"], d.loc[1, "fielding_team"]) == ("ATH", "SEA"))

print("3. team metrics by hand")
rows = []
def pitch(**k):
    base = dict(game_date=pd.Timestamp("2026-04-01"), game_type="R", home_team="H", away_team="A",
                inning_topbot="Top", pitch_type="SL", release_speed=85.0, description="ball", zone=5, events=None,
                bat_speed=np.nan, swing_length=np.nan, launch_speed=np.nan, launch_speed_angle=np.nan,
                woba_value=np.nan, woba_denom=np.nan, estimated_woba_using_speedangle=np.nan)
    base.update(k); return base
rows += [pitch(woba_value=0.9, woba_denom=1, events="single", launch_speed=100.0, launch_speed_angle=6,
               estimated_woba_using_speedangle=0.5, description="hit_into_play"),
         pitch(woba_value=0.0, woba_denom=1, events="strikeout", description="swinging_strike", zone=12),
         pitch(woba_value=0.7, woba_denom=1, events="walk"),
         pitch(woba_value=0.0, woba_denom=1, events="field_out", launch_speed=80.0, launch_speed_angle=3,
               estimated_woba_using_speedangle=0.1, description="hit_into_play"),
         pitch(description="foul", zone=13),
         pitch(description="called_strike", zone=14),
         pitch(pitch_type="FF", release_speed=95.0), pitch(pitch_type="FF", release_speed=97.0)]
t = team_table(add_teams(pd.DataFrame(rows)), "offense").loc["A"]
check("3a wOBA = sum(woba_value) / sum(woba_denom)", abs(t["woba"] - 1.6 / 4) < 1e-9, str(t["woba"]))
check("3b xwOBA uses the estimate on batted balls, actual value otherwise",
      abs(t["xwoba"] - (0.5 + 0.0 + 0.7 + 0.1) / 4) < 1e-9, str(t["xwoba"]))
check("3c gap = wOBA - xwOBA", abs(t["gap"] - (0.4 - 0.325)) < 1e-9)
check("3d K% and BB% per PA", abs(t["k_pct"] - 0.25) < 1e-9 and abs(t["bb_pct"] - 0.25) < 1e-9)
check("3e barrel% and hard-hit% per batted ball", t["barrel_pct"] == 0.5 and t["hard_hit_pct"] == 0.5)
check("3f whiff% = whiffs / swings (4 swings, 1 whiff)", abs(t["whiff_pct"] - 1 / 4) < 1e-9, str(t["whiff_pct"]))
check("3g chase% = swings / pitches outside the zone (3 outside, 2 swings)", abs(t["chase_pct"] - 2 / 3) < 1e-9, str(t["chase_pct"]))
p = team_table(add_teams(pd.DataFrame(rows)), "pitching").loc["H"]
check("3h pitching side groups by fielding team; four-seam velocity", abs(p["ff_velo"] - 96.0) < 1e-9 and p["pa"] == 4)

sw = pd.DataFrame([pitch(description="foul", bat_speed=60.0 + i, swing_length=7.0) for i in range(10)]
                  + [pitch(woba_value=0.0, woba_denom=1, events="field_out")])
bs = team_table(add_teams(sw), "offense").loc["A", "bat_speed"]
check("3i bat speed drops the slowest 10% of the team's swings", abs(bs - np.mean(range(61, 70))) < 1e-9, str(bs))

print("4. persistence statistics")
x = np.linspace(-1, 1, 30)
r = persistence(x, 2 * x + 1, B=300)
check("4a perfect line: r = 1, slope = 2", abs(r["r"] - 1) < 1e-9 and abs(r["slope"] - 2) < 1e-9)
rng = np.random.default_rng(3)
r = persistence(rng.normal(size=30), rng.normal(size=30), B=500)
check("4b independent noise: CI includes zero", r["ci_low"] < 0 < r["ci_high"])
check("4c CONFIRMED needs r above the floor AND CI above zero",
      not confirmed({"r": 0.25, "ci_low": 0.01}) and not confirmed({"r": 0.4, "ci_low": -0.01})
      and confirmed({"r": 0.4, "ci_low": 0.05}))

print("5. synthetic leagues: gap PERSISTS (power) and gap is LUCK (false positives)")
hits = 0
for s in range(100):
    a, b = sim.make_gap_arrays(100 + s, persist=1.0)
    hits += confirmed(persistence(a, b, B=300))
check("5a persistent gap is CONFIRMED in at least 70% of 100 leagues", hits >= 70, f"{hits}/100")
fp = 0
for s in range(200):
    a, b = sim.make_gap_arrays(5000 + s, persist=0.0)
    fp += confirmed(persistence(a, b, B=300))
check("5b luck-only gap is falsely CONFIRMED in under 10% of 200 leagues", fp / 200 < 0.10, f"{fp}/200")

print("6. which predicts next-year wOBA: last wOBA or last xwOBA")
gains = []
for s in range(15):
    o1, o2, p1, p2 = sim.make_team_tables(300 + s, persist=0.0)
    gains.append(compare_predictors(o1["woba"], o1["xwoba"], o2["woba"], B=200)["gain_xwoba_over_woba"])
check("6a with luck-only gaps, xwOBA predicts better on average", np.mean(gains) > 0, f"mean gain {np.mean(gains):.4f}")

print("7. end to end on raw pitch rows")
raw25, _ = sim.make_raw(41, "2025-03-27", "2025-09-28")
raw26, _ = sim.make_raw(42, "2026-03-26", "2026-09-27")
tabs = {}
for y, raw in ((2025, raw25), (2026, raw26)):
    dd = add_teams(raw)
    tabs[("offense", y)], tabs[("pitching", y)] = team_table(dd, "offense"), team_table(dd, "pitching")
check("7a 30 teams on each side", len(tabs[("offense", 2026)]) == 30 and len(tabs[("pitching", 2026)]) == 30)
check("7b every PA belongs to exactly one batting team and one fielding team",
      tabs[("offense", 2026)]["pa"].sum() == tabs[("pitching", 2026)]["pa"].sum() == 30000)
res = analyze(tabs[("offense", 2025)], tabs[("offense", 2026)], tabs[("pitching", 2025)], tabs[("pitching", 2026)])
check("7c analysis runs and reports both sides", set(res) == {"offense", "pitching"} and np.isfinite(res["offense"]["gap"]["r"]))
sh = split_half(raw26)
check("7d split-half runs for both sides", np.isfinite(sh["offense"]["r"]) and np.isfinite(sh["pitching"]["r"]))
cards = build_cards(tabs[("offense", 2026)], tabs[("pitching", 2026)])
check("7e cards: one row per team, ranks 1..30", len(cards) == 30 and cards["off_xwoba_rank"].min() == 1 and cards["off_xwoba_rank"].max() == 30)

lg = tabs[("offense", 2026)].copy()
lg["gap"] = 0.008                                    # every team +0.008, like a league-wide offset
from cards import _vs_league, _dir
check("7f gaps are measured against the league average (PA-weighted mean is zero)",
      abs(float((_vs_league(tabs[("offense", 2026)]) * tabs[("offense", 2026)]["pa"]).sum())) < 1e-6)
check("7g a league-wide offset alone makes every team 'in line', not 'above'",
      all(_dir(v, True, "en") == "in line with" for v in _vs_league(lg)))

print("8. end to end: planted persistent gap is recovered")
rng = np.random.default_rng(7)
planted = rng.normal(0, 0.02, 30)
r1, _ = sim.make_raw(51, "2025-03-27", "2025-09-28", persist_gap_off=planted, n_pa=90000, n_other=1000)
r2, _ = sim.make_raw(52, "2026-03-26", "2026-09-27", persist_gap_off=planted, n_pa=90000, n_other=1000)
o1, o2 = team_table(add_teams(r1), "offense"), team_table(add_teams(r2), "offense")
rr = persistence(o1["gap"], o2["gap"], B=300)["r"]
check("8a offense gap correlates strongly across seasons when the gap is planted", rr > 0.5, str(rr))
check("8b the measured gap tracks the planted truth",
      np.corrcoef(o1.loc[sim.TEAMS, "gap"], planted)[0, 1] > 0.5)

print("9. park check: a planted ballpark effect shows at home but not on the road")
rng = np.random.default_rng(9)
park = rng.normal(0, 0.02, 30)
def with_park(seed, start, end):
    r, _ = sim.make_raw(seed, start, end, persist_gap_off=np.zeros(30), n_pa=120000, n_other=500)
    pa = r["woba_denom"].fillna(0) > 0
    idx = pd.Series(range(30), index=sim.TEAMS)
    r.loc[pa, "woba_value"] = r.loc[pa, "woba_value"].to_numpy() + park[idx[r.loc[pa, "home_team"]].to_numpy()]
    return r
p1, p2 = with_park(61, "2025-03-27", "2025-09-28"), with_park(62, "2026-03-26", "2026-09-27")
tinyv = pd.DataFrame({"inning_topbot": ["Top", "Bot"]})
check("9a offense at home = bottom of the inning; pitching at home = top",
      by_venue(tinyv, "offense", "home")["inning_topbot"].tolist() == ["Bot"]
      and by_venue(tinyv, "pitching", "home")["inning_topbot"].tolist() == ["Top"])
pc = park_check(p1, p2, drop=("T00", "T01"))
check("9b planted park effect: pitching gap repeats at home, much less on the road",
      pc["pitching"]["home"]["r"] > 0.6 and pc["pitching"]["road"]["r"] < pc["pitching"]["home"]["r"] - 0.25,
      f"home {pc['pitching']['home']['r']:.2f} road {pc['pitching']['road']['r']:.2f}")
check("9c the drop-two-teams run returns 28 teams", pc["pitching"]["without_T00_T01"]["n"] == 28)

import tempfile
from plots import park_chart
with tempfile.TemporaryDirectory() as td:
    for lang in ("en", "es"):
        park_chart(pc, Path(td) / f"x_{lang}.png", lang)
    check("9d home-vs-road chart renders in EN and ES", all((Path(td) / f"x_{l}.png").stat().st_size > 5000 for l in ("en", "es")))

print(f"\n{PASSED} passed, {len(FAILED)} failed")
if FAILED:
    print("FAILED:", FAILED)
    sys.exit(1)
