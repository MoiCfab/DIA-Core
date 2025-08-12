"""CLI helper functions for DIA-Core.

This module centralises common operations performed by the command-line
interface. These helpers encapsulate ancillary logic such as computing
dynamic risk overrides, sending notifications and writing monitoring
information. By moving these responsibilities out of the CLI entry
points the core functions remain concise and therefore easier to test
and maintain. None of the functions defined here are intended to
perform any business critical computation; they only orchestrate
existing pure logic from other modules and perform I/O when required.

The helpers catch a small set of anticipated exceptions rather than
blanket catching ``Exception``. This aligns with the coding guidelines
prohibiting broad exception handling while still protecting the CLI
from crashing on non-critical issues such as file permission errors.

"""

from __future__ import annotations

import json

from dia_core.alerts.telegram_alerts import load_config_from_env, send as tg_send
from dia_core.cli.run_impl import get_last_window
from dia_core.market_state.regime_vector import compute_regime
from dia_core.monitor.ui_app import build_state
from dia_core.risk.dynamic_manager import adjust as adjust_dynamic_risk

# Minimum number of price samples required to compute a meaningful regime.
MIN_REGIME_WINDOW: int = 5


def compute_dynamic_risk_info(symbol: str, dynamic: bool) -> tuple[float | None, dict[str, float]]:
    """Compute dynamic risk overrides and regime metrics.

    When dynamic risk is enabled the helper will load the most recent
    pricing window, derive the current market regime and use the
    :func:`~dia_core.risk.dynamic_manager.adjust` function to compute a
    k_ATR override. If the window cannot be obtained or is too
    short, no override is produced.

    Args:
        symbol: Trading pair identifier such as ``"BTC/EUR"``.
        dynamic: Whether dynamic risk calculation should be attempted.

    Returns:
        A tuple ``(k_atr_override, regime_dict)``. ``k_atr_override`` is
        either a floating point value or ``None``. ``regime_dict``
        contains human readable regime metrics keyed by metric name.
    """
    if not dynamic:
        return None, {}
    try:
        window = get_last_window(symbol)
        # Only compute a regime when we have enough samples.
        if window is not None and len(window) > MIN_REGIME_WINDOW:
            regime = compute_regime(window)
            metrics: dict[str, float] = {
                "volatility": regime.volatility,
                "momentum": regime.momentum,
                "volume": regime.volume,
                "entropy": regime.entropy,
                "spread": regime.spread,
                "score": regime.score,
            }
            risk = adjust_dynamic_risk(regime)
            return float(risk.k_atr), metrics
    except (RuntimeError, ValueError, OSError):
        # Ignore recoverable errors and fall through to no override.
        pass
    return None, {}


def send_trade_notification(
    mode: str,
    symbol: str,
    side: str | None,
    k_atr_override: float | None,
    enabled: bool,
) -> None:
    """Send a Telegram notification if enabled.

    The message communicates the execution mode, trading symbol, side
    and k_ATR override. Configuration is pulled from environment
    variables via :func:`~dia_core.alerts.telegram_alerts.load_config_from_env`.

    Args:
        mode: Execution mode, e.g. ``"dry_run"``.
        symbol: Trading symbol.
        side: Trade side reported by the strategy. ``None`` when no
            position was taken.
        k_atr_override: Override used for ATR-based sizing. ``None``
            indicates an automatic value.
        enabled: Set to ``True`` to actually send the notification.
    """
    if not enabled:
        return
    cfg = load_config_from_env()
    if not cfg:
        return
    side_str = "None" if side is None else side
    k_atr_str = "auto" if k_atr_override is None else str(k_atr_override)
    msg = f"DIA-Core {mode} {symbol} — side={side_str} k_atr={k_atr_str}"
    try:
        tg_send(cfg, msg)
    except (RuntimeError, ValueError, OSError):
        # Notification failures are non blocking.
        return


def write_monitor_state(
    symbol: str,
    regime: dict[str, float],
    k_atr: float,
    last_side: str | None,
    path: str,
) -> None:
    """Write the latest monitor state to disk.

    When a monitor file is provided this helper uses the
    :func:`~dia_core.monitor.ui_app.build_state` factory to assemble a
    serialisable state and persists it as a single JSON object.

    Args:
        symbol: Trading pair.
        regime: Regime metrics as returned by
            :func:`compute_dynamic_risk_info`.
        k_atr: k_ATR override to persist, ``0.0`` when not available.
        last_side: Side returned by the strategy.
        path: Filesystem path to write the monitor file. When empty
            nothing is written.
    """
    if not path:
        return
    try:
        state = build_state(symbol=symbol, regime=regime, k_atr=k_atr, last_side=last_side)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "symbol": state.symbol,
                    "regime": state.regime,
                    "k_atr": state.k_atr,
                    "last_side": state.last_side,
                },
                handle,
            )
    except (OSError, ValueError):
        # Fail silently if the monitor cannot be written.
        return


def append_monitor_line(
    symbol: str, last_side: str | None, k_atr_override: float | None, path: str
) -> None:
    """Append a single trade record to a monitor log file.

    This helper is intended for the orchestration flow where multiple
    symbols are processed in a batch. Each invocation writes a JSON
    object on its own line, facilitating line oriented log parsing.

    Args:
        symbol: Trading symbol.
        last_side: Reported side of the trade or ``None``.
        k_atr_override: k_ATR override used for the trade.
        path: Monitor file path. When empty or ``False`` nothing is
            written.
    """
    if not path:
        return
    entry = {
        "symbol": symbol,
        "last_side": last_side,
        "k_atr": k_atr_override,
    }
    try:
        with open(path, "a", encoding="utf-8") as handle:
            json.dump(entry, handle)
            handle.write("\n")
    except (OSError, ValueError):
        return
