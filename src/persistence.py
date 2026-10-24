"""
persistence.py
Does a team's gap (actual minus expected) repeat? Correlation across the 30 teams
with a bootstrap CI that resamples whole teams, plus the slope (how much carries over).
"""
import numpy as np
import pandas as pd
from scipy import stats

from config import BOOTSTRAP_B, SEED, MIN_R


def _pearson(x, y):
    xc, yc = x - x.mean(), y - y.mean()
    den = np.sqrt((xc ** 2).sum() * (yc ** 2).sum())
    return float((xc * yc).sum() / den) if den > 0 else float("nan")


def persistence(x, y, B: int = BOOTSTRAP_B, seed: int = SEED) -> dict:
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    n = len(x)
    r = _pearson(x, y)
    rho = float(stats.spearmanr(x, y)[0])
    slope = float(np.polyfit(x, y, 1)[0])
    rng = np.random.default_rng(seed)
    rs, slopes = [], []
    for _ in range(B):
        i = rng.integers(0, n, n)
        if x[i].std() == 0 or y[i].std() == 0:
            continue
        rs.append(_pearson(x[i], y[i]))
        slopes.append(np.polyfit(x[i], y[i], 1)[0])
    lo, hi = np.percentile(rs, [2.5, 97.5])
    slo, shi = np.percentile(slopes, [2.5, 97.5])
    return {"n": n, "r": r, "ci_low": float(lo), "ci_high": float(hi), "spearman": rho,
            "slope": slope, "slope_low": float(slo), "slope_high": float(shi)}


def confirmed(res: dict, min_r: float = MIN_R) -> bool:
    return bool(res["r"] >= min_r and res["ci_low"] > 0)


def loo_rmse(x, y):
    """Leave-one-team-out RMSE of predicting y from x with a straight line."""
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    n = len(x)
    err = np.empty(n)
    for k in range(n):
        m = np.arange(n) != k
        b, a = np.polyfit(x[m], y[m], 1)
        err[k] = y[k] - (a + b * x[k])
    return err ** 2


def compare_predictors(xw, xx, y, B: int = BOOTSTRAP_B, seed: int = SEED) -> dict:
    """RMSE(last year's wOBA) - RMSE(last year's xwOBA), predicting this year's wOBA.
    Positive = xwOBA predicts better. Teams are resampled."""
    se_w, se_x = loo_rmse(xw, y), loo_rmse(xx, y)
    n = len(se_w)
    point = float(np.sqrt(se_w.mean()) - np.sqrt(se_x.mean()))
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(B):
        i = rng.integers(0, n, n)
        diffs.append(np.sqrt(se_w[i].mean()) - np.sqrt(se_x[i].mean()))
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return {"rmse_woba_pred": float(np.sqrt(se_w.mean())), "rmse_xwoba_pred": float(np.sqrt(se_x.mean())),
            "gain_xwoba_over_woba": point, "ci_low": float(lo), "ci_high": float(hi)}
