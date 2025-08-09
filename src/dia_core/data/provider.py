from __future__ import annotations

import logging
from typing import Any

import pandas as pd
from dia_core.data.cache import load_cache, save_cache
from dia_core.kraken.client import KrakenClient

logger = logging.getLogger(__name__)


def ohlc_dataframe(result: dict[str, Any], pair: str) -> pd.DataFrame:
    key = next(iter(result.keys()), None)
    if key is None:
        raise ValueError("OHLC result dict is vide")
    rows = result[key]
    cols = ["time", "open", "high", "low", "close", "vwap", "volume", "count"]
    df = pd.DataFrame(rows, columns=cols)
    df = df.astype(
        {
            "time": "int64",
            "open": "float64",
            "high": "float64",
            "low": "float64",
            "close": "float64",
            "volume": "float64",
        }
    )
    return df


def load_ohlc_window(
    client: KrakenClient, pair: str, interval: int, window_bars: int, cache_dir: str
) -> pd.DataFrame:
    df = load_cache(cache_dir, pair, interval)
    if df is None or len(df) < window_bars:
        logger.info("Téléchargement OHLC depuis Kraken", extra={"component": "data", "pair": pair})
        res = client.get_ohlc(pair, interval=interval)
        df = ohlc_dataframe(res, pair)
        df = df.tail(window_bars).reset_index(drop=True)
        save_cache(cache_dir, pair, interval, df)
    else:
        df = df.tail(window_bars).reset_index(drop=True)
    return df
