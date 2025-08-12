"""Module src/dia_core/cli/main.py."""

# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

from __future__ import annotations

import argparse
from collections.abc import Sequence
from contextlib import suppress
import json
import os
from typing import Any, cast

from dia_core.alerts.formatters import SymbolSummary
from dia_core.alerts.notify import notify_summary
from dia_core.cli.run_impl import run_once
from dia_core.logging.setup import setup_logging
from dia_core.orchestrator.scheduler import SchedulerConfig, run_batch

# Import helper functions to keep CLI handlers concise.
from dia_core.cli.helpers import (
    compute_dynamic_risk_info,
    send_trade_notification,
    write_monitor_state,
    append_monitor_line,
)

_MIN_REG_WINDOW = 5


def build_parser() -> argparse.ArgumentParser:
    """Construit le parser CLI et sous-commandes."""
    parser = argparse.ArgumentParser("dia-core")
    parser.add_argument("--config", default="", help="Chemin du fichier de configuration JSON")
    sub = parser.add_subparsers(dest="cmd", required=False)

    p_run = sub.add_parser("run", help="Exécuter le bot en mode dry_run/paper/live")
    p_run.add_argument("mode", choices=["dry_run", "paper", "live"], help="Mode d'exécution")
    p_run.add_argument("symbol", nargs="?", default="BTC/EUR", help="Symbole ex: BTC/EUR")
    p_run.add_argument(
        "--dynamic-risk",
        action="store_true",
        help="Activer le risque dynamique (V3)",
    )
    p_run.add_argument(
        "--monitor-file",
        default=os.environ.get("DIA_MONITOR_FILE", ""),
        help="Chemin JSON monitor (optionnel)",
    )
    p_run.add_argument(
        "--telegram",
        action="store_true",
        help="Notifications Telegram si configurées",
    )

    p_orch = sub.add_parser("orchestrate", help="Planifier plusieurs paires (V3)")
    p_orch.add_argument("mode", choices=["dry_run", "paper", "live"], help="Mode d'exécution")
    p_orch.add_argument("symbols", help="Liste de paires séparées par des virgules")
    p_orch.add_argument("--max-workers", type=int, default=2)
    p_orch.add_argument("--dynamic-risk", action="store_true")
    p_orch.add_argument("--monitor-file", default=os.environ.get("DIA_MONITOR_FILE", ""))
    p_orch.add_argument("--telegram", action="store_true")

    return parser


def _maybe_notify_telegram(msg: str) -> None:
    """Envoie `msg` sur Telegram si la config env est présente.

    Args:
        msg: Texte à envoyer.
    """
    # import paresseux pour ne pas forcer la dépendance en l'absence de config
    from dia_core.alerts.telegram_alerts import (
        load_config_from_env,
        TgConfig,
        send,
    )  # pylint: disable=import-outside-toplevel

    cfg: TgConfig | None = load_config_from_env()
    if not getattr(cfg, "token", None) or not getattr(cfg, "chat_id", None):
        return
    if cfg is not None:
        send(cfg, msg)


def _maybe_write_monitor(
    symbol: str,
    *,
    regime: dict[str, float],
    k_atr: float,
    last_side: str | None,
    path: str,
) -> None:
    """

    Args:
      symbol: str:
      *:
      regime: dict[str:
      float]:
      k_atr: float:
      last_side: str | None:
      path: str:
      symbol: str:
      regime: dict[str:
      k_atr: float:
      last_side: str | None:
      path: str:

    Returns:

    """
    # Deprecated wrapper retained for backwards compatibility. Delegates
    # to the helpers module for monitor persistence.
    write_monitor_state(symbol, regime, k_atr, last_side, path)


