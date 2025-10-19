import numpy as np

def realized_vol(p, window=50):
    p = np.nan_to_num(np.array(p, dtype=float), nan=1.0, posinf=1.0, neginf=1.0)
    p = np.clip(p, 0.01, 1e6)            # avoid 0-divide
    denom = np.where(p[:-1] == 0, 1e-9, p[:-1])
    rets = np.diff(p) / denom
    rets = np.clip(rets, -0.1, 0.1)      # cap 10 % step changes
    sigma = np.std(rets[-window:]) * np.sqrt(252)
    return max(float(sigma), 1e-6)

def half_spread(sigma, gamma=0.1, k=1.5, T=1.0):
    sigma = np.nan_to_num(sigma, nan=0.0, posinf=1e3, neginf=-1e3)
    return float(min(max(0.5 * sigma * (1 + gamma) / max(k, 1e-6), 0.0001), 5.0))
def adjust_spread(prices, base_spread, gamma=0.1, k=1.5, T=1.0, window=50):
    sigma = realized_vol(prices, window=window)
    half_spd = half_spread(sigma, gamma=gamma, k=k, T=T)
    return float(max(base_spread, 2 * half_spd))