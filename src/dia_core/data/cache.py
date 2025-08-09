from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def cache_path(cache_dir: str, pair: str, interval: int) -> Path:
    p = Path(cache_dir)
    p.mkdir(parents=True, exist_ok=True)
    safe = pair.replace("/", "_")
    return p / f"{safe}_{interval}.parquet"


def load_cache(cache_dir: str, pair: str, interval: int) -> pd.DataFrame | None:
    """Lecture cache parquet, optionnelle si pyarrow/fastparquet absent."""
    path = cache_path(cache_dir, pair, interval)
    if not path.exists():
        return None
    try:
        return pd.read_parquet(path)
    except (ImportError, ValueError) as e:
        logger.info("Parquet indisponible/illisible, skip read (%s): %s", path, e)
        return None


def save_cache(cache_dir: str, pair: str, interval: int, df: pd.DataFrame) -> None:
    """Écriture cache parquet, optionnelle si pyarrow/fastparquet absent."""
    path = cache_path(cache_dir, pair, interval)
    try:
        df.to_parquet(path, index=False)
    except (ImportError, ValueError) as e:
        logger.info("Parquet indisponible, skip write (%s): %s", path, e)
