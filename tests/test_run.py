import os
import json
from pathlib import Path

import pandas as pd
import pytest

from dia_core.risk.risk_manager import RiskManager
from dia_core.tracking.trade_logger import TradeLogger, TradeLogEntry
from dia_core.config.risk_config_loader import get_risk_limits_for, RiskLimits

DEFAULT_RISK = 0.01
HIGH_RISK = 0.015

# ==== TESTS RISK CONFIG LOADER ==== #


@pytest.fixture
def sample_config() -> dict[str, RiskLimits]:
    return {
        "BTC/EUR": {
            "max_drawdown_pct": 12.0,
            "max_exposure_pct": 25.0,
            "risk_per_trade": HIGH_RISK,
            "stop_loss_pct": 5.0,
        }
    }


def test_risk_config_known_symbol(sample_config: dict[str, RiskLimits]) -> None:
    limits = get_risk_limits_for("BTC/EUR", sample_config)
    assert limits["risk_per_trade"] == HIGH_RISK


def test_risk_config_unknown_symbol(sample_config: dict[str, RiskLimits]) -> None:
    limits = get_risk_limits_for("DOGE/EUR", sample_config)
    assert limits["risk_per_trade"] == DEFAULT_RISK  # fallback


# ==== TESTS RISK MANAGER ==== #


def test_risk_manager_returns_positive_size() -> None:
    # Fournit 20 lignes pour que le rolling(14) fonctionne
    ohlc = pd.DataFrame(
        {
            "high": [10 + i for i in range(20)],
            "low": [9 + i for i in range(20)],
        }
    )
    rm = RiskManager(capital=10_000, risk_per_trade=DEFAULT_RISK)
    size = rm.compute_size(ohlc)
    assert size > 0


def test_risk_manager_handles_zero_range() -> None:
    ohlc = pd.DataFrame({"high": [10, 10, 10], "low": [10, 10, 10]})
    rm = RiskManager(capital=10000, risk_per_trade=0.01)
    size = rm.compute_size(ohlc)
    assert size == 0.0


# ==== TESTS TRADE LOGGER ==== #


def test_trade_logger_creates_log(tmp_path: Path) -> None:
    log_path = tmp_path / "test_log.jsonl"
    logger = TradeLogger(str(log_path))
    entry = TradeLogEntry("BTC/EUR", "buy", 0.01, 27000, "executed", meta={"note": "test"})
    logger.log_trade(entry)

    assert os.path.exists(log_path)
    with open(log_path) as f:
        line = json.loads(f.readline())
    assert line["symbol"] == "BTC/EUR"
    assert line["meta"]["note"] == "test"
