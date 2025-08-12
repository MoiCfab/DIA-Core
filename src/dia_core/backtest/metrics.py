# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

"""
Nom du module : backtest/metrics.py

Description :
    Métriques simples : courbe d'équité, PnL, drawdown, Sharpe/Sortino (daily naive).

Auteur : DYXIUM Invest / D.I.A. Core
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

_MIN_EQUITY_LEN = 2


@dataclass(frozen=True)
class PerfStats:
    """ """

    total_return: float
    max_drawdown: float
    sharpe: float
    sortino: float


def _downs(x: NDArray[np.float64]) -> NDArray[np.float64]:
    """

    Args:
      x: NDArray[np.float64]:
      x: NDArray[np.float64]:

    Returns:

    """
    return np.clip(x, None, 0.0).astype(np.float64)


def perf_from_equity(equity: NDArray[np.float64]) -> PerfStats:
    """

    Args:
      equity: NDArray[np.float64]:
      equity: NDArray[np.float64]:

    Returns:

    """
    if equity.size < _MIN_EQUITY_LEN:
        return PerfStats(0.0, 0.0, 0.0, 0.0)
    rets: NDArray[np.float64] = (np.diff(equity) / (equity[:-1] + 1e-12)).astype(np.float64)
    tot = float(equity[-1] / (equity[0] + 1e-12) - 1.0)
    roll_max = np.maximum.accumulate(equity)
    dd: NDArray[np.float64] = ((equity - roll_max) / (roll_max + 1e-12)).astype(np.float64)
    max_dd = float(np.min(dd))
    mu = float(np.mean(rets))
    sd = float(np.std(rets) + 1e-12)
    downside = _downs(rets)
    ds = float(np.std(downside) + 1e-12)
    sharpe = mu / sd
    sortino = mu / ds
    return PerfStats(total_return=tot, max_drawdown=max_dd, sharpe=sharpe, sortino=sortino)
