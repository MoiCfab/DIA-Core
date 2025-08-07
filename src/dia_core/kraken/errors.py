class KrakenError(Exception):
    """Erreur générique Kraken."""
    pass

class KrakenNetworkError(KrakenError):
    """Erreur réseau ou serveur Kraken."""
    pass

class KrakenRateLimit(KrakenError):
    """Trop de requêtes envoyées."""
    pass

class KrakenAuthError(KrakenError):
    """Problème d'authentification API."""
    pass

class KrakenRejectedOrder(KrakenError):
    """Ordre refusé par Kraken."""
    pass
