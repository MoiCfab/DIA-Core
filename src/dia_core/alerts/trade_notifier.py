# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : alerts/trade_notifier.py

Description :
Composant unifié de notification et journalisation des trades.
Utilise Telegram si configuré, et écrit dans le log officiel du bot.

Utilisé par :
    - BotEngine
    - KrakenExecutor
    - BacktestEngine

Auteur : DYXIUM Invest / D.I.A. Core
"""
from contextlib import suppress
from typing import Any

from src.dia_core.tracking.trade_logger import TradeLogger
from src.dia_core.alerts.telegram_alerts import send as send_telegram, TgConfig

from src.dia_core.tracking.trade_logger import TradeLogEntry


class TradeNotifier:
    """Notifier unifié pour chaque trade exécuté."""

    def __init__(
        self,
        symbol: str,
        notify_telegram: bool = True,
        tg_config: TgConfig | None = None,
        log_path: str = "logs/trade_log.jsonl",
    ) -> None:
        """
        Initialise le notifier.

        Args:
            symbol: str:
                Symbole concerné (ex: "BTC/EUR")
            notify_telegram: bool:
                Active ou non l`envoi vers Telegram
            log_path: str:
                Chemin du fichier de journalisation des trades
        """
        self.symbol = symbol
        self.notify_telegram = notify_telegram
        self.tg_config = tg_config
        self.logger = TradeLogger(log_path)

    def notify(
        self,
        action: str,
        size: float,
        price: float,
        status: str = "executed",
        meta: dict[str, Any] | None = None,
    ) -> None:
        """
        Notifie un trade : console + Telegram + log.

        Args:
            action: str:
                Action réalisée ("buy", "sell")
            size: float:
                Taille de l`ordre
            price: float:
                Prix exécuté
            status: str:
                "executed", "simulated" ou autre statut
            meta: dict | None:
                Détails supplémentaires à enregistrer

        Returns:
            None
        """
        msg = f"🔔 {self.symbol} → {action.upper()} x {size:.4f} @ {price:.2f} ({status})"

        if self.notify_telegram:
            with suppress(Exception):
                send_telegram(self.tg_config, msg)

        entry = TradeLogEntry(
            symbol=self.symbol,
            action=action,
            size=size,
            price=price,
            status=status,
            meta=meta,
        )
        self.logger.log_trade(entry)
