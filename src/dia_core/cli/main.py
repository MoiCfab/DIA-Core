# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from contextlib import suppress
from typing import Any, cast

from dia_core.alerts.telegram_alerts import load_config_from_env
from dia_core.alerts.telegram_alerts import send as tg_send
from dia_core.logging.setup import setup_logging
from dia_core.market_state.regime_vector import compute_regime
from dia_core.monitor.ui_app import build_state
from dia_core.orchestrator.scheduler import SchedulerConfig, run_batch
from dia_core.risk.dynamic_manager import adjust as adjust_dynamic_risk

_MIN_REG_WINDOW = 5


def build_parser() -> argparse.ArgumentParser:
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
    cfg = load_config_from_env()
    if not cfg:
        return
    with suppress(Exception):
        tg_send(cfg, msg)


def _maybe_write_monitor(
    symbol: str, *, regime: dict[str, float], k_atr: float, last_side: str | None, path: str
) -> None:
    if not path:
        return
    with suppress(Exception):
        state = build_state(symbol=symbol, regime=regime, k_atr=k_atr, last_side=last_side)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "symbol": state.symbol,
                    "regime": state.regime,
                    "k_atr": state.k_atr,
                    "last_side": state.last_side,
                },
                f,
            )


def _handle_run(args: argparse.Namespace) -> int:
    from dia_core.cli.run_impl import get_last_window, run_once

    dyn = bool(args.dynamic_risk)
    mon_path = str(args.monitor_file or "")
    notify = bool(args.telegram)

    if not dyn and not mon_path and not notify:
        ok, _ = run_once(mode=args.mode, symbol=args.symbol)
        return 0 if ok else 1

    k_atr_override: float | None = None
    regime_dict: dict[str, float] = {}
    with suppress(Exception):
        window = get_last_window(symbol=args.symbol)
        if dyn and window is not None and len(window) > _MIN_REG_WINDOW:
            reg = compute_regime(window)
            regime_dict = {
                "volatility": reg.volatility,
                "momentum": reg.momentum,
                "volume": reg.volume,
                "entropy": reg.entropy,
                "spread": reg.spread,
                "score": reg.score,
            }
            k_atr_override = float(adjust_dynamic_risk(reg).k_atr)

    ok, side = run_once(mode=args.mode, symbol=args.symbol, k_atr_override=k_atr_override)
    if notify:
        msg = (
            f"DIA-Core {args.mode} {args.symbol} — side={side} "
            f"k_atr={k_atr_override if k_atr_override is not None else 'auto'}"
        )
        _maybe_notify_telegram(msg)
    _maybe_write_monitor(
        args.symbol,
        regime=regime_dict,
        k_atr=(k_atr_override or 0.0),
        last_side=side,
        path=mon_path,
    )
    return 0 if ok else 1


def _handle_orchestrate(args: argparse.Namespace) -> int:
    from dia_core.cli.run_impl import get_last_window, run_once

    syms: Sequence[str] = [s.strip() for s in str(args.symbols).split(",") if s.strip()]

    def _worker(sym: str) -> None:
        k_atr_override: float | None = None
        if args.dynamic_risk:
            with suppress(Exception):
                window = get_last_window(symbol=sym)
                if window is not None and len(window) > _MIN_REG_WINDOW:
                    reg = compute_regime(window)
                    k_atr_override = float(adjust_dynamic_risk(reg).k_atr)
        ok, side = run_once(mode=args.mode, symbol=sym, k_atr_override=k_atr_override)
        if args.telegram:
            msg = (
                f"DIA-Core {args.mode} {sym} — side={side} "
                f"k_atr={k_atr_override if k_atr_override is not None else 'auto'}"
            )
            _maybe_notify_telegram(msg)
        if args.monitor_file:
            with suppress(Exception), open(args.monitor_file, "a", encoding="utf-8") as f:
                json.dump({"symbol": sym, "last_side": side, "k_atr": k_atr_override}, f)
                f.write("\n")

    cfg = SchedulerConfig(max_workers=int(args.max_workers))
    run_batch(syms, worker=_worker, cfg=cfg)
    return 0


def _load_cfg(path: str) -> dict[str, Any] | None:
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cast(dict[str, Any], data) if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _handle_default_from_config(args: argparse.Namespace) -> int:
    from dia_core.cli.run_impl import run_once

    cfg = _load_cfg(str(args.config))
    mode = (cfg or {}).get("mode", "dry_run")
    symbol = ((cfg or {}).get("exchange") or {}).get("symbol", "BTC/EUR")
    ok, _ = run_once(mode=mode, symbol=symbol)
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
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
