from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, Deque, Optional
from src.execution.order import Order

@dataclass
class BookLevel:
    price: float
    qty: int

class DepthLOB:
    def __init__(self, mid: float, tick: float, levels: int = 5):
        self.tick = tick
        self.levels = levels
        self.bids: Dict[float, Deque[Order]] = defaultdict(deque)
        self.asks: Dict[float, Deque[Order]] = defaultdict(deque)
        self._order_index = {}
        self._next_id = 1
        for i in range(levels):
            p_bid = round(mid - (i+1)*tick, 2)
            p_ask = round(mid + (i+1)*tick, 2)
            self.place_limit(owner="EXT", side="BUY", price=p_bid, qty=200, ts=-1)
            self.place_limit(owner="EXT", side="SELL", price=p_ask, qty=200, ts=-1)

    def next_id(self) -> int:
        oid = self._next_id; self._next_id += 1; return oid

    def best_bid(self) -> Optional[BookLevel]:
        if not self.bids: return None
        p = max(self.bids.keys())
        q = sum(o.qty for o in self.bids[p])
        return BookLevel(price=p, qty=q)

    def best_ask(self) -> Optional[BookLevel]:
        if not self.asks: return None
        p = min(self.asks.keys())
        q = sum(o.qty for o in self.asks[p])
        return BookLevel(price=p, qty=q)

    def mid(self) -> float:
        bb = self.best_bid(); ba = self.best_ask()
        if not bb or not ba: return 0.0
        return round((bb.price + ba.price)/2, 2)

    def place_limit(self, owner: str, side: str, price: float, qty: int, ts: int) -> int:
        oid = self.next_id()
        order = Order(order_id=oid, owner=owner, side=side, price=price, qty=qty, ts=ts)
        book = self.bids if side == "BUY" else self.asks
        book[price].append(order)
        self._order_index[oid] = (side, price)
        return oid

    def cancel(self, order_id: int) -> bool:
        info = self._order_index.get(order_id)
        if not info: return False
        side, price = info
        book = self.bids if side == "BUY" else self.asks
        q = book.get(price)
        if not q: return False
        kept = deque(); removed = False
        while q:
            o = q.popleft()
            if o.order_id == order_id and not removed:
                removed = True; continue
            kept.append(o)
        if kept: book[price] = kept
        else: book.pop(price, None)
        self._order_index.pop(order_id, None)
        return removed

    def _match_queue(self, taker_side: str, qty: int, best_price: float):
        fills = []
        book = self.asks if taker_side == "BUY" else self.bids
        q = book.get(best_price, deque())
        filled_here = 0
        while qty > 0 and q:
            maker = q[0]
            take = min(qty, maker.qty)
            maker.qty -= take; qty -= take; filled_here += take
            fills.append(Order(order_id=maker.order_id, owner=maker.owner, side=maker.side, price=best_price, qty=take, ts=maker.ts))
            if maker.qty == 0:
                q.popleft(); self._order_index.pop(maker.order_id, None)
        if not q: book.pop(best_price, None)
        else: book[best_price] = q
        return fills, filled_here

    def place_market(self, owner: str, side: str, qty: int):
        fills = []; remaining = qty
        if side == "BUY":
            while remaining > 0 and self.asks:
                best_p = min(self.asks.keys())
                f, took = self._match_queue("BUY", remaining, best_p)
                fills += f; remaining -= took
        else:
            while remaining > 0 and self.bids:
                best_p = max(self.bids.keys())
                f, took = self._match_queue("SELL", remaining, best_p)
                fills += f; remaining -= took
        return fills

    def shift_prices(self, delta: float):
        if delta == 0.0: return
        new_bids = defaultdict(deque)
        for p, q in self.bids.items():
            new_bids[round(p + delta, 2)] = q
        new_asks = defaultdict(deque)
        for p, q in self.asks.items():
            new_asks[round(p + delta, 2)] = q
        self.bids, self.asks = new_bids, new_asks
