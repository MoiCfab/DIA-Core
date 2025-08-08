from __future__ import annotations


class RiskLimitExceeded(RuntimeError):
    """Le trade viole au moins une limite de risque (hard-stop)."""
