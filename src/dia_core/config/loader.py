from __future__ import annotations
import json
from pydantic import ValidationError
from .models import AppConfig


def load_config(path: str) -> AppConfig:
    try:
        with open(path, "r", encoding="utf-8") as f:
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
