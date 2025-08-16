# Copyright (c) 2025 Fabien Grolier - DYXIUM Invest / D.I.A. Core
# All Rights Reserved - Usage without permission is prohibited

"""
Nom du script : runner_backtest.py

Description :
Exécute un backtest complet sur une paire avec un modèle IA donné,
ou une stratégie heuristique par défaut.

Utilisé pour : validation des stratégies

Auteur : DYXIUM Invest / D.I.A. Core
"""

import argparse
from dia_core.backtest.backtest_engine import BacktestEngine
from dia_core.strategy.decision_policy import (
    ModelBasedPolicy,
    HeuristicPolicy,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest DIA-Core V4")
    parser.add_argument("--symbol", default="BTC/EUR", help="Paire ex: BTC/EUR")
    parser.add_argument(
        "--data", required=True, help="Fichier CSV OHLC (colonnes: time, open, high, low, close)"
    )
    parser.add_argument("--model", help="Chemin vers modèle IA (.pkl)")
    parser.add_argument("--equity", type=float, default=10_000.0, help="Capital initial")
    parser.add_argument("--log", default=None, help="Fichier de sortie (.jsonl)")

    args = parser.parse_args()

    # Politique
    policy = ModelBasedPolicy(args.model) if args.model else HeuristicPolicy()

    engine = BacktestEngine(
        policy=policy,
        data_path=args.data,
        symbol=args.symbol,
        initial_equity=args.equity,
        output_log=args.log,
    )

    engine.run()
    print(f"✅ Backtest terminé pour {args.symbol}.")


if __name__ == "__main__":
    main()
