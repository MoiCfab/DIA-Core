# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited
from __future__ import annotations

from collections.abc import Mapping
import json
import time
from typing import Any, Final

import httpx
import numpy as np
import pandas as pd
from pandas import DataFrame

_COLS: Final = ["time", "open", "high", "low", "close", "vwap", "volume", "count"]
_BASES = {"BTC": "XXBT", "ETH": "XETH"}
_QUOTES = {"EUR": "ZEUR", "USD": "ZUSD", "USDT": "USDT"}


def _kraken_pair(symbol: str) -> str:
    base, quote = symbol.split("/")
    return f"{_BASES.get(base, base)}{_QUOTES.get(quote, quote)}"


def get_last_price(symbol: str, *, timeout_s: float = 7.0) -> float:
    """Prix spot récent via Kraken public / Ticker, fallback synthétique si réseau HS."""
    pair = _kraken_pair(symbol)
    url = "https://api.kraken.com/0/public/Ticker"
    try:
        with httpx.Client(timeout=timeout_s) as c:
            r = c.get(url, params={"pair": pair})
            r.raise_for_status()
            js = r.json()
            return float(js["result"][pair]["c"][0])
    except (httpx.HTTPError, KeyError, ValueError, json.JSONDecodeError):
        t = time.time()
        base = 25_000.0 if "BTC" in symbol else 1_500.0
        return float(base * (1.0 + 0.01 * np.sin(t / 300.0)))


def load_ohlc_window(symbol: str, window: int = 200, *, interval_min: int = 1) -> pd.DataFrame:
    """Fenêtre OHLC via Kraken public / OHLC, fallback synthétique si réseau HS."""
    pair = _kraken_pair(symbol)
    url = "https://api.kraken.com/0/public/OHLC"
    try:
        with httpx.Client(timeout=10.0) as c:
            r = c.get(url, params={"pair": pair, "interval": interval_min})
            r.raise_for_status()
            js = r.json()
            rows = js["result"][pair][-window:]
            df = pd.DataFrame(rows, columns=_COLS, dtype=float)
            df["time"] = df["time"].astype(int)
            return df
    except (httpx.HTTPError, KeyError, ValueError, json.JSONDecodeError):
        now = int(time.time())
        step = 60
        close = np.full(window, get_last_price(symbol))
        rng = np.random.default_rng(42)
        for i in range(1, window):
            close[i] = close[i - 1] * (1.0 + rng.normal(0.0, 0.0009))
        high = close * (1.0 + rng.uniform(0, 0.001, size=window))
        low = close * (1.0 - rng.uniform(0, 0.001, size=window))
        open_ = np.r_[close[0], close[:-1]]
        vwap = close
        volume = rng.lognormal(mean=8.5, sigma=0.3, size=window)
        count = rng.integers(50, 200, size=window)
        ts = np.arange(now - (window - 1) * step, now + 1, step, dtype=int)
        return pd.DataFrame(
            np.c_[ts, open_, high, low, close, vwap, volume, count],
            columns=_COLS,
            dtype=float,
        )


def ohlc_dataframe(pair: str, payload: Mapping[str, Any], *, interval_min: int = 1) -> DataFrame:
    if "result" in payload and isinstance(payload["result"], Mapping) and pair in payload["result"]:
        rows = payload["result"][pair]
    elif pair in payload:
        rows = payload[pair]
    else:
        raise ValueError(f"Pair '{pair}' not found in payload")

    df = pd.DataFrame(rows, columns=_COLS, dtype=float)
    df["time"] = df["time"].astype(int)
    return df
