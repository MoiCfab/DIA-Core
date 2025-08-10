# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

"""
Nom du module : data/provider.py

Description :
Fonctions de préparation et de chargement des fenêtres OHLC à partir de l`API Kraken,
avec cache local optionnel au format Parquet. Ce module convertit la réponse JSON
en `DataFrame` propre (typée) et assure le découpage à une taille de fenêtre donnée.

Utilisé par :
    cli/main.py (exemple de lancement)
    strategies/* (indicateurs / contexte marché)

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
from dia_core.data.cache import load_cache, save_cache
from dia_core.kraken.client import KrakenClient

logger = logging.getLogger(__name__)


def ohlc_dataframe(result: dict[str, Any], pair: str) -> pd.DataFrame:
    """Convertit la réponse OHLC Kraken en `DataFrame` typé.

    Args :
        result : Dictionnaire retourné par l`API Kraken (`"result": {PAIR_KEY: [...]}`).
        pair: Paire demandée (ex. "BTC/EUR"). Utilisée seulement pour la validation/erreurs.

    Returns :
        Un `DataFrame` avec colonnes : ``time, open, high, low, close, vwap, volume, count``.

    Raises :
        ValueError: Si la structure `result` est vide ou inattendue.

    Notes :
        - Les types numériques sont forcés en float64 / int64 pour garantir la compatibilité
          avec les indicateurs.
        - La colonne `time` est fournie en millisecondes (int64).
    """
    key = next(iter(result.keys()), None)
    if key is None:
        raise ValueError("OHLC result dict is vide")
    rows = result[key]
    cols = ["time", "open", "high", "low", "close", "vwap", "volume", "count"]
    df = pd.DataFrame(rows, columns=cols)
    df = df.astype(
        {
            "time": "int64",
            "open": "float64",
            "high": "float64",
            "low": "float64",
            "close": "float64",
            "volume": "float64",
        }
    )
    return df


def load_ohlc_window(
    client: KrakenClient, pair: str, interval: int, window_bars: int, cache_dir: str
) -> pd.DataFrame:
    """Charge une fenêtre OHLC depuis le cache ou l`API Kraken.

    La fonction tente d`abord de lire le cache Parquet local. Si le cache est absent
    ou insuffisant (< "window_bars"), elle télécharge depuis Kraken, convertit
    le JSON en "DataFrame", tronque à la taille souhaitée, puis met à jour le cache.

    Args :
        client : Client Kraken initialisé (transport HTTP et clés si besoin).
        pair : Paire (ex. "BTC/EUR").
        interval : Intervalle en minutes (1, 5, 15, 60, ...).
        window_bars : Nombre de bougies à retourner.
        cache_dir : Répertoire racine du cache Parquet.

    Returns :
        Un `DataFrame` OHLC propre, de longueur ≤ "window_bars", index réinitialisé.

    Journalisation :
        INFO lors d`un téléchargement depuis l`API (cache manquant/insuffisant).
    """
    df = load_cache(cache_dir, pair, interval)
    if df is None or len(df) < window_bars:
        logger.info("Téléchargement OHLC depuis Kraken", extra={"component": "data", "pair": pair})
        res = client.get_ohlc(pair, interval=interval)
        df = ohlc_dataframe(res, pair)
        df = df.tail(window_bars).reset_index(drop=True)
        save_cache(cache_dir, pair, interval, df)
    else:
        df = df.tail(window_bars).reset_index(drop=True)
    return df
