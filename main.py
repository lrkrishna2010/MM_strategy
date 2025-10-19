import os, json
import numpy as np
import pandas as pd
from src.utils.config import load_config
from src.utils.logger import get_logger
from src.alpha.news_ingestor import synthetic_news_tape
from src.alpha.sentiment_signal import SentimentSignal
from src.execution.venue_router import MarketMakerRouter
from src.execution.flow_sim import simulate_external_flow
from src.execution.flow_hawkes import Hawkes1D
from src.reporting.performance_stats import basic_stats
from src.reporting.html_report import save_html_report
from src.reporting.tearsheet import save_tearsheet
from src.reporting.risk_plus import rolling_es
from src.reporting.pdf_report import build_pdf
from src.reporting.pnl_attribution import attribution_from_exec
from src.reporting.risk_montecarlo import mc_from_df
from src.sim.regime import Regime2State

def step_changes(series, window=50):
    arr = np.array(series[-(window+1):], dtype=float)
    if len(arr) < 2:
        return np.array([])
    return np.diff(arr)

def compute_portfolio_var(routers, window=50):
    invs, changes = [], []
    for r in routers.values():
        any_mm = next(iter(r.venues.values())).mm
        invs.append(float(any_mm.inv))
        ch = step_changes(any_mm.mid_history, window=window)
        if ch.size == 0:
            return 0.0
        changes.append(ch)
    minlen = min(len(c) for c in changes)
    if minlen < 10:
        return 0.0
    X = np.vstack([c[-minlen:] for c in changes]).astype(float)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    cov = np.cov(X)
    cov = np.nan_to_num(cov, nan=0.0, posinf=0.0, neginf=0.0)
    cov = np.clip(cov, -1e4, 1e4)
    inv_vec = np.array(invs, dtype=float).reshape(-1, 1)
    try:
        var_price = float((inv_vec.T @ cov @ inv_vec).item())
    except Exception:
        return 0.0
    if not np.isfinite(var_price) or var_price <= 0.0:
        return 0.0
    return float(1.65 * np.sqrt(var_price))

