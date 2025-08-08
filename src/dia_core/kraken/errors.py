from __future__ import annotations


class ConnectivityError(RuntimeError):
    """Erreurs réseau (timeout, DNS, 5xx après retries)."""


class RateLimitError(RuntimeError):
    """HTTP 429 (rate limit) ou message équivalent côté Kraken."""


class AuthError(RuntimeError):
    """HTTP 401/403 ou auth invalide côté Kraken."""


class OrderRejected(RuntimeError):
    """Rejet d'ordre renvoyé par l'API (payload['error'] non vide)."""


class RiskLimitExceeded(RuntimeError):
    """Le trade viole au moins une limite de risque (hard-stop)."""