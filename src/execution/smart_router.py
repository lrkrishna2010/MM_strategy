from collections import deque
from dataclasses import dataclass
from typing import Dict

@dataclass
class VenueStats:
    fills: int = 0
    notional: float = 0.0
    spread_capture: float = 0.0
    maker_rebate: float = 0.0
    adverse_moves: float = 0.0

class SmartVenueSelector:
    def __init__(self, lookback=200):
        self.lookback = lookback
        self.history: Dict[str, deque] = {}
        self.stats: Dict[str, VenueStats] = {}

    def update_from_fill(self, venue: str, spread_capture: float, notional: float, maker_rebate: float, adverse: float):
        if venue not in self.stats:
            self.stats[venue] = VenueStats()
            self.history[venue] = deque(maxlen=self.lookback)
        st = self.stats[venue]
        st.fills += 1; st.notional += notional
        st.spread_capture += spread_capture; st.maker_rebate += maker_rebate; st.adverse_moves += adverse
        ev = spread_capture + maker_rebate - adverse
        self.history[venue].append(ev)

    def expected_value(self, venue: str) -> float:
        if venue not in self.history or len(self.history[venue]) == 0:
            return 0.0
        h = self.history[venue]
        return sum(h) / len(h)

    def pick_venues(self, venues: Dict[str, object], k: int = None):
        scores = [(v.name, self.expected_value(v.name)) for v in venues.values()]
        scores.sort(key=lambda x: x[1], reverse=True)
        if not scores:
            return list(venues.keys())
        if k is None or k >= len(scores):
            return [s for s,_ in scores]
        return [s for s,_ in scores[:k]]
