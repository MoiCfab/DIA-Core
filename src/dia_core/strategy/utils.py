"""Utility functions for strategy decision making.

This module provides a set of helpers used by trading strategies to
encapsulate simple calculations such as k_ATR interpolation,
probability computation and order intent construction. Splitting these
operations into separate functions reduces the cyclomatic complexity
of the main strategy implementation and facilitates unit testing.

"""

from __future__ import annotations


import numpy as np

from dia_core.kraken.types import OrderIntent
from dia_core.strategy.common import AdaptiveParams, _MOMENTUM_BUY_THRESHOLD


def compute_k_atr(params: AdaptiveParams, regime_score: float) -> float:
    """Linearly interpolate the k_ATR value based on regime score.

    Args:
        params: Parameter set defining the minimum and maximum k_ATR.
        regime_score: Normalised regime score between 0 and 1.

    Returns:
        Interpolated k_ATR value.
    """
    t = float(np.clip(regime_score, 0.0, 1.0))
    return float(params.k_atr_min + (params.k_atr_max - params.k_atr_min) * t)


def compute_trade_probability(params: AdaptiveParams, regime_score: float) -> float:
    """Calculate the probability of executing a trade.

    The probability is clamped to the interval [0, 1].

    Args:
        params: Parameter set defining base probability and boost factor.
        regime_score: Normalised regime score between 0 and 1.

    Returns:
        A float between 0 and 1 representing the probability of trading.
    """
    raw_prob: float = params.base_prob + params.max_boost * regime_score
    return float(np.clip(raw_prob, 0.0, 1.0))


def should_execute_trade(probability: float, price: float, rng: np.random.Generator) -> bool:
    """Determine whether to execute a trade based on probability and price.

    Args:
        probability: Probability of executing a trade.
        price: Latest market price. Trades are never executed when price
            is non-positive.
        rng: NumPy random generator used to draw a uniform sample.

    Returns:
        ``True`` if the trade should be executed, ``False`` otherwise.
    """
    if price <= 0.0:
        return False
    return rng.random() <= probability


def determine_side(regime_momentum: float) -> str:
    """Select the trade side based on regime momentum.

    A simple threshold check translates momentum into a 'buy' or 'sell' signal.

    Args:
        regime_momentum: Normalised momentum between 0 and 1.

    Returns:
        ``"buy"`` when momentum exceeds the global threshold, ``"sell"`` otherwise.
    """
    return "buy" if regime_momentum >= _MOMENTUM_BUY_THRESHOLD else "sell"


def build_order_intent(symbol: str, side: str, price: float) -> OrderIntent:
    """Construct an :class:`OrderIntent` for a single unit trade.

    Args:
        symbol: Trading pair identifier.
        side: Side of the trade, either ``"buy"`` or ``"sell"``.
        price: Limit price for the order.

    Returns:
        A new :class:`OrderIntent` with default values for quantity and
        time in force.
    """
    return OrderIntent(
        symbol=symbol,
        side=side,
        type="limit",
        qty=0.0,
        limit_price=price,
        time_in_force="GTC",
    )
