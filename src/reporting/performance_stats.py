import pandas as pd
import numpy as np

def basic_stats(df: pd.DataFrame):
    if df.empty:
        return pd.Series({"pnl_end":0.0,"inv_end":0.0,"pnl_mean":0.0,"pnl_std":0.0,"sharpe_like":0.0})
    pnl = np.array(df["pnl"], dtype=float).flatten()
    inv = np.array(df["inventory"], dtype=float).flatten()
    pnl = np.nan_to_num(pnl, nan=0.0, posinf=0.0, neginf=0.0)
    inv = np.nan_to_num(inv, nan=0.0, posinf=0.0, neginf=0.0)
    pnl = np.clip(pnl, -1e6, 1e6)
    inv = np.clip(inv, -1e3, 1e3)
    pnl_end = float(pnl[-1]) if len(pnl) else 0.0
    inv_end = float(inv[-1]) if len(inv) else 0.0
    s = np.std(pnl) or 1e-9
    m = np.mean(pnl)
    return pd.Series({
        "pnl_end": pnl_end,
        "inv_end": inv_end,
        "pnl_mean": m,
        "pnl_std": s,
        "sharpe_like": m/s if s else 0.0
    })
