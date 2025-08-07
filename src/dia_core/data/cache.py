from __future__ import annotations
import os
from typing import Optional
import pandas as pd

def cache_path(cache_dir: str, pair: str, interval: int) -> str:
    os.makedirs(cache_dir, exist_ok=True)
    safe = pair.replace("/", "_")
    return os.path.join(cache_dir, f"{safe}_{interval}.parquet")

def load_cached(cache_dir: str, pair: str, interval: int) -> Optional[pd.DataFrame]:
    path = cache_path(cache_dir, pair, interval)
    if os.path.exists(path):
        return pd.read_parquet(path)
    return None

def save_cache(cache_dir: str, pair: str, interval: int, df: pd.DataFrame) -> None:
    path = cache_path(cache_dir, pair, interval)
    df.to_parquet(path, index=False)
