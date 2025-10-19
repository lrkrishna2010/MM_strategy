from dataclasses import dataclass
from typing import Dict, Callable, Optional
from src.execution.depth_lob import DepthLOB
from src.execution.market_maker_depth import MarketMakerDepth
from src.execution.risk_manager import RiskManager
from src.execution.smart_router import SmartVenueSelector

@dataclass
class Venue:
    name: str
    lob: DepthLOB
    mm: MarketMakerDepth
    maker_fee_bps: float
    taker_fee_bps: float
    latency_ms: int

class MarketMakerRouter:
    def __init__(self, symbol: str, venues_conf, start_price: float, tick: float,
                 quote_size: int, inv_limit: int, mm_kwargs: dict,
                 exec_logger: Optional[Callable[[dict], None]] = None,
                 top_k: int = None):
        self.symbol = symbol
        self.venues: Dict[str, Venue] = {}
        self.selector = SmartVenueSelector(lookback=200)
        shared_risk = RiskManager(inv_limit)
        for v in venues_conf:
            lob = DepthLOB(start_price, tick, levels=5)
            mm = MarketMakerDepth(lob, shared_risk, quote_size, inv_limit, **mm_kwargs,
                                  maker_fee_bps=v.maker_fee_bps, exec_logger=exec_logger, venue_name=v.name)
            self.venues[v.name] = Venue(v.name, lob, mm, v.maker_fee_bps, v.taker_fee_bps, v.latency_ms)
        self.top_k = top_k

    def inventory(self) -> int:
        return next(iter(self.venues.values())).mm.inv

    def pnl(self) -> float:
        return sum(v.mm.pnl for v in self.venues.values()) / max(1,len(self.venues))

    def mid(self) -> float:
        mids = [v.lob.mid() for v in self.venues.values() if v.lob.mid() > 0]
        return sum(mids)/len(mids) if mids else 0.0

    def make_quotes(self, alpha: float, ts: int):
        chosen = self.selector.pick_venues(self.venues, k=self.top_k)
        for name in chosen:
            self.venues[name].mm.make_quote(alpha, ts)

    def mark_to_market(self):
        for v in self.venues.values():
            v.mm.mark_to_market()

    def hedge_portfolio(self, qty_perc: float):
        inv = self.inventory()
        if inv == 0: return
        hedge_qty = int(qty_perc * abs(inv))
        if hedge_qty <= 0: return
        best = sorted(self.venues.values(), key=lambda x: x.taker_fee_bps)[0]
        side = "SELL" if inv > 0 else "BUY"
        fills = best.lob.place_market(owner="MM", side=side, qty=hedge_qty)
        best.mm.apply_taker_fills(fills, best.taker_fee_bps)

    def update_selector_from_exec(self, exec_event: dict):
        if exec_event.get("role") == "maker":
            self.selector.update_from_fill(
                venue=exec_event.get("venue","?"),
                spread_capture=float(exec_event.get("spread_capture",0.0)),
                notional=abs(exec_event.get("qty",0))*float(exec_event.get("price",0.0)),
                maker_rebate=float(exec_event.get("fee",0.0)),
                adverse=0.0
            )
