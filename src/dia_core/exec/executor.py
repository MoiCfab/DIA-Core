from __future__ import annotations

import logging
import uuid
from typing import Literal

from dia_core.kraken.client import KrakenClient
from dia_core.kraken.types import OrderIntent, SubmittedOrder
from dia_core.config.models import RiskLimits as ConfigRiskLimits
from dia_core.exec.pre_trade import pre_trade_checks

logger = logging.getLogger(__name__)
Mode = Literal["dry_run", "paper", "live"]


class Executor:
    def __init__(
        self,
        client: KrakenClient,
        mode: Mode = "dry_run",
        min_notional: float = 10.0,
        limits: ConfigRiskLimits | None = None,
        require_interactive_confirm: bool = True,
    ):
        self.client = client
        self.mode = mode
        self.min_notional = min_notional
        # Utilise le modèle de config (attendu par pre_trade_checks / validate_order)
        self.limits: ConfigRiskLimits = limits or ConfigRiskLimits()
        self.require_interactive_confirm = require_interactive_confirm

    def _confirm_live(self) -> None:
        if self.mode == "live" and self.require_interactive_confirm:
            answer = input("LIVE MODE: tapez 'YES' pour confirmer : ").strip()
            if answer != "YES":
                raise SystemExit("Live submission annulée par l'utilisateur.")

    def submit(self, intent: OrderIntent, equity: float) -> SubmittedOrder:
        # Validation risque (hard-stop)
        res = pre_trade_checks(intent, self.limits, equity, self.min_notional)
        if not res.allowed:
            logger.warning(
                "Ordre refusé",
                extra={"extra": {"component": "executor", "reason": res.reason}},
            )
            return SubmittedOrder(
                client_order_id=str(uuid.uuid4()),
                status="rejected",
                reason=res.reason,
            )

        if self.mode == "dry_run":
            logger.info(
                "Dry-run : ordre simulé",
                extra={"extra": {"component": "executor"}},
            )
            return SubmittedOrder(client_order_id=str(uuid.uuid4()), status="accepted")

        if self.mode == "paper":
            logger.info(
                "Paper : ordre enregistré (pas d'envoi exchange)",
                extra={"extra": {"component": "executor"}},
            )
            return SubmittedOrder(client_order_id=str(uuid.uuid4()), status="accepted")

        # LIVE MODE
        self._confirm_live()
        payload = {
            "pair": intent.symbol,
            "type": intent.side,
            "ordertype": intent.type,
            "volume": f"{intent.qty}",
            "validate": "true",  # Kraken dry-run interne pour sécuriser
        }
        if intent.type == "limit" and intent.limit_price:
            payload["price"] = f"{intent.limit_price}"

        self.client.add_order(payload)
        logger.info(
            "Ordre validé par Kraken (validate=true)",
            extra={"extra": {"component": "executor"}},
        )
        return SubmittedOrder(client_order_id=str(uuid.uuid4()), status="accepted")
