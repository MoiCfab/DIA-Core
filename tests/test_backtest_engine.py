# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

from __future__ import annotations

import numpy as np
import pandas as pd
from dia_core.backtest.engine import BTConfig, BTResult, run


def _prices(n: int = 120) -> pd.DataFrame:
    t = np.arange(n)
    close = 100 + 0.05 * t + 0.3 * np.sin(t / 7)
    return pd.DataFrame(
        {
            "time": t,
            "open": close,
            "high": close + 0.3,
            "low": close - 0.3,
            "close": close,
            "vwap": close,
            "volume": np.linspace(10, 20, n),
            "count": np.full(n, 1),
        }
    )


def test_backtest_runs() -> None:
    df = _prices(150)
    res = run(df, cfg=BTConfig(initial_equity=1_000.0))
    assert isinstance(res, BTResult)
    assert res.equity.size == df.shape[0]
    # max_drawdown <= 0 (valeur négative)
    assert res.stats.max_drawdown <= 0.0
