from __future__ import annotations

import pandas as pd
from dia_core.data.provider import ohlc_dataframe


def test_ohlc_dataframe_basic() -> None:
    payload = {"XXBTZEUR": [[1710000000, 1, 2, 0.5, 1.5, 1.2, 10.0, 42]]}
    df = ohlc_dataframe({**payload}, "XXBTZEUR")
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns)[:5] == ["time", "open", "high", "low", "close"]
    assert len(df) == 1
