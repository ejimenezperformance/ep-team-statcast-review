"""
data_loader.py
Downloads one regular season from Statcast in 10-day chunks, one slim file per
chunk, so an interrupted run resumes where it stopped.

Run:  python src/data_loader.py 2025      (20-40 minutes; needs internet)
      python src/data_loader.py 2026
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

from config import DATA_DIR, SEASONS, CHUNK_DAYS, NEEDED_COLUMNS


def chunk_dir(year: int) -> Path:
    return DATA_DIR / f"chunks_{year}"


def chunk_ranges(start: str, end: str, days: int):
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    out = []
    while s <= e:
        t = min(s + pd.Timedelta(days=days - 1), e)
        out.append((s.strftime("%Y-%m-%d"), t.strftime("%Y-%m-%d")))
        s = t + pd.Timedelta(days=1)
    return out


def check_columns(df: pd.DataFrame) -> None:
    missing = [c for c in NEEDED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Statcast pull is missing columns: {missing}. Try: pip install -U pybaseball")


def slim(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[df["game_type"] == "R", NEEDED_COLUMNS]


def pull_season(year: int) -> None:
    from pybaseball import statcast, cache
    cache.enable()
    d = chunk_dir(year)
    d.mkdir(parents=True, exist_ok=True)
    cfg = SEASONS[year]
    ranges = chunk_ranges(cfg["start"], cfg["end"], CHUNK_DAYS)
    for i, (a, b) in enumerate(ranges, 1):
        path = d / f"{a}_{b}.csv.gz"
        if path.exists():
            print(f"[{i}/{len(ranges)}] {a} to {b}: already downloaded")
            continue
        df = statcast(start_dt=a, end_dt=b, verbose=False)
        if df is None or df.empty:
            pd.DataFrame(columns=NEEDED_COLUMNS).to_csv(path, index=False)
            print(f"[{i}/{len(ranges)}] {a} to {b}: no games")
            continue
        check_columns(df)
        out = slim(df)
        out.to_csv(path, index=False)
        print(f"[{i}/{len(ranges)}] {a} to {b}: kept {len(out):,} pitches")


def load_season(year: int) -> pd.DataFrame:
    files = sorted(chunk_dir(year).glob("*.csv.gz"))
    if not files:
        raise SystemExit(f"No data for {year}. Run: python src/data_loader.py {year}")
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df["game_date"] = pd.to_datetime(df["game_date"])
    return df


if __name__ == "__main__":
    if len(sys.argv) < 2 or int(sys.argv[1]) not in SEASONS:
        raise SystemExit(f"Usage: python src/data_loader.py <{'|'.join(map(str, SEASONS))}>")
    pull_season(int(sys.argv[1]))
    print("Done.")
