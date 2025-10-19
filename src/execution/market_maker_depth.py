from dataclasses import dataclass
from typing import Optional, Callable
from src.pricing.spread_adjuster import half_spread, realized_vol
from src.pricing.avellaneda_stoikov import optimal_quotes
from src.execution.depth_lob import DepthLOB
from src.execution.risk_manager import RiskManager

@dataclass
class QuoteIds:
    bid_id: Optional[int]
    ask_id: Optional[int]

class MarketMakerDepth:
    def __init__(self, lob: DepthLOB, risk: RiskManager, size: int, inv_limit: int,
                 alpha_weight=0.7, alpha_smooth=0.2, max_move=1.0, base_spread_bps=10.0, tick_size=0.01,
                 tx_fee_bps: float = 0.5, skew_k: float = 0.6,
                 use_avellaneda: bool = True, as_gamma: float = 0.001, as_k: float = 1.5, as_T: float = 1.0,
                 maker_fee_bps: float = -0.05,
                 exec_logger: Optional[Callable[[dict], None]] = None,
                 venue_name: str = "?",
                 adaptive_tick: bool = True, min_tick: float = 0.005, max_tick: float = 0.05,
                 vol_low: float = 0.0005, vol_high: float = 0.01):
        self.lob = lob
        self.risk = risk
        self.size = size
        self.inv_limit = inv_limit
        self.alpha_weight = alpha_weight
        self.alpha_smooth = alpha_smooth
        self.max_move = max_move
        self.base_spread_bps = base_spread_bps
        self.tick = tick_size
        self.tx_fee_bps = tx_fee_bps
        self.skew_k = skew_k
        self.use_avellaneda = use_avellaneda
        self.as_gamma = as_gamma; self.as_k = as_k; self.as_T = as_T
        self.maker_fee_bps = maker_fee_bps
        self.exec_logger = exec_logger
        self.venue_name = venue_name
        self.adaptive_tick = adaptive_tick
        self.min_tick = min_tick; self.max_tick = max_tick
        self.vol_low = vol_low; self.vol_high = vol_high

        self.inv = 0
        self.realized = 0.0
        self.pnl = 0.0
        self.last_mid = self.lob.mid()
        self.mid_history = [self.last_mid]
        self.qids = QuoteIds(None, None)

    def _fee(self, qty: int, price: float, bps: float) -> float:
        return abs(qty) * price * (bps * 1e-4)

    def cancel_quotes(self):
        if self.qids.bid_id: self.lob.cancel(self.qids.bid_id)
        if self.qids.ask_id: self.lob.cancel(self.qids.ask_id)
        self.qids = QuoteIds(None, None)

    def _effective_tick(self, vol: float) -> float:
        if not self.adaptive_tick:
            return self.tick
        v = max(self.vol_low, min(vol, self.vol_high))
        x = (v - self.vol_low) / max(1e-9, (self.vol_high - self.vol_low))
        return round(self.min_tick + x * (self.max_tick - self.min_tick), 4)

    def make_quote(self, alpha: float, ts: int):
        mid = self.lob.mid()
        vol = realized_vol(self.mid_history, window=50)
        eff_tick = self._effective_tick(vol)

        if self.use_avellaneda:
            sigma = max(1e-6, vol * 0.05)
            bid, ask, r, half = optimal_quotes(mid + alpha*0.05, self.inv, sigma, self.as_gamma, self.as_k, self.as_T, eff_tick)
        else:
            h = half_spread(mid, self.inv, self.inv_limit, self.base_spread_bps, vol=vol)
            bid = round(mid - h, 2); ask = round(mid + h, 2)

        self.cancel_quotes()
        size_bid = self.risk.capped_size(self.inv, self.size)
        size_ask = self.risk.capped_size(-self.inv, self.size)
        if size_bid > 0: self.qids.bid_id = self.lob.place_limit("MM", "BUY", bid, size_bid, ts)
        if size_ask > 0: self.qids.ask_id = self.lob.place_limit("MM", "SELL", ask, size_ask, ts)

    def on_fills(self, fills):
        for f in fills:
            if f.owner == "MM":
                mid = self.lob.mid()
                if f.side == "SELL":
                    self.inv -= f.qty
                    cash = f.qty * f.price
                    rebate = self._fee(f.qty, f.price, self.maker_fee_bps)
                    self.realized += cash + rebate
                    if self.exec_logger:
                        self.exec_logger({
                            "venue": self.venue_name, "role": "maker", "side": "SELL", "qty": f.qty,
                            "price": f.price, "mid": mid, "fee_bps": self.maker_fee_bps, "fee": rebate,
                            "spread_capture": (f.price - mid) * f.qty, "symbol": None
                        })
                else:
                    self.inv += f.qty
                    cost = f.qty * f.price
                    rebate = self._fee(f.qty, f.price, self.maker_fee_bps)
                    self.realized -= cost - rebate
                    if self.exec_logger:
                        self.exec_logger({
                            "venue": self.venue_name, "role": "maker", "side": "BUY", "qty": f.qty,
                            "price": f.price, "mid": mid, "fee_bps": self.maker_fee_bps, "fee": rebate,
                            "spread_capture": (mid - f.price) * f.qty, "symbol": None
                        })

    def apply_taker_fills(self, fills, taker_fee_bps: float):
        for f in fills:
            mid = self.lob.mid()
            if f.side == "SELL":
                self.inv += f.qty
                cost = f.qty * f.price
                fee = self._fee(f.qty, f.price, taker_fee_bps)
                self.realized -= cost + fee
                if self.exec_logger:
                    self.exec_logger({
                        "venue": self.venue_name, "role": "taker", "side": "BUY", "qty": f.qty,
                        "price": f.price, "mid": mid, "fee_bps": taker_fee_bps, "fee": -fee,
                        "spread_capture": 0.0, "symbol": None
                    })
            else:
                self.inv -= f.qty
                cash = f.qty * f.price
                fee = self._fee(f.qty, f.price, taker_fee_bps)
                self.realized += cash - fee
                if self.exec_logger:
                    self.exec_logger({
                        "venue": self.venue_name, "role": "taker", "side": "SELL", "qty": f.qty,
                        "price": f.price, "mid": mid, "fee_bps": taker_fee_bps, "fee": -fee,
                        "spread_capture": 0.0, "symbol": None
                    })

    def mark_to_market(self):
        mid = self.lob.mid()
        self.pnl = self.realized + self.inv * mid
        self.last_mid = mid
        self.mid_history.append(mid)
