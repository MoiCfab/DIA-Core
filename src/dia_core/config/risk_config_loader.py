"""
Nom du module : config/risk_config_loader.py

Description :
Charge la configuration `RiskLimits` depuis un fichier YAML centralisé.
Gère les cas où une paire est absente avec des valeurs par défaut sûres.

Auteur : DYXIUM Invest / D.I.A. Core
"""

import yaml
from typing import TypedDict


# Définit les clés attendues pour une configuration de risque
class RiskLimits(TypedDict):
    max_drawdown_pct: float
    max_exposure_pct: float
    risk_per_trade: float
    stop_loss_pct: float


# Valeurs par défaut sécurisées si la paire n'est pas configurée
DEFAULT_LIMITS: RiskLimits = {
    "max_drawdown_pct": 15.0,
    "max_exposure_pct": 20.0,
    "risk_per_trade": 0.01,
    "stop_loss_pct": 5.0,
}


def load_risk_limits(path: str = "config/risk_limits.yaml") -> dict[str, RiskLimits]:
    """Charge toutes les limites de risque par symbole."""
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data or {}
    except FileNotFoundError:
        print(f"⚠️ Fichier {path} introuvable. Utilisation des valeurs par défaut.")
        return {}


def get_risk_limits_for(symbol: str, config: dict[str, RiskLimits]) -> RiskLimits:
    """
    Récupère la configuration de risque pour une paire donnée.

    Args:
        symbol: Symbole à chercher (ex: BTC/EUR)
        config: Dictionnaire complet des RiskLimits chargés

    Returns:
        RiskLimits: limites applicables à cette paire
    """
    if symbol in config:
        return config[symbol]

    print(f"⚠️ Aucune config de risque pour {symbol} → fallback utilisé.")
    return DEFAULT_LIMITS.copy()
