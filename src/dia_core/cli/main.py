from __future__ import annotations
import os
import argparse
import logging
import time
from dotenv import load_dotenv

from dia_core.config.loader import load_config
from dia_core.logging.setup import setup_logging
from dia_core.kraken.client import KrakenClient
from dia_core.exec.executor import Executor
from dia_core.kraken.types import OrderIntent
from dia_core.portfolio import journal
from dia_core.data.provider import load_ohlc_window

from dia_core.alerts.email_alerts import EmailAlerter, EmailConfig
from dia_core.orchestrator.overload_guard import OverloadGuard


def main() -> None:
    # 1) Config email (ex: via .env lus par ta couche config)
    email_cfg = EmailConfig(
        smtp_host="smtp.gmail.com",
        smtp_port=587,  # STARTTLS
        username="fabienmaison.fg@gmail.com",
        password=os.getenv("GMAIL_KEY"),  # récupéré depuis .env
        use_tls=True,
        sender="fabienmaison.fg@gmail.com",  # doit matcher le compte Gmail
        recipients=["fabiengrolier.17@example.com"],
    )
    alerter = EmailAlerter(email_cfg)
    # 2) Garde-fou
    guard = OverloadGuard(alerter)
    # 3) Boucle: après chaque cycle, mesurer la latence moyenne du cycle stratégie
    active_pairs = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "EUR/USD", "GBP/USD"]
    low_priority = ["GBP/USD", "EUR/USD", "SOL/USDT"]  # ordre: à couper en premier

    avg_cycle_latency_ms = 0.0  # <- mesure fournie par ta boucle
    active_pairs = guard.tick(active_pairs, low_priority, avg_cycle_latency_ms)

    parser = argparse.ArgumentParser(prog="dia-core")
    parser.add_argument(
        "--config", default="config.json", help="Chemin vers le fichier de configuration"
    )
    parser.add_argument("--version", action="store_true", help="Afficher la version et quitter")
    args = parser.parse_args()

    if args.version:
        print("DIA-Core V1.0.0a1")
        return

    # Charger .env (clés API)
    load_dotenv()

    # Charger configuration JSON
    cfg = load_config(args.config)

    # Initialiser logging structuré
    setup_logging(cfg.log_dir, level="INFO")

    logging.getLogger(__name__).info(
        "DIA-Core démarré",
        extra={"component": "cli", "mode": cfg.mode, "pair": cfg.pair},
    )

    # Initialiser KrakenClient
    client = KrakenClient()

    # Charger les OHLC (par ex. intervalle 1 minute, 100 dernières bougies)
    df = load_ohlc_window(
        client, pair=cfg.pair, interval=1, window_bars=100, cache_dir=cfg.cache_dir
    )
    print(df.head())

    # Initialiser Executor (dry_run par défaut)
    executor = Executor(
        client,
        mode=cfg.mode,
        min_notional=cfg.exchange.min_notional,
        require_interactive_confirm=cfg.require_interactive_confirm,
    )

    # Ouvrir base SQLite
    conn = journal.open_db(cfg.journal_path)

    # Exemple : soumettre un ordre dry-run
    intent = OrderIntent(symbol=cfg.pair, side="buy", type="limit", qty=0.001, limit_price=20000.0)
    result = executor.submit(intent, equity=1000.0)

    # Enregistrer dans le journal
    journal.insert_order(
        conn,
        {
            "id": result.client_order_id,
            "ts": int(time.time() * 1000),
            "symbol": intent.symbol,
            "side": intent.side,
            "type": intent.type,
            "qty": intent.qty,
            "price": intent.limit_price,
            "status": result.status,
            "reason": result.reason,
        },
    )
    journal.log_event(conn, "INFO", "cli", f"Ordre {result.status} enregistré")

    # Afficher résultat
    print(result.model_dump())


if __name__ == "__main__":
    main()