def run():
    cfg = load_config(); log = get_logger("mm")
    symbols = cfg.symbols
    all_records = []; exec_events = []

    def exec_logger(evt: dict):
        exec_events.append(evt)

    mm_kwargs = dict(
        alpha_weight=cfg.alpha_weight, alpha_smooth=cfg.alpha_smooth,
        max_move=cfg.max_move, base_spread_bps=cfg.base_spread_bps, tick_size=cfg.tick_size,
        tx_fee_bps=cfg.tx_fee_bps, skew_k=cfg.skew_k,
        use_avellaneda=cfg.use_avellaneda, as_gamma=cfg.as_gamma, as_k=cfg.as_k, as_T=cfg.as_T,
        adaptive_tick=cfg.adaptive_tick, min_tick=cfg.min_tick, max_tick=cfg.max_tick,
        vol_low=cfg.vol_low, vol_high=cfg.vol_high
    )
    routers = {s: MarketMakerRouter(s, cfg.venues, cfg.start_price, cfg.tick_size,
                                    cfg.quote_size, cfg.inventory_limit,
                                    mm_kwargs, exec_logger, top_k=cfg.router_top_k)
               for s in symbols}
    sigs = {s: SentimentSignal(smooth=cfg.alpha_smooth) for s in symbols}
    news = {s: synthetic_news_tape(s) for s in symbols}
    news_idx = {s: 0 for s in symbols}
    hawkes = {s: Hawkes1D(cfg.hawkes_mu, cfg.hawkes_alpha, cfg.hawkes_beta) for s in symbols}
    regime = Regime2State()

    csv_path = os.path.join(cfg.events_path, "events_multi_v11.csv")
    os.makedirs(cfg.events_path, exist_ok=True)

    for t in range(cfg.n_steps):
        for s in symbols:
            while news_idx[s] < len(news[s]) and t >= news[s][news_idx[s]].ts:
                headline = news[s][news_idx[s]].headline
                alpha = sigs[s].on_news(headline)
                log.info(f"[{s}] News: '{headline}' alpha_smooth={alpha:.3f}")
                news_idx[s] += 1

        st = regime.step()
        flow_mult = 2.0 if st==Regime2State.STRESS else 1.0

        for s in symbols:
            alpha = sigs[s].last
            routers[s].make_quotes(alpha, ts=t)
            for v in routers[s].venues.values():
                n = 1
                if cfg.use_hawkes:
                    _ = hawkes[s].step_intensity(0); n = 1 + hawkes[s].sample_events()
                for _ in range(int(flow_mult*n)):
                    fills = simulate_external_flow(v.lob, alpha, intensity=1.0, impact_kappa=cfg.impact_kappa, tick=cfg.tick_size)
                    if fills: v.mm.on_fills(fills)
            routers[s].mark_to_market()

        var_pf = compute_portfolio_var(routers, window=50)
        hedged = False
        if np.isfinite(var_pf) and var_pf > cfg.portfolio_var_limit and cfg.hedge_portfolio_on_breach:
            for s in symbols:
                routers[s].hedge_portfolio(cfg.hedge_fraction_portfolio)
            hedged = True; log.info(f"[PF] HEDGE portfolio: VaR {var_pf:.2f} > {cfg.portfolio_var_limit:.2f}")

        for s in symbols:
            mid = routers[s].mid(); inv = routers[s].inventory(); pnl = routers[s].pnl()
            any_mm = next(iter(routers[s].venues.values())).mm
            pnl_series = pd.Series(any_mm.mid_history).diff().fillna(0.0).cumsum()
            es_series = rolling_es(pnl_series, window=cfg.es_window, conf=cfg.es_conf)
            es_val = float(es_series.iloc[-1]) if len(es_series) else 0.0
            all_records.append({"symbol": s, "timestamp": t, "mid": mid, "inventory": inv, "pnl": pnl,
                                "alpha": sigs[s].last, "var_pf": var_pf, "es": es_val,
                                "regime": st, "event": "HEDGE_PF" if hedged else ""})

        if t % 50 == 0:
            for s in symbols:
                mid = routers[s].mid(); inv = routers[s].inventory(); pnl = routers[s].pnl()
                log.info(f"[{s}] Iter {t:4d}: mid={mid:.2f} inv={inv} pnl={pnl:.2f}")

    df = pd.DataFrame(all_records)
    df.to_csv(csv_path, index=False)

    # Execution & attribution
    exec_df = pd.DataFrame(exec_events) if exec_events else pd.DataFrame(columns=["venue","role","side","qty","price","mid","fee_bps","fee","spread_capture","symbol"])
    exec_path = os.path.join("data/market_events", "executions_v11.csv")
    os.makedirs("data/market_events", exist_ok=True); exec_df.to_csv(exec_path, index=False)

    from src.reporting.pnl_attribution import attribution_from_exec
    attrib = attribution_from_exec(exec_df)
    attrib_path = os.path.join("reports", "pnl_attribution_v11.csv")
    os.makedirs("reports", exist_ok=True); attrib.to_csv(attrib_path, index=False)

    # Reports
    out_paths, image_paths = [], []
    for s in symbols:
        sub = df[df["symbol"]==s].reset_index(drop=True)
        stats = basic_stats(sub)
        print(f"==== BASIC STATS [{s}] ===="); print(stats.to_string())
        ts_path = save_tearsheet(sub, os.path.join(cfg.report_path, s))
        html = save_html_report(sub, stats, os.path.join(cfg.report_path, s), "report.html")
        out_paths.append(html); image_paths.append(ts_path)

    pf = df.groupby("timestamp")[["pnl","inventory","var_pf","es"]].sum().reset_index()
    from src.reporting.performance_stats import basic_stats as bs
    pf_stats = bs(pf.rename(columns={"var_pf":"pnl"}))
    ts_pf = save_tearsheet(pf, os.path.join(cfg.report_path, "PORTFOLIO"))
    out_paths.append(save_html_report(pf, pf_stats, os.path.join(cfg.report_path, "PORTFOLIO"), "report.html"))
    image_paths.append(ts_pf)

    mc = mc_from_df(df, n_runs=100, seed=123)
    with open(os.path.join(cfg.report_path, "MC_SUMMARY_v11.json"), "w") as f:
        json.dump(mc, f, indent=2)

    pdf_path = os.path.join(cfg.report_path, "RISK_REPORT_v11.pdf")
    summary = {
        "Symbols": ", ".join(symbols),
        "Final Portfolio PnL": float(pf["pnl"].iloc[-1]) if len(pf) else 0.0,
        "Final Portfolio Inventory": float(pf["inventory"].iloc[-1]) if len(pf) else 0.0,
        "Last Portfolio VaR": float(pf["var_pf"].iloc[-1]) if len(pf) else 0.0,
        "Last Portfolio ES": float(pf["es"].iloc[-1]) if len(pf) else 0.0,
        "MC": mc
    }
    from src.reporting.pdf_report import build_pdf
    build_pdf(pdf_path, "MM_SENTIMENT v11 — Risk Report", summary, image_paths)
    print("PDF report saved:", pdf_path)
    return df

if __name__ == "__main__":
    run()
