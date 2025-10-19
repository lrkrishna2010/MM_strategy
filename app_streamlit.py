import time
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import json

st.set_page_config(page_title="MM_SENTIMENT Dashboard v11", layout="wide")
st.title("📈 MM_SENTIMENT v11 — Impact + Regimes + Smart Router")

data_path = st.text_input("Path to events CSV", "data/market_events/events_multi_v11.csv")
attrib_path = st.text_input("PnL Attribution CSV", "reports/pnl_attribution_v11.csv")
mc_path = st.text_input("MC Summary JSON", "reports/MC_SUMMARY_v11.json")
auto = st.checkbox("Auto-refresh every 2s", value=False)

def load_df(p):
    pth = Path(p)
    if pth.exists():
        try: return pd.read_csv(pth)
        except Exception: return pd.DataFrame()
    return pd.DataFrame()

while True:
    df = load_df(data_path)
    if df.empty:
        st.info("CSV not found yet. Run `python main.py` first to generate it.")
    else:
        symbols = sorted(df["symbol"].unique())
        sym = st.selectbox("Symbol", symbols, key="sym")
        sub = df[df["symbol"]==sym].copy()

        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(px.line(sub, x="timestamp", y="pnl", title=f"{sym} PnL"), use_container_width=True)
        with c2: st.plotly_chart(px.line(sub, x="timestamp", y="inventory", title=f"{sym} Inventory"), use_container_width=True)

        if "alpha" in sub.columns:
            st.plotly_chart(px.line(sub, x="timestamp", y="alpha", title=f"{sym} Alpha"), use_container_width=True)

        if "var_pf" in df.columns:
            pf = df.groupby("timestamp")["var_pf"].mean().reset_index()
            st.plotly_chart(px.line(pf, x="timestamp", y="var_pf", title="Portfolio VaR (1-step 95%)"), use_container_width=True)

        st.subheader("Execution PnL Attribution (by venue)")
        if Path(attrib_path).exists():
            attrib = pd.read_csv(attrib_path); st.dataframe(attrib, use_container_width=True)
        else:
            st.info("Attribution CSV not found yet.")

        st.subheader("Monte Carlo Summary")
        if Path(mc_path).exists():
            mc = json.loads(Path(mc_path).read_text()); st.json(mc)
        else:
            st.info("MC summary JSON not found yet.")

    if not auto: break
    import streamlit.runtime.scriptrunner.script_runner as st_runner
time.sleep(2)
st_runner.RerunException(st_runner.RerunData(None))

