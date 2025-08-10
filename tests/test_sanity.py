# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : tests/test_sanity.py

Description :
Test unitaire de base ("sanity check") pour verifier que l'environnement
de tests fonctionne correctement. Sert de test de reference minimal.

Auteur : DYXIUM Invest / D.I.A. Core
"""

EXPECTED_SUM = 4


def test_sanity() -> None:
    """Vérifie que la somme 2 + 2 donne bien la valeur attendue."""
    assert EXPECTED_SUM == 2 + 2
