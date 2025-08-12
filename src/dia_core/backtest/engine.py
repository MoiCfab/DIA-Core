# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

"""
Nom du module : backtest/engine.py

Description :
    Backtester minimal, déterministe, sans dépendances externes.
    Boucle : pour chaque barre -> stratégie -> intent éventuel -> pricing simple
    (exécution immédiate au close simulé), mise à jour equity, métriques.

Auteur : DYXIUM Invest / D.I.A. Core
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
import pandas as pd

from dia_core.backtest.metrics import PerfStats, perf_from_equity
from dia_core.exec.pre_trade import MarketSnapshot
from dia_core.kraken.types import OrderIntent
from dia_core.market_state.regime_vector import RegimeVector
from dia_core.strategy.adaptive_trade import AdaptiveParams, decide_intent


@dataclass(frozen=True)
class BTConfig:
    """Paramètres du backtest (fenêtre, fees, seed)."""

    initial_equity: float = 10_000.0
    symbol: str = "BTC/EUR"
    fee_bps: float = 5.0  # 0.05%


@dataclass(frozen=True)
class BTResult:
    """Résultats de backtest (équité et métriques)."""

    equity: NDArray[np.float64]
    positions: NDArray[np.float64]
    stats: PerfStats


def run(
    df: pd.DataFrame,
    *,
    cfg: BTConfig | None = None,
    decide: Callable[..., tuple[OrderIntent | None, MarketSnapshot, RegimeVector]] = decide_intent,
    params: AdaptiveParams | None = None,
) -> BTResult:
    """Args:
      df: pd.DataFrame:
      *:
      cfg: BTConfig | None:  (Default value = None)
      decide: Callable[...:
      tuple[OrderIntent | None:
      MarketSnapshot:
      RegimeVector]]:  (Default value = decide_intent)

    Args:
      df: pd.DataFrame:
      *:
      cfg: BTConfig | None:  (Default value = None)
      decide: Callable[...:
      tuple[OrderIntent | None:
      MarketSnapshot:
      RegimeVector]]:  (Default value = decide_intent)
      params: AdaptiveParams | None:  (Default value = None)

    Returns:


    """
    cfg = cfg or BTConfig()
    params = params or AdaptiveParams()
    if df.empty:
        eq: NDArray[np.float64] = np.array([cfg.initial_equity], dtype=np.float64)
        return BTResult(eq, np.zeros_like(eq), perf_from_equity(eq))

    equity: float = cfg.initial_equity
    pos: float = 0.0  # +qty long, -qty short
    prev_price: float = float(df["close"].iloc[0])
    positions: list[float] = [pos]
    equities: list[float] = [equity]

    # Boucle : exécution au close
    for i in range(1, len(df)):
        window = df.iloc[: i + 1]
        price = float(window["close"].iloc[-1])
        intent, market, _ = decide(df=window, symbol=cfg.symbol, params=params, rng_seed=i)

        # Ferme la position précédente si un signal opposé arrive
        if pos != 0.0 and intent is not None:
            pnl = pos * (price - prev_price) - abs(pos * price) * (cfg.fee_bps / 1e4)
            equity += pnl
            pos = 0.0

        # Ouvre nouvelle position (1 unité notionnelle) si intent
        if intent is not None:
            side: float = 1.0 if intent.side == "buy" else -1.0
            pos = side * 1.0
            equity -= abs(pos * price) * (cfg.fee_bps / 1e4)

        # Marque au marché
        equity_mtm = equity + pos * (price - prev_price) if pos != 0.0 else equity

        positions.append(pos)
        equities.append(equity_mtm)
        prev_price = price

    eq_arr: NDArray[np.float64] = np.asarray(equities, dtype=np.float64)
    pos_arr: NDArray[np.float64] = np.asarray(positions, dtype=np.float64)
    stats = perf_from_equity(eq_arr)
    return BTResult(eq_arr, pos_arr, stats)
