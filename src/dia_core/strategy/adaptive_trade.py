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

from dataclasses import dataclass

import numpy as np
import pandas as pd
from dia_core.exec.pre_trade import MarketSnapshot
from dia_core.kraken.types import OrderIntent
from dia_core.market_state.regime_vector import RegimeVector, compute_regime
from dia_core.strategy.policy.bandit import BanditPolicy

_MOMENTUM_BUY_THRESHOLD: float = 0.5


@dataclass(frozen=True)
class AdaptiveParams:
    """Paramètres simples de modulation.

    Attributes :
        base_prob : probabilité de base (régime neutre)
        max_boost : amplification max de la prob par score
        k_atr_min : k_atr en régime calme
        k_atr_max : k_atr en régime explosif
    """

    base_prob: float = 0.10
    max_boost: float = 0.60
    k_atr_min: float = 1.5
    k_atr_max: float = 3.0


def _interp(a: float, b: float, t: float) -> float:
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
    """Génère éventuellement un OrderIntent en fonction du régime.

    - La direction suit le signe du momentum (>=0.5 → buy, sinon sell).
    - La probabilité de déclenchement = base_prob + score * max_boost.
    - k_atr = interpolation entre [k_atr_min, k_atr_max] selon *score*.

    Returns: (intent|None, market, regime)
    """
    params = params or AdaptiveParams()
    regime = compute_regime(df)

    # Si une policy est fournie, on tire un bras → hyperparamètres
    if policy is not None:
        _idx, cfg = policy.select(np.random.default_rng(rng_seed))
        params = AdaptiveParams(**cfg)

    price = float(df["close"].iloc[-1]) if not df.empty else 0.0

    k_atr = _interp(params.k_atr_min, params.k_atr_max, regime.score)
    market = MarketSnapshot(
        price=price, atr=max(1e-6, np.std(np.diff(df["close"].to_numpy()))), k_atr=k_atr
    )

    # Probabilité de trade
    p = float(np.clip(params.base_prob + params.max_boost * regime.score, 0.0, 1.0))
    rnd = np.random.default_rng(rng_seed)
    if rnd.random() > p or price <= 0.0:
        return None, market, regime

    side = "buy" if regime.momentum >= _MOMENTUM_BUY_THRESHOLD else "sell"
    intent = OrderIntent(
        symbol=symbol, side=side, type="limit", qty=0.0, limit_price=price, time_in_force="GTC"
    )
    return intent, market, regime
