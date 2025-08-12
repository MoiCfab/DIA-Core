from __future__ import annotations

from dia_core.exec.pre_trade import (  # <- utilise la même dataclass que propose_order
    RiskContext,
)
from dia_core.market_state.fake import (
    current_exposure_pct as _expo,
    orders_last_min as _olm,
)


def build_risk_context(
    *,
    equity: float,
    open_notional: float | None = None,
    fallback_orders_last_min: int | None = None,
) -> RiskContext:
    expo = _expo(equity, open_notional or 0.0)
    olm = fallback_orders_last_min if fallback_orders_last_min is not None else _olm()
    return RiskContext(equity=equity, current_exposure_pct=expo, orders_last_min=olm)
