# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / DIA-Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du module : kraken/errors.py

Description :
Definit les exceptions spécifiques a l'utilisation de l'API Kraken dans DIA-Core.
Ces exceptions permettent de différencier clairement les erreurs de connectivité,
de limitation de requêtes, d'authentification et de rejet d'ordres.

Utilise par :
    kraken/client.py (gestion des réponses et erreurs)
    autres modules effectuant des appels API Kraken

Auteur : DYXIUM Invest / D.I.A. Core
"""

from __future__ import annotations


class ConnectivityError(RuntimeError):
    """Erreur de connectivité (timeout, DNS, ou codes HTTP 5xx apres retries)."""


class RateLimitError(RuntimeError):
    """Erreur de limitation de requêtes (HTTP 429 ou message equivalent Kraken)."""


class AuthError(RuntimeError):
    """Erreur d'authentification (HTTP 401/403 ou credentials invalides Kraken)."""


class OrderRejectedError(RuntimeError):
    """Rejet d'ordre par l'API (payload['error'] non vide dans la réponse Kraken)."""
