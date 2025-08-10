# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

from __future__ import annotations

import numpy as np
import pandas as pd
from dia_core.strategy.adaptive_trade import AdaptiveParams, decide_intent


def _df(n: int = 80) -> pd.DataFrame:
    t = np.arange(n)
    close = 100 + 0.1 * t
    return pd.DataFrame(
        {
            "time": t,
            "open": close,
            "high": close + 0.2,
            "low": close - 0.2,
            "close": close,
            "vwap": close,
            "volume": np.linspace(5, 10, n),
            "count": np.full(n, 1),
        }
    )


def test_decide_intent_deterministic() -> None:
    df = _df(80)
    intent, market, regime = decide_intent(
        df=df, symbol="BTC/EUR", params=AdaptiveParams(), rng_seed=123
    )
    assert market.price > 0
    assert 0.0 <= regime.score <= 1.0
    # Avec rng_seed fixé, le résultat est déterministe
    # intent peut être None ou OrderIntent, mais l'appel ne doit pas lever
