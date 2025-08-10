# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

"""
Nom du module : config/loader.py

Description :
Charge et valide la configuration principale de DIA-Core à partir d`un fichier JSON.
Le fichier est transformé en instance de `AppConfig` (modèle Pydantic), avec
vérification stricte des types et des valeurs.

Fonctions principales :
- `load_config` : ouvre le fichier, parse le JSON, valide les données via Pydantic.

Utilisé par :
    main.py (point d'entrée CLI)
    Services ou scripts qui doivent initialiser DIA-Core avec des paramètres externes

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations

import json

from pydantic import ValidationError

from .models import AppConfig


def load_config(path: str) -> AppConfig:
    """Charge la configuration JSON et retourne un objet "AppConfig".

    Args :
        path : Chemin vers le fichier de configuration JSON.

    Returns :
        Une instance validée de "AppConfig".

    Raises :
        SystemExit : Si le fichier est introuvable,
            si le JSON est invalide,
            si le format racine n'est pas un objet JSON,
            ou si la validation Pydantic échoue.

    Exemple :
            cfg = load_config("config.json")
            cfg.mode
        'dry_run'
    """
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError as e:
        raise SystemExit(f"[CONFIG] Fichier introuvable : {path}") from e
    except json.JSONDecodeError as e:
        raise SystemExit(f"[CONFIG] Erreur JSON dans {path} : {e}") from e

    if not isinstance(raw, dict):
        raise SystemExit("[CONFIG] Format JSON inattendu : un objet est requis à la racine")

    try:
        return AppConfig(**raw)
    except ValidationError as e:
        raise SystemExit(f"[CONFIG] Configuration invalide :\n{e}") from e
