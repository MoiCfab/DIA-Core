from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Side = Literal["buy", "sell"]
OrderType = Literal["market", "limit"]


class OrderIntent(BaseModel):
    symbol: str
    side: Side
    type: OrderType = "limit"
    qty: float
    limit_price: float | None = None
    time_in_force: Literal["GTC", "IOC"] = "GTC"


class SubmittedOrder(BaseModel):
    client_order_id: str
    exchange_order_id: str | None = None
    status: Literal["accepted", "rejected", "filled", "partially_filled", "pending"] = "pending"
    reason: str | None = None
