import pandas as pd

def attribution_from_exec(exec_df: pd.DataFrame):
    if exec_df.empty:
        return pd.DataFrame(columns=["symbol","venue","maker_rebate","taker_fees","spread_capture","net_exec_pnl"])
    g = exec_df.groupby(["symbol","venue"])
    out = g.agg(
        maker_rebate=("fee", lambda s: s[s>0].sum()),
        taker_fees=("fee", lambda s: -s[s<0].sum()),
        spread_capture=("spread_capture","sum"),
        qty=("qty","sum")
    ).reset_index()
    out["net_exec_pnl"] = out["maker_rebate"] - out["taker_fees"] + out["spread_capture"]
    return out
