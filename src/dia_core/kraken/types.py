from __future__ import annotations
from pydantic import BaseModel
from typing import Literal, Optional

Side = Literal["buy", "sell"]
OrderType = Literal["market", "limit"]

class OrderIntent(BaseModel):
    symbol: str
    side: Side
    type: OrderType = "limit"
    qty: float
    limit_price: Optional[float] = None
    time_in_force: Literal["GTC", "IOC"] = "GTC"

class SubmittedOrder(BaseModel):
    client_order_id: str
    exchange_order_id: Optional[str] = None
    status: Literal["accepted", "rejected", "filled", "partially_filled", "pending"] = "pending"
    reason: Optional[str] = None
