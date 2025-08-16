# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : orchestrator/market_scanner.py

Description :
Composant responsable de déterminer les paires à analyser.
Peut être implémenté avec ou sans IA.
Ici, version simple renvoyant une liste statique ou paramétrée.

Utilisé par :
    orchestrator/orchestrator.py

Auteur : DYXIUM Invest / D.I.A. Core
"""


class MarketScanner:
    """Sélectionneur de symboles à surveiller/trader."""

    def __init__(self, limit: int = 5) -> None:
        """
        Initialise le scanner.

        Args:
          limit: int:
            Nombre maximum de symboles à retourner.
        """
        self.limit = limit

    def get_symbols(self) -> list[str]:
        """
        Retourne une liste de symboles à traiter.

        Cette version retourne un sous-ensemble statique,
        mais peut être remplacée par un scanner IA dynamique.

        Returns :
          List[str] : Liste de paires ex : ["BTC/EUR", "ETH/EUR"]
        """
        universe = [
            "BTC/EUR",
            "ETH/EUR",
            "SOL/EUR",
            "ADA/EUR",
            "XRP/EUR",
            "LINK/EUR",
            "DOGE/EUR",
        ]
        return universe[: self.limit]
