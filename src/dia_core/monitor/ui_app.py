# Copyright (c) 2025 Fabien Grolier — DYXIUM Invest / DIA-Core
# All Rights Reserved — Usage without permission is prohibited

"""
Nom du module : monitor/ui_app.py

Description :
    Mini dashboard *optionnel* (Streamlit) pour visualiser :
      - score de régime et composantes
      - agressivité/k_atr
      - dernière décision de la stratégie

    Importation sûre (aucune dépendance streamlit au moment de l'import),
    `run()` effectue l'import localement et échoue proprement si streamlit
    n'est pas installé.

Auteur : DYXIUM Invest / D.I.A. Core
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class UiState:
    """État minimal affiché par l`UI (positions, PnL, régime)."""

    symbol: str
    regime: Mapping[str, float]
    k_atr: float
    last_side: str | None


def build_state(
    *, symbol: str, regime: Mapping[str, float], k_atr: float, last_side: str | None
) -> UiState:
    """

    Args:
      *:
      symbol: str:
      regime: Mapping[str:
      float]:
      k_atr: float:
      last_side: str | None:

    Returns:

    """
    return UiState(symbol=symbol, regime=dict(regime), k_atr=float(k_atr), last_side=last_side)


def run(state: UiState) -> None:  # pragma: no cover - interface
    """

    Args:
      state: UiState:

    Returns:

    """
    try:
        import streamlit as st  # type: ignore
    except Exception as e:  # streamlit absent
        raise RuntimeError("Streamlit not installed") from e

    st.set_page_config(page_title="DIA-Core Monitor", layout="wide")
    st.title("DIA-Core — Monitor Live")
    st.subheader(state.symbol)

    cols = st.columns(3)
    cols[0].metric("k_atr", f"{state.k_atr:.2f}")
    cols[1].metric("last side", state.last_side or "—")
    cols[2].metric("regime score", f"{state.regime.get('score', 0.0):.2f}")

    with st.expander("Régime (composantes)"):
        st.json(asdict(state)["regime"])
