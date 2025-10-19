from dataclasses import dataclass

@dataclass
class Order:
    order_id: int
    owner: str
    side: str
    price: float
    qty: int
    ts: int
