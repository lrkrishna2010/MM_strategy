import math

def _safe(val, fallback):
    try:
        if val is None or math.isnan(val) or math.isinf(val):
            return fallback
    except Exception:
        return fallback
    return val

def _snap_bid(x, tick, mid):
    tick = _safe(tick, 0.01)
    if tick <= 0.0: tick = 0.01
    x = _safe(x, mid - tick)
    try:
        return math.floor(x / tick) * tick
    except Exception:
        return round(mid - tick, 2)

def _snap_ask(x, tick, mid):
    tick = _safe(tick, 0.01)
    if tick <= 0.0: tick = 0.01
    x = _safe(x, mid + tick)
    try:
        return math.ceil(x / tick) * tick
    except Exception:
        return round(mid + tick, 2)

def optimal_quotes(mid: float, q: int, sigma: float, gamma: float, k: float, T: float, tick: float):
    mid   = _safe(mid, 0.0)
    q     = int(q or 0)
    sigma = abs(_safe(sigma, 1e-6)) or 1e-6
    gamma = abs(_safe(gamma, 1e-3)) or 1e-3
    k     = abs(_safe(k, 1.5)) or 1e-3
    T     = max(_safe(T, 1.0), 1e-6)
    tick  = abs(_safe(tick, 0.01)) or 0.01

    try:
        r = mid - q * gamma * (sigma ** 2) * T
    except Exception:
        r = mid

    try:
        half = (1.0 / gamma) * math.log(1.0 + (gamma / k))
    except Exception:
        half = 0.01 * max(1.0, mid)

    half = max(half, tick)
    bid_raw, ask_raw = r - half, r + half
    bid = _snap_bid(bid_raw, tick, mid)
    ask = _snap_ask(ask_raw, tick, mid)
    return round(bid,2), round(ask,2), r, half
