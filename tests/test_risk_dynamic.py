# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

from __future__ import annotations

from dia_core.market_state.regime_vector import RegimeVector
from dia_core.risk.dynamic_manager import adjust


def test_adjust_monotonic() -> None:
    r_low = RegimeVector(
        volatility=0.1, momentum=0.2, volume=0.0, entropy=0.0, spread=0.0, score=0.1
    )
    r_hi = RegimeVector(
        volatility=0.9, momentum=0.8, volume=0.0, entropy=0.0, spread=0.0, score=0.9
    )
    a = adjust(r_low)
    b = adjust(r_hi)
    assert b.k_atr > a.k_atr
    assert b.risk_per_trade_pct > a.risk_per_trade_pct
    assert b.max_exposure_pct > a.max_exposure_pct
