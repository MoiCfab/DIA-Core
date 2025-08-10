# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

from __future__ import annotations

import numpy as np
import pandas as pd
from dia_core.market_state.regime_vector import RegimeVector, compute_regime


def _dummy_df(n: int = 50) -> pd.DataFrame:
    t = np.arange(n)
    close = np.linspace(100.0, 110.0, n) + 0.5 * np.sin(t / 3)
    high = close + 0.5
    low = close - 0.5
    return pd.DataFrame(
        {
            "time": t,
            "open": close,
            "high": high,
            "low": low,
            "close": close,
            "vwap": close,
            "volume": np.linspace(10, 20, n),
            "count": np.full(n, 1),
        }
    )


def test_compute_regime_shapes() -> None:
    df = _dummy_df(60)
    r = compute_regime(df)
    assert isinstance(r, RegimeVector)
    for x in (r.volatility, r.momentum, r.volume, r.entropy, r.spread, r.score):
        assert 0.0 <= x <= 1.0
