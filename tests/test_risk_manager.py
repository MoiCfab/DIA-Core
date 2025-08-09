from __future__ import annotations

import pytest
from dia_core.config.models import AppConfig, ExchangeMeta, RiskLimits
from dia_core.exec.pre_trade import MarketSnapshot, propose_order
from dia_core.risk.dynamic_fake import build_risk_context
from dia_core.risk.errors import RiskLimitExceededError
from dia_core.risk.sizing import SizingParams, compute_position_size
from dia_core.risk.validator import RiskCheckParams, validate_order


def _cfg() -> AppConfig:
    return AppConfig(
        mode="dry_run",
        exchange=ExchangeMeta(
            symbol="BTC/EUR",
            price_decimals=2,
            qty_decimals=6,
            min_qty=0.0001,
            min_notional=10.0,
        ),
        risk=RiskLimits(
            max_daily_loss_pct=2.0,
            max_drawdown_pct=15.0,
            max_exposure_pct=50.0,
            risk_per_trade_pct=0.5,
            max_orders_per_min=30,
        ),
        data_window_bars=1000,
        cache_dir="state/cache",
        journal_path="state/journal.sqlite",
        log_dir="logs",
        pair="XXBTZEUR",
        require_interactive_confirm=True,
    )


def test_sizing_min_qty_notional_respected() -> None:
    min_qty = 0.003
    min_notional = 10.0
    equity = 1000.0  # capital total
    price = 200.0  # prix actuel
    atr = 5.0  # volatilité ATR
    k_atr = 2.0  # multiplicateur
    cfg = AppConfig(
        risk=RiskLimits(
            risk_per_trade_pct=1.0,
            max_exposure_pct=50.0,
            max_orders_per_min=10,
            max_daily_loss_pct=5.0,
            max_drawdown_pct=10.0,
        ),
        exchange=ExchangeMeta(
            symbol="BTC/EUR",
            price_decimals=2,
            qty_decimals=3,
            min_qty=0.001,
            min_notional=10.0,
        ),
    )
    params = SizingParams(
        equity=equity,
        price=price,
        atr=atr,
        risk_per_trade_pct=cfg.risk.risk_per_trade_pct,
        k_atr=k_atr,
        min_qty=cfg.exchange.min_qty,
        min_notional=cfg.exchange.min_notional,
        qty_decimals=cfg.exchange.qty_decimals,
    )

    qty = compute_position_size(params)
    assert qty >= min_qty
    assert qty * price >= min_notional


def test_validator_blocks_on_exposure() -> None:
    limits = _cfg().risk
    with pytest.raises(RiskLimitExceededError):
        validate_order(
            limits,
            RiskCheckParams(
                current_exposure_pct=49.0,
                projected_exposure_pct=55.0,  # dépasse
                daily_loss_pct=0.0,
                drawdown_pct=0.0,
                orders_last_min=0,
            ),
        )


def test_pre_trade_blocks_when_limits_violated() -> None:
    cfg = _cfg()
    # Valeurs choisies pour dépasser max_exposure_pct (=50%)
    equity = 1000.0
    price = 100.0
    atr = 1.0
    # Projection: current 50% + nouveau > 0 -> blocage
    try:
        market = MarketSnapshot(price=price, atr=atr, k_atr=2.0)
        risk = build_risk_context(
            equity=equity, open_notional=0.5 * equity, fallback_orders_last_min=0
        )
        propose_order(cfg=cfg, market=market, risk=risk)
        pytest.fail("Doit lever RiskLimitExceeded")
    except RiskLimitExceededError:
        pass


def test_pre_trade_ok_when_within_limits() -> None:
    cfg = _cfg()
    equity = 10000.0
    price = 100.0
    atr = 5.0  # stop plus large donc qty plus faible
    market = MarketSnapshot(price=price, atr=atr, k_atr=2.0)
    risk = build_risk_context(equity=equity, open_notional=0.0, fallback_orders_last_min=0)
    out = propose_order(cfg=cfg, market=market, risk=risk)

    assert out["qty"] > 0.0
    assert out["notional"] == out["qty"] * price
