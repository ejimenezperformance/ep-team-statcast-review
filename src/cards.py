"""
cards.py -- one short bilingual card per team, from the current-season tables.
Rank 1 = best. Wording is descriptive: gaps "came with" contact quality, they are not causes.
"""
import numpy as np
import pandas as pd


def _rank(s: pd.Series, high_is_good: bool) -> pd.Series:
    return s.rank(ascending=not high_is_good, method="min").astype("Int64")


def _vs_league(t: pd.DataFrame) -> pd.Series:
    """Gap minus the PA-weighted league average gap. Statcast's xwOBA sits a little below actual wOBA
    for the whole league, so a gap is only meaningful relative to the other teams."""
    league = float((t["gap"] * t["pa"]).sum() / t["pa"].sum())
    return t["gap"] - league


def build_cards(off: pd.DataFrame, pit: pd.DataFrame) -> pd.DataFrame:
    c = pd.DataFrame(index=off.index.intersection(pit.index))
    off, pit = off.assign(gap_vs_league=_vs_league(off)), pit.assign(gap_vs_league=_vs_league(pit))
    c["off_xwoba"] = off["xwoba"]; c["off_woba"] = off["woba"]; c["off_gap"] = off["gap"]; c["off_gap_vs_league"] = off["gap_vs_league"]
    c["off_xwoba_rank"] = _rank(off["xwoba"], True)
    c["off_gap_rank"] = _rank(off["gap_vs_league"], True)
    if "bat_speed" in off:
        c["bat_speed"] = off["bat_speed"]; c["bat_speed_rank"] = _rank(off["bat_speed"], True)
    c["pit_xwoba"] = pit["xwoba"]; c["pit_woba"] = pit["woba"]; c["pit_gap"] = pit["gap"]; c["pit_gap_vs_league"] = pit["gap_vs_league"]
    c["pit_xwoba_rank"] = _rank(pit["xwoba"], False)
    c["pit_gap_rank"] = _rank(pit["gap_vs_league"], False)      # lower gap against = better results than contact quality
    if "ff_velo" in pit:
        c["ff_velo"] = pit["ff_velo"]; c["ff_velo_rank"] = _rank(pit["ff_velo"], True)
    return c.sort_values("off_xwoba_rank")


def _dir(gap: float, offense: bool, lang: str) -> str:
    better = gap > 0 if offense else gap < 0
    if abs(gap) < 0.003:
        return {"en": "in line with", "es": "en línea con"}[lang]
    return {"en": ("above" if better else "below"), "es": ("por encima de" if better else "por debajo de")}[lang]


def cards_markdown(cards: pd.DataFrame, year: int, persist_note_en: str, persist_note_es: str) -> str:
    out = [f"# Team cards {year} / Fichas por equipo {year}\n",
           f"**EN:** {persist_note_en}\n", f"**ES:** {persist_note_es}\n",
           "Rank 1 = best. / Puesto 1 = mejor.\n"]
    for team, r in cards.iterrows():
        bs = (f" Bat speed {r['bat_speed']:.1f} mph (#{int(r['bat_speed_rank'])})."
              if "bat_speed" in r and pd.notna(r.get("bat_speed")) else "")
        fv = (f" Four-seam velocity {r['ff_velo']:.1f} mph (#{int(r['ff_velo_rank'])})."
              if "ff_velo" in r and pd.notna(r.get("ff_velo")) else "")
        out.append(
            f"## {team}\n"
            f"- EN: Offense xwOBA {r['off_xwoba']:.3f} (#{int(r['off_xwoba_rank'])}); results came "
            f"{_dir(r['off_gap_vs_league'], True, 'en')} what its contact quality says, vs. league average ({r['off_gap_vs_league']:+.3f}).{bs} "
            f"Pitching xwOBA against {r['pit_xwoba']:.3f} (#{int(r['pit_xwoba_rank'])}); results came "
            f"{_dir(r['pit_gap_vs_league'], False, 'en')} what its contact quality says, vs. league average ({r['pit_gap_vs_league']:+.3f}).{fv}\n"
            f"- ES: Ofensiva xwOBA {r['off_xwoba']:.3f} (#{int(r['off_xwoba_rank'])}); los resultados vinieron "
            f"{_dir(r['off_gap_vs_league'], True, 'es')} lo que dice su calidad de contacto, frente al promedio de la liga ({r['off_gap_vs_league']:+.3f}).{bs.replace('Bat speed', 'Velocidad de bate')} "
            f"Pitcheo xwOBA en contra {r['pit_xwoba']:.3f} (#{int(r['pit_xwoba_rank'])}); los resultados vinieron "
            f"{_dir(r['pit_gap_vs_league'], False, 'es')} lo que dice su calidad de contacto, frente al promedio de la liga ({r['pit_gap_vs_league']:+.3f}).{fv.replace('Four-seam velocity', 'Velocidad de recta de cuatro costuras')}\n")
    return "\n".join(out)
