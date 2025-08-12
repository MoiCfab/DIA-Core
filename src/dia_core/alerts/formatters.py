"""Module src/dia_core/alerts/formatters.py."""

# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class SymbolSummary:
    """Conteneur des champs affichés dans les messages."""

    symbol: str
    side: str | None
    k_atr: float | None
    sharpe: float | None = None
    sortino: float | None = None
    max_dd: float | None = None
    delta_eq_pct: float | None = None
    regime_score: float | None = None
    regime_mom: float | None = None
    regime_vol: float | None = None


def _fmt_pct(x: float | None, *, plus: bool = True) -> str:
    """

    Args:
      x: float | None:
      *:
      plus: bool:  (Default value = True)
      x: float | None:
      plus: bool:  (Default value = True)

    Returns:

    """
    if x is None:
        return "n/a"
    s = f"{x:+.1f}%" if plus else f"{x:.1f}%"
    return s


def render_subject(mode: str, items: list[SymbolSummary]) -> str:
    """

    Args:
      mode: str:
      items: list[SymbolSummary]:
      mode: str:
      items: list[SymbolSummary]:

    Returns:

    """
    ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%MZ")
    # Sujet compact: prend le 1er symbole
    head = items[0] if items else None
    delta = _fmt_pct(head.delta_eq_pct) if head else "n/a"
    sharpe = f"{head.sharpe:.2f}" if head and head.sharpe is not None else "n/a"
    dd = _fmt_pct((head.max_dd or 0.0), plus=False) if head else "n/a"
    sym = head.symbol if head else "-"
    return f"[DIA-Core] {mode} {sym} — ΔEq {delta} | Sharpe {sharpe} | DD {dd} | {ts}"


def render_text(mode: str, items: list[SymbolSummary]) -> str:
    """

    Args:
      mode: str:
      items: list[SymbolSummary]:
      mode: str:
      items: list[SymbolSummary]:

    Returns:

    """
    ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%MZ")
    lines = [
        f"DIA-Core — {mode} — {ts}",
        f"Symboles: {', '.join(i.symbol for i in items)}",
        "",
    ]
    for it in items:
        line1 = (
            f"{it.symbol}: side={it.side or '-'} | k_atr={it.k_atr:.2f}"
            if it.k_atr is not None
            else f"{it.symbol}: side={it.side or '-'}"
        )
        line2 = (
            f"Perf: ΔEq {_fmt_pct(it.delta_eq_pct)} "
            f"| Sharpe {it.sharpe:.2f if it.sharpe is not None else 'n/a'} "
            f"| Sortino {it.sortino:.2f if it.sortino is not None else 'n/a'} "
            f"| MaxDD {_fmt_pct((it.max_dd or 0.0), plus=False)}"
        )
        line3 = (
            f"Régime: vol {it.regime_vol:.2f if it.regime_vol is not None else 0.0} "
            f"| mom {it.regime_mom:.2f if it.regime_mom is not None else 0.0} "
            f"| score {it.regime_score:.2f if it.regime_score is not None else 0.0}"
        )
        lines.extend([line1, line2, line3, ""])
    return "\n".join(lines)


def render_markdown(mode: str, items: list[SymbolSummary]) -> str:
    """

    Args:
      mode: str:
      items: list[SymbolSummary]:
      mode: str:
      items: list[SymbolSummary]:

    Returns:

    """
    # Telegram (MarkdownV2 safe-enough: pas d`emoji ni caractères spéciaux ici)
    ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%MZ")
    out = [f"*DIA-Core* — *{mode}* — `{ts}`", ""]
    for it in items:
        s_delta = _fmt_pct(it.delta_eq_pct)
        s_sh = f"{it.sharpe:.2f}" if it.sharpe is not None else "n/a"
        s_so = f"{it.sortino:.2f}" if it.sortino is not None else "n/a"
        s_dd = _fmt_pct((it.max_dd or 0.0), plus=False)
        s_line1 = (
            f"*{it.symbol}*: side=`{it.side or '-'}` | k_atr=`{it.k_atr:.2f}`"
            if it.k_atr is not None
            else f"*{it.symbol}*: side=`{it.side or '-'}`"
        )
        s_line2 = f"Perf: ΔEq {s_delta} | Sharpe {s_sh} | Sortino {s_so} | MaxDD {s_dd}"
        s_line3 = (
            f"Régime: vol `{(it.regime_vol or 0):.2f}` "
            f"| mom `{(it.regime_mom or 0):.2f}` | score `{(it.regime_score or 0):.2f}`"
        )
        out.extend([s_line1, s_line2, s_line3, ""])
    return "\n".join(out)
