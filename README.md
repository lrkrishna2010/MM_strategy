#  MM Strategy — Sentiment-Driven Multi-Venue Market Maker

A **production-ready quantitative market making simulator** powered by **news sentiment**, **order book imbalance**, and **portfolio VaR-based hedging**.  
It integrates *Avellaneda–Stoikov* quoting, *adaptive spread control*, *multi-venue routing*, *Monte Carlo risk estimation*, and a *Streamlit dashboard* for live visualization.

---

##  Features

-  **Sentiment-Driven Alpha** — NLP-based news signals blended with order book imbalance.
-  **Avellaneda–Stoikov Model** — Dynamic reservation price and spread adjustment.
-  **Multi-Venue Router** — Smart order routing with depth-aware liquidity allocation.
-  **Portfolio Risk Manager** — Value-at-Risk (VaR) monitoring and inventory hedging.
-  **PnL Attribution Engine** — Tracks realized/unrealized PnL, Sharpe, and exposure.
-  **Monte Carlo Simulation** — Scenario testing across regimes and volatility surfaces.
-  **Streamlit Dashboard** — Interactive visualization for simulation and analytics.

---

##  Project Structure

```
MM_strategy/
│
├── main.py                       # Entry point for simulation
├── app_streamlit.py               # Streamlit dashboard
├── config.yaml                    # Configuration parameters
├── requirements.txt               # Dependencies
│
├── src/
│   ├── alpha/                     # Alpha models (sentiment, OBI, signal blender)
│   ├── execution/                 # Market making & venue routing logic
│   ├── pricing/                   # Reservation price & spread models
│   ├── reporting/                 # Performance & PDF reporting
│   ├── sim/                       # Simulation engine
│   └── utils/                     # Config loading & helper utilities
│
└── reports/
    └── RISK_REPORT_v11.pdf        # Example generated PDF report
```

---

##  Setup Instructions

```bash
# Clone repository
git clone https://github.com/lrkrishna2010/MM_strategy.git
cd MM_strategy

# Create and activate environment
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# or
.venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## Running the Simulation

```bash
python main.py
```

The simulation will stream logs such as:
```
[XYZ] Iter  200: mid=100.23 inv=-40 pnl=1234.56
[PF] HEDGE portfolio: VaR 1050.00 > 1000.00
==== BASIC STATS [XYZ] ====
pnl_end=1234.56, sharpe_like=1.84
```

---

##  Launching the Dashboard

```bash
streamlit run app_streamlit.py
```

The dashboard visualizes:
- Sentiment time series  
- Quotes and mid-price trajectories  
- Inventory and PnL evolution  
- Portfolio risk vs VaR threshold  

---

##  Configuration

Edit **`config.yaml`** to tune:
| Parameter | Description |
|------------|-------------|
| `router_top_k` | Number of venues to route quotes to |
| `impact_kappa` | Market impact coefficient |
| `portfolio_var_limit` | VaR constraint for hedging |
| `alpha_smooth` | EMA smoothing factor for blended alpha |
| `inventory_limit` | Maximum allowed inventory per asset |

---

##  Theoretical Foundations

- **Avellaneda & Stoikov (2008)** — High-frequency market making with inventory and risk aversion.
- **Cartea & Jaimungal (2016)** — Algorithmic and High-Frequency Trading: optimal execution under risk.
- **Hawkes Processes** — Captures self-exciting market order bursts.
- **Value-at-Risk (VaR)** — Portfolio risk constraint for inventory hedging.

---

##  Example Output

After running:
```
==== BASIC STATS [XYZ] ====
pnl_end        12350.20
inv_end         -400.00
sharpe_like        2.48
PDF report saved: reports/RISK_REPORT_v11.pdf
```

---

##  Future Enhancements

- Integrate **LSTM or Transformer-based sentiment models**  
- Add **live data ingestion** (news APIs, Yahoo Finance, Polygon.io)  
- Expand to **cross-asset hedging and correlation-aware VaR**  
- Include **unit tests**, **logging configs**, and **Docker deployment**

---

##  Contributing

Pull requests are welcome!  
For major changes, please open an issue first to discuss the proposal.

---

##  License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

##  Author

**Radhesh Krishna Lalam**  
BSc Finance & Mathematics — University of Essex    
GitHub: [@lrkrishna2010](https://github.com/lrkrishna2010)

---


