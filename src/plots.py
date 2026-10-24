"""
plots.py -- persistence scatter for offense and pitching (EN and ES), EP style, direct team labels.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

NAVY, GOLD, OFFWHITE, GREEN, RED = "#0B1B33", "#D4A53A", "#F5F3EC", "#3D6B4F", "#B5482A"

TEXT = {
    "en": {
        "title": "Does a team's gap between results and contact quality repeat next season?",
        "offense": "Offense: wOBA minus xwOBA", "pitching": "Pitching: wOBA against minus xwOBA against",
        "x": "2025 gap", "y": "2026 gap", "r": "r",
        "note": "One dot per team (30). Gap = actual minus expected from contact quality. Dashed = league average. Line = least squares. CI by resampling teams.",
        "conf": "CONFIRMED", "not": "NOT CONFIRMED",
    },
    "es": {
        "title": "¿La diferencia entre resultados y calidad de contacto de un equipo se repite al año siguiente?",
        "offense": "Ofensiva: wOBA menos xwOBA", "pitching": "Pitcheo: wOBA en contra menos xwOBA en contra",
        "x": "Diferencia 2025", "y": "Diferencia 2026", "r": "r",
        "note": "Un punto por equipo (30). Diferencia = real menos esperado por calidad de contacto. Punteado = promedio de la liga. Línea = mínimos cuadrados. IC remuestreando equipos.",
        "conf": "CONFIRMADO", "not": "NO CONFIRMADO",
    },
}


def persistence_chart(panels: dict, path, lang="en"):
    """panels: {'offense': (teams, x, y, result, confirmed), 'pitching': (...)}"""
    T = TEXT[lang]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.6), dpi=150)
    fig.patch.set_facecolor(OFFWHITE)
    for ax, side in zip(axes, ("offense", "pitching")):
        teams, x, y, res, ok = panels[side]
        ax.set_facecolor(OFFWHITE)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        col = GREEN if ok else NAVY
        ax.axhline(float(np.mean(y)), color=RED, lw=1, ls="--"); ax.axvline(float(np.mean(x)), color=RED, lw=1, ls="--")
        ax.scatter(x, y, color=col, s=26, zorder=3)
        for t, xi, yi in zip(teams, x, y):
            ax.annotate(t, (xi, yi), xytext=(3, 3), textcoords="offset points", fontsize=7, color=NAVY)
        b, a = np.polyfit(x, y, 1)
        xs = np.linspace(min(x), max(x), 50)
        ax.plot(xs, a + b * xs, color=GOLD, lw=2.5)
        ax.set_xlabel(T["x"], color=NAVY); ax.set_ylabel(T["y"], color=NAVY)
        verdict = T["conf"] if ok else T["not"]
        ax.set_title(f"{T[side]}\n{T['r']} = {res['r']:+.2f}  [{res['ci_low']:+.2f}, {res['ci_high']:+.2f}]  ·  {verdict}",
                     color=NAVY, fontsize=10, fontweight="bold")
    fig.suptitle(T["title"], color=NAVY, fontweight="bold", fontsize=12)
    fig.text(0.01, 0.01, T["note"], fontsize=8, color=NAVY)
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(path, facecolor=OFFWHITE)
    plt.close(fig)


PARK_TEXT = {
    "en": {"title": "The gap that repeats shows up at home, not on the road",
           "ylabel": "Year-to-year correlation of the gap (2025 → 2026)",
           "home": "Home games only", "road": "Road games only",
           "offense": "Offense", "pitching": "Pitching",
           "note": "Exploratory, decided after seeing the main result. Bars = 95% CI (resampling teams). Same number of games in each bar. xwOBA ignores the ballpark."},
    "es": {"title": "La diferencia que se repite aparece en casa, no de visitante",
           "ylabel": "Correlación año a año de la diferencia (2025 → 2026)",
           "home": "Solo partidos en casa", "road": "Solo partidos de visitante",
           "offense": "Ofensiva", "pitching": "Pitcheo",
           "note": "Exploratorio, decidido después de ver el resultado principal. Barras = IC 95% (remuestreo de equipos). Misma cantidad de partidos en cada barra. El xwOBA ignora el estadio."},
}


def park_chart(pc: dict, path, lang="en"):
    T = PARK_TEXT[lang]
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=150)
    fig.patch.set_facecolor(OFFWHITE); ax.set_facecolor(OFFWHITE)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    xs, w = {"offense": 0.0, "pitching": 1.0}, 0.34
    for side in ("offense", "pitching"):
        for venue, off, col in (("home", -w / 2 - 0.02, GOLD), ("road", w / 2 + 0.02, NAVY)):
            g = pc[side][venue]
            x = xs[side] + off
            ax.bar(x, g["r"], width=w, color=col, zorder=2)
            ax.errorbar(x, g["r"], yerr=[[g["r"] - g["ci_low"]], [g["ci_high"] - g["r"]]],
                        color=NAVY if col == GOLD else RED, capsize=5, lw=2, zorder=3)
            ax.text(x, g["ci_high"] + 0.03, f"{g['r']:+.2f}", ha="center", fontsize=10, color=NAVY, fontweight="bold")
            ax.text(x, -0.62, T[venue], ha="center", fontsize=8.5, color=NAVY)
    ax.axhline(0, color=NAVY, lw=1)
    ax.set_xticks([xs["offense"], xs["pitching"]]); ax.set_xticklabels([T["offense"], T["pitching"]], color=NAVY, fontsize=11, fontweight="bold")
    ax.tick_params(axis="x", pad=24)
    ax.set_ylim(-0.7, 0.95); ax.set_ylabel(T["ylabel"], color=NAVY, fontsize=9)
    ax.set_title(T["title"], color=NAVY, fontweight="bold", fontsize=12)
    fig.text(0.01, 0.01, T["note"], fontsize=7.5, color=NAVY)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, facecolor=OFFWHITE)
    plt.close(fig)