def _handle_run(args: argparse.Namespace) -> int:
    """

    Args:
      args: argparse.Namespace:
      args: argparse.Namespace:

    Returns:

    """

    dyn: bool = bool(args.dynamic_risk)
    mon_path: str = str(args.monitor_file or "")
    notify_enabled: bool = bool(args.telegram)

    # Fast path when no dynamic risk, no monitoring and no notification.
    if not dyn and not mon_path and not notify_enabled:
        ok, _ = run_once(mode=args.mode, symbol=args.symbol)
        return 0 if ok else 1

    k_atr_override, regime_dict = compute_dynamic_risk_info(args.symbol, dyn)
    ok, side = run_once(mode=args.mode, symbol=args.symbol, k_atr_override=k_atr_override)
    # Send a notification if requested.
    send_trade_notification(args.mode, args.symbol, side, k_atr_override, notify_enabled)
    # Persist monitor state if a file path was supplied.
    write_monitor_state(
        args.symbol,
        regime_dict,
        k_atr=(k_atr_override or 0.0),
        last_side=side,
        path=mon_path,
    )
    return 0 if ok else 1


def _handle_orchestrate(args: argparse.Namespace) -> int:
    """

    Args:
      args: argparse.Namespace:
      args: argparse.Namespace:

    Returns:

    """

    # Split the symbols argument into individual entries, ignoring
    # whitespace and empty strings.
    syms: Sequence[str] = [s.strip() for s in str(args.symbols).split(",") if s.strip()]

    def worker(symbol: str) -> None:
        """Process a single symbol during orchestration.

        The worker encapsulates the per symbol logic: computing a
        dynamic k_ATR override when requested, running the trading loop
        once, sending a notification and appending a line to the
        monitor file. It intentionally avoids capturing the outer
        ``args`` structure directly, instead copying only the values
        it needs into local variables to aid type checking and reduce
        complexity.

        Args:
            symbol: The trading pair to process.
        """
        dynamic_enabled = bool(args.dynamic_risk)
        telegram_enabled = bool(args.telegram)
        monitor_path = str(args.monitor_file or "")

        # Compute a dynamic risk override for this symbol if requested.
        k_atr_override, _ = compute_dynamic_risk_info(symbol, dynamic_enabled)
        ok, side = run_once(mode=args.mode, symbol=symbol, k_atr_override=k_atr_override)
        _ = ok  # Result is ignored for orchestration flows.
        # Send Telegram notification if enabled.
        send_trade_notification(args.mode, symbol, side, k_atr_override, telegram_enabled)
        # Append the result to the monitor file for aggregation.
        append_monitor_line(symbol, side, k_atr_override, monitor_path)

    cfg = SchedulerConfig(max_workers=int(args.max_workers))
    # Execute the batch using the scheduler. The scheduler will report
    # individual job errors via its returned results.
    run_batch(syms, worker=worker, cfg=cfg)

    # After the batch we send a global summary notification via the
    # existing API. The summary currently contains only a placeholder
    # structure; additional information could be propagated here.
    with suppress(Exception):  # pragma: no cover
        summaries: list[SymbolSummary] = []
        sym = args.symbol
        summaries.append(
            SymbolSummary(
                symbol=sym,
                side=None,
                k_atr=None,
                sharpe=None,
                sortino=None,
                max_dd=None,
                delta_eq_pct=None,
                regime_score=None,
                regime_mom=None,
                regime_vol=None,
            )
        )
        notify_summary(args.mode, summaries)
    return 0


def _load_cfg(path: str) -> dict[str, Any] | None:
    """

    Args:
      path: str:
      path: str:

    Returns:

    """
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cast(dict[str, Any], data) if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _handle_default_from_config(args: argparse.Namespace) -> int:
    """

    Args:
      args: argparse.Namespace:
      args: argparse.Namespace:

    Returns:

    """

    cfg = _load_cfg(str(args.config))
    mode = (cfg or {}).get("mode", "dry_run")
    symbol = ((cfg or {}).get("exchange") or {}).get("symbol", "BTC/EUR")
    ok, _ = run_once(mode=mode, symbol=symbol)
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    """

    Args:
      argv: list[str] | None:  (Default value = None)
      argv: list[str] | None:  (Default value = None)

    Returns:

    """
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.cmd:
        return _handle_default_from_config(args)
    setup_logging(log_dir=os.environ.get("DIA_LOG_DIR", "Logs"))

    if args.cmd == "run":
        return _handle_run(args)
    if args.cmd == "orchestrate":
        return _handle_orchestrate(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
