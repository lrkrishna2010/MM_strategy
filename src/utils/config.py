from dataclasses import dataclass, field
from typing import List
import os, yaml

@dataclass
class VenueConf:
    name: str
    maker_fee_bps: float = -0.05
    taker_fee_bps: float = 0.20
    latency_ms: int = 2

@dataclass
class Config:
    symbols: List[str] = field(default_factory=lambda: ["XYZ","ABC"])
    start_price: float = 100.0
    tick_size: float = 0.01
    quote_size: int = 40
    inventory_limit: int = 400
    max_move: float = 1.0
    alpha_weight: float = 0.7
    obi_weight: float = 0.3
    alpha_smooth: float = 0.2
    base_spread_bps: float = 5.0
    n_steps: int = 500
    report_path: str = "reports"
    events_path: str = "data/market_events"
    # Risk
    portfolio_var_limit: float = 1500.0
    hedge_portfolio_on_breach: bool = True
    hedge_fraction_portfolio: float = 0.25
    skew_k: float = 0.8
    tx_fee_bps: float = 0.8
    # Avellaneda–Stoikov
    use_avellaneda: bool = True
    as_gamma: float = 0.001
    as_k: float = 1.5
    as_T: float = 1.0
    # Hawkes
    use_hawkes: bool = True
    hawkes_mu: float = 0.8
    hawkes_alpha: float = 0.6
    hawkes_beta: float = 0.3
    # ES
    es_conf: float = 0.95
    es_window: int = 100
    # Venues
    venues: List[VenueConf] = field(default_factory=lambda: [
        VenueConf(name="VENUE_A", maker_fee_bps=-0.05, taker_fee_bps=0.20, latency_ms=2),
        VenueConf(name="VENUE_B", maker_fee_bps=-0.02, taker_fee_bps=0.25, latency_ms=5),
        VenueConf(name="VENUE_C", maker_fee_bps=-0.08, taker_fee_bps=0.18, latency_ms=8),
    ])
    router_top_k: int = 2
    impact_kappa: float = 0.03
    # Adaptive tick for quoting
    adaptive_tick: bool = True
    min_tick: float = 0.005
    max_tick: float = 0.05
    vol_low: float = 0.0005
    vol_high: float = 0.01

def _parse_venues(lst):
    out = []
    for d in lst:
        out.append(VenueConf(
            name=d.get("name","VENUE"),
            maker_fee_bps=float(d.get("maker_fee_bps", -0.05)),
            taker_fee_bps=float(d.get("taker_fee_bps", 0.20)),
            latency_ms=int(d.get("latency_ms", 2)),
        ))
    return out

def load_config(path: str = "config.yaml") -> "Config":
    cfg = Config()
    if os.path.exists(path):
        with open(path, "r") as f:
            y = yaml.safe_load(f) or {}
        for k, v in y.items():
            if k == "venues" and isinstance(v, list):
                cfg.venues = _parse_venues(v)
            elif hasattr(cfg, k):
                setattr(cfg, k, v)
    return cfg
