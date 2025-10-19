# MM_SENTIMENT v11

A clean, production-ready multi-venue market making simulator driven by news sentiment.
Includes Avellaneda–Stoikov quoting, Hawkes bursts, regime switching, adaptive ticks, market impact,
portfolio VaR hedging, PnL attribution, Monte Carlo, and a Streamlit dashboard.

## Setup
```bash
cd MM_SENTIMENT_v11
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
# Dashboard
streamlit run app_streamlit.py
```

## Config
See `config.yaml` for knobs like `router_top_k`, `impact_kappa`, `portfolio_var_limit`.
# MM_strategy
