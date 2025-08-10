# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : tests/test_cache_provider.py

Description :
Test unitaire de la fonction ohlc_dataframe du module data/provider.py.
Vérifie que la conversion d'un payload OHLC en DataFrame fonctionne
correctement et retourne les colonnes attendues.

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations

import pandas as pd
from dia_core.data.provider import ohlc_dataframe


def test_ohlc_dataframe_basic() -> None:
    """Teste la creation d'un DataFrame OHLC basique.

    Vérifie :
        que le résultat est bien un DataFrame pandas
        que les premieres colonnes correspondent à ["time", "open", "high", "low", "close"]
        que la longueur du DataFrame correspond au nombre de lignes du payload
    """
    payload = {"XXBTZEUR": [[1710000000, 1, 2, 0.5, 1.5, 1.2, 10.0, 42]]}
    df = ohlc_dataframe("XXBTZEUR", {**payload})
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns)[:5] == ["time", "open", "high", "low", "close"]
    assert len(df) == 1
