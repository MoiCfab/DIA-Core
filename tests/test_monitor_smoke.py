# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

from __future__ import annotations

from dia_core.monitor.ui_app import UiState, build_state

_SCORE = 0.7


def test_build_state() -> None:
    st = build_state(symbol="BTC/EUR", regime={"score": _SCORE}, k_atr=2.0, last_side="buy")
    assert isinstance(st, UiState)
    assert st.regime["score"] == _SCORE
