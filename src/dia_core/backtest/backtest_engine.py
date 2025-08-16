# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : backtest/backtest_engine.py

Description :
Simulateur simple d'exécution de stratégie sur données historiques.
Fait tourner une politique de décision (IA, heuristique…) en backtest.

Auteur : DYXIUM Invest / D.I.A. Core
"""

from dataclasses import dataclass
from typing import Final, Literal

import pandas as pd

from src.dia_core.strategy.decision_policy import DecisionPolicy, TradeDecision
from src.dia_core.risk.risk_manager import RiskManager
from src.dia_core.tracking.trade_logger import TradeLogger, TradeLogEntry

Decision = Literal["buy", "sell", "hold"]


@dataclass(frozen=True, slots=True)
class Regime:
    """Snapshot d`un régime de marché minimal.

    Attributs :
        momentum : variation récente du prix sur une petite fenêtre.
        volatility : volatilité locale (écart-type des rendements récents).
        trend : proxy de tendance (moyenne mobile courte - moyenne complète).
    """

    momentum: float
    volatility: float
    trend: float


class BacktestEngine:
    """Simule du trading sur données historiques avec une politique donnée.

    Le moteur lit un CSV (indexé par 'time'), calcule un petit vecteur de régime
    à chaque pas, interroge la politique pour obtenir une décision, met à jour le
    PnL et journalise le trade. Les helpers gardent la boucle principale simple.

    Paramètres :
        policy : politique de stratégie implémentant `decide(...)`.
        data_path : chemin du CSV OHLC (doit contenir colonnes 'time' et 'close').
        symbol : symbole de trading (ex. "BTC/EUR").
        initial_equity : capital initial de la simulation.
        output_log : chemin optionnel pour le journal JSONL des trades.
    """

    WINDOW: Final[int] = 30

    def __init__(
        self,
        policy: DecisionPolicy,
        data_path: str,
        symbol: str = "BTC/EUR",
        initial_equity: float = 10_000.0,
        output_log: str | None = None,
    ) -> None:
        self.symbol = symbol
        self.policy = policy
        self.equity = initial_equity
        self.ohlc = pd.read_csv(data_path, parse_dates=["time"], index_col="time")
        self.logger = TradeLogger(output_log or f"logs/backtest_{symbol.replace('/', '-')}.jsonl")
        self._open_price: float | None = None
        self._open_side: Decision | None = None

    # ---------------- helpers ----------------

    @staticmethod
    def _compute_regime(window: pd.DataFrame) -> Regime:
        """Calcule le vecteur de régime à partir de la fenêtre courante."""
        mom = (window["close"].iloc[-1] - window["close"].iloc[-5]) / window["close"].iloc[-5]
        vol = window["close"].pct_change().rolling(5).std().iloc[-1]
        trd = float(window["close"].rolling(10).mean().iloc[-1] - window["close"].mean())
        return Regime(momentum=float(mom), volatility=float(vol), trend=trd)

    @staticmethod
    def _last_price(window: pd.DataFrame) -> float:
        """Renvoie le dernier prix de clôture de la fenêtre."""
        return float(window["close"].iloc[-1])

    @staticmethod
    def _signed_size(raw_size: float, decision: Decision) -> float:
        """Ajuste le signe de la taille selon la décision."""
        sign = -1.0 if decision == "sell" else 1.0
        return sign * abs(float(raw_size))

    def _update_pnl(self, price: float, size: float) -> None:
        """Met à jour l`équité à partir de la position ouverte et du prix actuel."""
        if self._open_price is None or self._open_side is None:
            return
        direction = -1.0 if self._open_side == "sell" else 1.0
        pnl = direction * abs(size) * (price - self._open_price)
        self.equity += pnl

    def _set_position(self, price: float, side: Decision) -> None:
        """Enregistre la nouvelle position ouverte."""
        self._open_price = price
        self._open_side = side

    def _log_trade(self, decision: Decision, size: float, price: float) -> None:
        """Journalise un trade simulé dans le TradeLogger."""
        entry = TradeLogEntry(
            self.symbol,
            decision,
            abs(size),
            price,
            "simulé",
            {"equity": self.equity},
        )
        self.logger.log_trade(entry)

    # ---------------- run ----------------

    def run(self) -> None:
        """Rejoue le dataset et applique la politique étape par étape."""
        risk_mgr = RiskManager(capital=self.equity)
        for i in range(self.WINDOW, len(self.ohlc)):
            window = self.ohlc.iloc[i - self.WINDOW : i]
            regime = self._compute_regime(window)
            decision: TradeDecision = self.policy.decide(
                self.symbol,
                window,
                {
                    "momentum": regime.momentum,
                    "volatility": regime.volatility,
                    "trend": regime.trend,
                },
            )

            if decision == "hold":
                continue

            price = self._last_price(window)
            raw_size = float(risk_mgr.compute_size(window))
            size = self._signed_size(raw_size, decision)

            self._update_pnl(price, size)
            self._log_trade(decision, size, price)
            self._set_position(price, decision)
