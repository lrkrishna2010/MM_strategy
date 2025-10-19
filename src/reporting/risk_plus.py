import numpy as np
import pandas as pd

def expected_shortfall(returns: np.ndarray, conf: float = 0.95):
    if returns.size == 0: return 0.0
    q = np.quantile(returns, 1-conf)
    tail = returns[returns <= q]
    if tail.size == 0: return 0.0
    return float(tail.mean())

def rolling_es(pnl_series: pd.Series, window: int = 100, conf: float = 0.95):
    if len(pnl_series) < window + 1:
        return pd.Series([0.0]*len(pnl_series))
    rets = pnl_series.diff().fillna(0.0).values
    es_vals = []
    for i in range(len(rets)):
        if i < window: es_vals.append(0.0)
        else: es_vals.append(expected_shortfall(np.array(rets[i-window:i]), conf=conf))
    return pd.Series(es_vals)
