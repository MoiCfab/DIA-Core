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
from dia_core.backtest.models import CloseOpenParams
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
    """Run a deterministic backtest over a price series.

    The implementation is intentionally decomposed into smaller helper
    functions to keep the cyclomatic complexity of each unit very low.
    See the private helpers ``_run_backtest_loop``,
    ``_close_and_open_position`` and ``_mark_to_market`` for details.

    Args:
        df: Historical OHLC data sorted chronologically.
        cfg: Optional backtest configuration. Defaults to
            :class:`BTConfig` when ``None``.
        decide: Strategy callback responsible for emitting an optional
            :class:`OrderIntent`. The default is
            :func:`dia_core.strategy.adaptive_trade.decide_intent`.
        params: Optional strategy parameters for the decision function.

    Returns:
        A :class:`BTResult` containing the equity curve, position
        history and performance statistics.
    """
    bt_cfg = cfg or BTConfig()
    strategy_params = params or AdaptiveParams()
    # If the DataFrame is empty we return a trivial result.
    if df.empty:
        eq: NDArray[np.float64] = np.array([bt_cfg.initial_equity], dtype=np.float64)
        return BTResult(eq, np.zeros_like(eq), perf_from_equity(eq))
    # Run the main loop and gather equity and positions.
    equities, positions = _run_backtest_loop(df, bt_cfg, decide, strategy_params)
    eq_arr: NDArray[np.float64] = np.asarray(equities, dtype=np.float64)
    pos_arr: NDArray[np.float64] = np.asarray(positions, dtype=np.float64)
    stats = perf_from_equity(eq_arr)
    return BTResult(eq_arr, pos_arr, stats)


def _run_backtest_loop(
    df: pd.DataFrame,
    cfg: BTConfig,
    decide: Callable[..., tuple[OrderIntent | None, MarketSnapshot, RegimeVector]],
    params: AdaptiveParams,
) -> tuple[list[float], list[float]]:
    """Iterate over a price series and compute equity/position changes.

    Args:
        df: Historical OHLC data.
        cfg: Backtest configuration.
        decide: Strategy callback.
        params: Strategy parameters.

    Returns:
        Two lists containing the equity and position for each bar.
    """
    equity: float = cfg.initial_equity
    position: float = 0.0  # Positive for long positions, negative for short.
    prev_price: float = float(df["close"].iloc[0])
    positions: list[float] = [position]
    equities: list[float] = [equity]

    for i in range(1, len(df)):
        window = df.iloc[: i + 1]
        current_price: float = float(window["close"].iloc[-1])
        intent, _market, _ = decide(df=window, symbol=cfg.symbol, params=params, rng_seed=i)
        equity, position = _close_and_open_position(
            CloseOpenParams(
                equity=equity,
                position=position,
                prev_price=prev_price,
                current_price=current_price,
                fee_bps=cfg.fee_bps,
                intent_side=(intent.side if intent is not None else None),
            )
        )
        # Mark the position to market regardless of whether a trade occurred.
        equity_mtm: float = _mark_to_market(equity, position, prev_price, current_price)
        positions.append(position)
        equities.append(equity_mtm)
        prev_price = current_price
    return equities, positions


def _close_and_open_position(params: CloseOpenParams) -> tuple[float, float]:
    """Close an existing position and open a new one if instructed.

    The helper applies trading fees on both closing and opening trades. It
    returns the updated equity and position values.

    Args:
        equity: Current equity before executing this step.
        position: Current position size. Non-zero values indicate an
            open position.
        prev_price: Price at which the previous bar closed.
        current_price: Current bar close price.
        cfg: Backtest configuration providing the fee schedule.
        intent: Optional order intent emitted by the strategy.

    Returns:
        A tuple ``(equity, position)`` with updated values.
    """
    equity = params.equity
    position = params.position
    price_prev = params.prev_price
    price_now = params.current_price
    fee = params.fee_bps / 1e4
    side = params.intent_side

    # Close existing position if a new intent is present.
    if position != 0.0 and side is not None:
        pnl = position * (price_now - price_prev) - abs(position * price_now) * fee
        equity += pnl
        position = 0.0

    # Open new position if instructed.
    if side is not None:
        side_mul = 1.0 if side == "buy" else -1.0
        position = side_mul * 1.0
        equity -= abs(position * price_now) * fee

    return equity, position


def _mark_to_market(
    equity: float,
    position: float,
    prev_price: float,
    current_price: float,
) -> float:
    """Compute the mark-to-market equity.

    When a position is open the equity is adjusted by the unrealised
    profit or loss. When no position is open the equity is returned as
    is.

    Args:
        equity: The realised equity after closing/opening trades.
        position: Current position size.
        prev_price: Last bar close price.
        current_price: Current bar close price.

    Returns:
        The mark-to-market equity value.
    """
    if position != 0.0:
        return equity + position * (current_price - prev_price)
    return equity
