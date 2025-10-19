import numpy as np
import pandas as pd

def mc_from_df(df: pd.DataFrame, n_runs: int = 100, seed: int = 42):
    rng = np.random.default_rng(seed)
    pf = df.groupby("timestamp")[["pnl","inventory"]].sum().reset_index()
    if len(pf) < 2:
        return {"mean_pnl":0.0,"p5":0.0,"p50":0.0,"p95":0.0}
    rets = pf["pnl"].diff().fillna(0.0).values
    results = []
    for _ in range(n_runs):
        idx = rng.integers(0, len(rets), size=len(rets))
        r = rets[idx] + rng.normal(0, max(1e-9, np.std(rets))*0.1, size=len(rets))
        pnl_path = r.cumsum()
        results.append(pnl_path[-1])
    arr = np.array(results)
    return {
        "mean_pnl": float(arr.mean()),
        "p5": float(np.quantile(arr, 0.05)),
        "p50": float(np.quantile(arr, 0.50)),
        "p95": float(np.quantile(arr, 0.95)),
    }
