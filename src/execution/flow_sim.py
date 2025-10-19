import random
from src.execution.depth_lob import DepthLOB

def simulate_external_flow(lob: DepthLOB, alpha: float, intensity: float = 1.0, impact_kappa: float = 0.02, tick: float = 0.01):
    fills_total = []
    n_events = max(1, int(2 * intensity))
    for _ in range(n_events):
        if random.random() < 0.7:
            p_buy = 0.5 + 0.4 * max(alpha, 0.0)
            side = "BUY" if random.random() < p_buy else "SELL"
            qty = random.choice([20, 50, 100])
            fills = lob.place_market(owner="EXT", side=side, qty=qty)
            fills_total.extend(fills)
            direction = 1 if side == "BUY" else -1
            delta = direction * impact_kappa * (qty / 100.0) * tick
            lob.shift_prices(delta)
        else:
            best_bid = lob.best_bid(); best_ask = lob.best_ask()
            if not best_bid or not best_ask: continue
            side = random.choice(["BUY","SELL"])
            if side == "BUY":
                price = round(best_bid.price - random.randint(1,2)*lob.tick, 2)
            else:
                price = round(best_ask.price + random.randint(1,2)*lob.tick, 2)
            qty = random.choice([50, 100])
            lob.place_limit(owner="EXT", side=side, price=price, qty=qty, ts=-1)
    return fills_total
