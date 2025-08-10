# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

"""
Nom du module : market_state/regime_vector.py

Description :
    Calcul du vecteur d'état de marché R et d'un score de régime continu
    à partir d'une fenêtre OHLC (DataFrame). Tout est purement local et
    déterministe pour faciliter les tests et la CI.

    Entrée attendue : DataFrame colonnes
        ["time","open","high","low","close","vwap","volume","count"]

Utilisé par :
    strategy/adaptive_trade.py (pilotage probabilité/agressivité)
    backtest/engine.py (moteur de simulation)

Auteur : DYXIUM Invest / D.I.A. Core
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, cast

import numpy as np
import pandas as pd
from numpy.typing import NDArray

_MIN_MOMENTUM_POINTS: Final[int] = 3


@dataclass(frozen=True)
class RegimeVector:
    """Vecteur d'état continu normalisé dans [0,1].

    Attributes :
        volatility : vol normalisé (std log-returns) ∈ [0,1]
        momentum : momentum directionnel ∈ [0,1] (0=baissier, 1=haussier)
        volume : volume z-score aplati en [0,1]
        entropy : entropie des retours (Shannon) normalisée ∈ [0,1]
        spread : (high-low)/close normalisé ∈ [0,1]
        score : intensité agrégée du régime (moyenne pondérée) ∈ [0,1]
    """

    volatility: float
    momentum: float
    volume: float
    entropy: float
    spread: float
    score: float


_SMALL: Final[float] = 1e-12


def _safe_min_max(x: NDArray[np.float64]) -> tuple[float, float]:
    a = float(np.nanmin(x))
    b = float(np.nanmax(x))
    if not np.isfinite(a) or not np.isfinite(b) or abs(b - a) < _SMALL:
        return 0.0, 1.0
    return a, b


def _minmax_scale(x: NDArray[np.float64]) -> NDArray[np.float64]:
    lo, hi = _safe_min_max(x)
    return np.clip((x - lo) / (hi - lo + _SMALL), 0.0, 1.0).astype(np.float64)


def _zscore01(x: NDArray[np.float64]) -> NDArray[np.float64]:
    mu = float(np.nanmean(x))
    sd = float(np.nanstd(x))
    z = (x - mu) / (sd + _SMALL)
    # Aplati vers [0,1] via fonction lisse
    out = 0.5 * (1.0 + np.tanh(z / 2.0))
    return cast(NDArray[np.float64], out.astype(np.float64))


def _entropy01(r: NDArray[np.float64], bins: int = 15) -> float:
    # Histogramme discret des retours, entropie de Shannon
    hist, _ = np.histogram(r[np.isfinite(r)], bins=bins, density=True)
    p = hist[hist > 0]
    if p.size == 0:
        return 0.0
    h = -np.sum(p * np.log(p + _SMALL))
    # Normalisation par log(bins)
    return float(np.clip(h / np.log(bins + _SMALL), 0.0, 1.0))


def compute_regime(df: pd.DataFrame, *, mom_window: int = 20) -> RegimeVector:
    """Calcule un vecteur de régime continu à partir d'une fenêtre OHLC.

    Args:
        df: Fenêtre OHLC (≥ mom_window lignes).
        mom_window: Fenêtre pour le momentum directionnel.

    Returns:
        RegimeVector avec composantes ∈ [0,1].
    """
    if df.empty or len(df) < max(5, mom_window):
        return RegimeVector(0.0, 0.5, 0.0, 0.0, 0.0, 0.0)

    close: NDArray[np.float64] = df["close"].astype(float).to_numpy(copy=False)
    high: NDArray[np.float64] = df["high"].astype(float).to_numpy(copy=False)
    low: NDArray[np.float64] = df["low"].astype(float).to_numpy(copy=False)
    volu: NDArray[np.float64] = df["volume"].astype(float).to_numpy(copy=False)

    # Retours log, robustes aux échelles
    r = np.diff(np.log(np.clip(close, _SMALL, None)))
    if r.size == 0:
        return RegimeVector(0.0, 0.5, 0.0, 0.0, 0.0, 0.0)

    # Volatilité : std des retours sur toute la fenêtre → minmax
    vol_series = pd.Series(r)
    vol_roll = vol_series.rolling(window=mom_window, min_periods=5).std().to_numpy()
    vol_norm = float(_minmax_scale(np.nan_to_num(vol_roll, nan=0.0).astype(np.float64))[-1])

    # Momentum directionnel : slope des prix (OLS) → sigmoïde vers [0,1]
    px = close[-mom_window:]
    x = np.arange(px.size, dtype=float)
    if px.size >= _MIN_MOMENTUM_POINTS:
        x_mat = np.c_[np.ones_like(x), x]
        beta = np.linalg.lstsq(x_mat, px, rcond=None)[0]
        slope = float(beta[1]) / (abs(float(beta[1])) + abs(float(beta[0])) + _SMALL)
    else:
        slope = 0.0
    mom = 0.5 * (1.0 + np.tanh(slope * 5.0))  # centrée 0.5

    # Volume : z-score aplati
    vol01 = float(_zscore01(volu)[-1])

    # Entropie : diversité des directions de r
    ent01 = _entropy01(r)

    # Spread : (H-L)/Close normalisé sur la fenêtre
    spr = (high - low) / np.clip(close, _SMALL, None)
    spr01 = float(_minmax_scale(np.nan_to_num(spr, nan=0.0).astype(np.float64))[-1])

    # Score global pondéré (favorise volatilité + momentum)
    weights = np.array([0.30, 0.30, 0.15, 0.10, 0.15], dtype=float)
    vec = np.array([vol_norm, mom, vol01, ent01, spr01], dtype=float)
    score = float(np.clip(np.dot(weights, vec), 0.0, 1.0))

    return RegimeVector(
        volatility=float(vol_norm),
        momentum=float(mom),
        volume=float(vol01),
        entropy=float(ent01),
        spread=float(spr01),
        score=score,
    )
