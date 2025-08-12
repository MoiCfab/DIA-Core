# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

"""
Nom du module : strategy/adaptive_trade.py

Description :
    Stratégie « métamorphe » continue. À partir d'un RegimeVector, module :
        probabilité de trade,
        agressivité (k_atr),
        direction (via momentum),
        génération d'un OrderIntent *optionnel*.

    Aucune IO réseau : la stratégie renvoie au plus un OrderIntent qui sera
    validé/sizé par le pipeline de risque existant (pre_trade/propose_order).

Auteur : DYXIUM Invest / D.I.A. Core
"""
from __future__ import annotations


import numpy as np
import pandas as pd

from dia_core.exec.pre_trade import MarketSnapshot
from dia_core.kraken.types import OrderIntent
from dia_core.market_state.regime_vector import RegimeVector, compute_regime
from dia_core.strategy.common import AdaptiveParams, _MOMENTUM_BUY_THRESHOLD
from dia_core.strategy.policy.bandit import BanditPolicy

# Import utility functions to keep decision logic simple.
from dia_core.strategy.utils import (
    compute_k_atr,
    compute_trade_probability,
    should_execute_trade,
    determine_side,
    build_order_intent,
)

__all__ = ["AdaptiveParams", "_MOMENTUM_BUY_THRESHOLD"]


def _interp(a: float, b: float, t: float) -> float:
    """

    Args:
      a: float:
      b: float:
      t: float:

    Returns:

    """
    t2 = float(np.clip(t, 0.0, 1.0))
    return float(a + (b - a) * t2)


def decide_intent(
    *,
    df: pd.DataFrame,
    symbol: str,
    params: AdaptiveParams | None = None,
    rng_seed: int | None = 42,
    policy: BanditPolicy | None = None,
) -> tuple[OrderIntent | None, MarketSnapshot, RegimeVector]:
    """Generate an optional :class:`OrderIntent` based on market regime.

    The decision logic follows a simple probabilistic approach where the
    likelihood of a trade increases with the regime score. The k_ATR
    multiplicator, trade probability and side selection are all
    delegated to small helper functions defined in
    :mod:`dia_core.strategy.utils`. This keeps the cyclomatic
    complexity of this function low and facilitates unit testing.

    Args:
        df: Price window as a :class:`pandas.DataFrame`.
        symbol: Trading pair identifier.
        params: Optional set of strategy parameters. Defaults to
            :class:`AdaptiveParams`.
        rng_seed: Random seed used to initialise the RNG for
            reproducibility.
        policy: Optional multi-armed bandit policy for hyperparameter
            selection.

    Returns:
        A tuple ``(intent, market, regime)``. ``intent`` is ``None``
        when no trade should be executed.
    """
    strategy_params: AdaptiveParams = params or AdaptiveParams()
    regime: RegimeVector = compute_regime(df)
    # Override parameters from a bandit policy when provided.
    if policy is not None:
        _idx, cfg = policy.select(np.random.default_rng(rng_seed))
        strategy_params = AdaptiveParams(**cfg)
    price: float = float(df["close"].iloc[-1]) if not df.empty else 0.0
    # Compute k_ATR and market snapshot.
    k_atr: float = compute_k_atr(strategy_params, regime.score)
    market: MarketSnapshot = MarketSnapshot(
        price=price,
        atr=max(1e-6, np.std(np.diff(df["close"].to_numpy()))),
        k_atr=k_atr,
    )
    # Determine probability of trading.
    prob: float = compute_trade_probability(strategy_params, regime.score)
    rng = np.random.default_rng(rng_seed)
    if not should_execute_trade(prob, price, rng):
        return None, market, regime
    # Decide trade side and build the intent.
    side: str = determine_side(regime.momentum)
    intent: OrderIntent = build_order_intent(symbol, side, price)
    return intent, market, regime
