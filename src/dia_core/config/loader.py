from __future__ import annotations
import json
from pydantic import ValidationError
from .models import AppConfig

def load_config(path: str) -> AppConfig:
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        raise SystemExit(f"[CONFIG] Fichier introuvable : {path}")
    except json.JSONDecodeError as e:
        raise SystemExit(f"[CONFIG] Erreur JSON dans {path} : {e}")

    try:
        return AppConfig(**raw)
    except ValidationError as e:
        raise SystemExit(f"[CONFIG] Configuration invalide :\n{e}") from e
