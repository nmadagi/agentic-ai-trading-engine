# 🤖 Agentic AI Trading Engine

> A modular, multi-agent AI system for autonomous equity trading — powered by LLM-driven agents, a backtesting engine, real-time market data, and Alpaca paper trading integration.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python) ![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red?logo=streamlit) ![Alpaca](https://img.shields.io/badge/Alpaca-Paper%20Trading-brightgreen) ![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## 📌 Overview

The **Agentic AI Trading Engine** is a fully modular Python project that simulates how an autonomous AI system can analyze markets, generate trading signals, manage risk, and execute trades — all without manual intervention.

It combines:
- 🧠 **LLM-based agentic reasoning** for trade decision-making
- 📊 **Streamlit dashboard** for live monitoring and control
- 🔄 **AutoHedge agent** for automated hedge position management
- 📈 **Backtesting engine** for strategy validation
- 🏦 **Alpaca paper trading** for simulated order execution

---

## 🗂️ Project Structure

```
agentic-ai-trading-engine/
├── app.py                  # Streamlit dashboard (main UI)
├── alpaca_trading.py       # Alpaca broker integration & order execution
├── autohedge_agent.py      # Autonomous hedging agent logic
├── backtest_engine.py      # Strategy backtesting framework
├── config.py               # Global config (API keys, parameters)
├── data_manager.py         # Data loading, caching, preprocessing
├── market_data.py          # Real-time & historical market data fetching
├── risk_management.py      # Position sizing, stop-loss, drawdown controls
├── requirements.txt        # Python dependencies
└── .gitignore
```

---

## ⚙️ Key Features

| Feature | Description |
|---|---|
| 🤖 Multi-Agent Architecture | Separate agents for signals, hedging, and risk |
| 📉 Backtesting Engine | Validate strategies on historical data before live trading |
| 🏦 Alpaca Paper Trading | Execute simulated trades via Alpaca's paper trading API |
| 🛡️ Risk Management | Configurable stop-loss, position limits, max drawdown controls |
| 📊 Streamlit Dashboard | Real-time portfolio view, trade log, and P&L charts |
| 🔀 AutoHedge Agent | Automatically manages hedge positions to offset directional risk |

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/nmadagi/agentic-ai-trading-engine.git
cd agentic-ai-trading-engine
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API keys
Edit `config.py` and add your Alpaca paper trading credentials:
```python
ALPACA_API_KEY = "your_key_here"
ALPACA_SECRET_KEY = "your_secret_here"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
```

### 4. Run the dashboard
```bash
streamlit run app.py
```

---

## 🧠 Agent Architecture

```
┌────────────────────────────────────┐
│          Streamlit Dashboard        │
└────────────┬───────────────────────┘
             │
    ┌────────▼────────┐
    │  Market Data     │◄── Real-time prices, OHLCV
    └────────┬─────────┘
             │
    ┌────────▼─────────┐
    │  Signal Agent     │◄── LLM reasoning + technical indicators
    └────────┬──────────┘
             │
    ┌────────▼──────────┐     ┌──────────────────┐
    │  Risk Manager      │────►│  AutoHedge Agent │
    └────────┬───────────┘     └──────────────────┘
             │
    ┌────────▼──────────┐
    │  Alpaca Executor   │◄── Paper trade orders
    └────────────────────┘
```

---

## 📦 Tech Stack

- **Python 3.10+**
- **Streamlit** — Dashboard & UI
- **Alpaca Trade API** — Paper trading broker
- **Pandas / NumPy** — Data manipulation
- **Plotly** — Interactive charts
- **OpenAI / LLM API** — Agentic trade reasoning

---

## ⚠️ Disclaimer

This project is for **educational and research purposes only**. It uses paper trading and synthetic logic. Do not use this for real financial decisions.

---

## 👤 Author

**Nitin Madagi** | [GitHub](https://github.com/nmadagi) | [Portfolio](https://nmadagi.github.io/portfolio)

## 📄 License

This project is licensed under the [MIT License](LICENSE).
