# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

"""
Nom du module : data/cache.py

Description :
Gestion simple du cache local des fenêtres OHLC au format Parquet.
Le cache est facultatif : si le support Parquet n`est pas disponible (pyarrow/fastparquet),
les opérations de lecture/écriture sont ignorées proprement avec journalisation.

Utilisé par :
    data/provider.py (chargement de fenêtres OHLC avec fallback réseau)
    cli/main.py (exécution de démonstration et tests locaux)

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def cache_path(cache_dir: str, pair: str, interval: int) -> Path:
    """Construit le chemin du fichier Parquet pour une paire et un intervalle.

    Args :
        cache_dir : Répertoire racine du cache.
        pair : Symbole de la paire, ex. "BTC/EUR".
        interval : Intervalle en minutes (ex. 1, 5, 60).

    Returns :
        Chemin absolu du fichier Parquet (création du répertoire si nécessaire).

    Notes :
        Les caractères "/" sont remplacés par "_" pour produire un nom de fichier sûr.

    Args:
      cache_dir: str:
      pair: str:
      interval: int:
      cache_dir: str:
      pair: str:
      interval: int:

    Returns:

    """
    p = Path(cache_dir)
    p.mkdir(parents=True, exist_ok=True)
    safe = pair.replace("/", "_")
    return p / f"{safe}_{interval}.parquet"


def load_cache(cache_dir: str, pair: str, interval: int) -> pd.DataFrame | None:
    """Lit une fenêtre OHLC depuis le cache Parquet si disponible.

    Le chargement est optionnel : si le fichier n`existe pas ou si le support Parquet
    n`est pas installé/valide, la fonction retourne `None` sans élever d`exception.

    Args :
        cache_dir : Répertoire racine du cache.
        pair : Symbole de la paire (ex. "BTC/EUR").
        interval : Intervalle en minutes (ex. 1, 5, 60).

    Returns :
        Un "pd.DataFrame" si la lecture a réussi, sinon "None".

    Journalisation :
        INFO si la lecture est ignorée (par exemple absence de pyarrow/fastparquet ou
        fichier illisible).

    Exemple :
        df = load_cache("state/cache", "BTC/EUR", 1)
        df is None or isinstance(df, pd.DataFrame)
        True

    Args:
      cache_dir: str:
      pair: str:
      interval: int:
      cache_dir: str:
      pair: str:
      interval: int:

    Returns:

    """
    path = cache_path(cache_dir, pair, interval)
    if not path.exists():
        return None
    try:
        return pd.read_parquet(path)
    except (ImportError, ValueError) as e:
        logger.info("Parquet indisponible/illisible, skip read (%s): %s", path, e)
        return None


def save_cache(cache_dir: str, pair: str, interval: int, df: pd.DataFrame) -> None:
    """Écrit une fenêtre OHLC dans le cache Parquet si le support est disponible.

    L`écriture est optionnelle : en cas d`absence de moteur Parquet (pyarrow/fastparquet)
    ou d`erreur de sérialisation, la fonction journalise et n`élève pas d`exception.

    Args :
        cache_dir : Répertoire racine du cache.
        pair : Symbole de la paire (ex. "BTC/EUR").
        interval : Intervalle en minutes (ex. 1, 5, 60).
        df : Données OHLC à persister (colonnes attendues alignées avec provider).

    Journalisation :
        INFO si l`écriture est ignorée (absence de moteur Parquet, erreur de format).

    Args:
      cache_dir: str:
      pair: str:
      interval: int:
      df: pd.DataFrame:
      cache_dir: str:
      pair: str:
      interval: int:
      df: pd.DataFrame:

    Returns:

    """
    path = cache_path(cache_dir, pair, interval)
    try:
        df.to_parquet(path, index=False)
    except (ImportError, ValueError) as e:
        logger.info("Parquet indisponible, skip write (%s): %s", path, e)
