"""
app.py
Complete Streamlit Dashboard for AutoHedge Pro
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Import all modules
from config import DEFAULT_START_CAPITAL
from market_data import get_yfinance_price_series
from alpaca_trading import alpaca_place_market_order, alpaca_get_positions, alpaca_get_account
from data_manager import load_runs
from backtest_engine import run_enhanced_backtest
from autohedge_agent import run_autohedge

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="AutoHedge Pro Trading Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================

st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
    }
    .success-box {
        background-color: #d1fae5;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #10b981;
    }
    .warning-box {
        background-color: #fef3c7;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f59e0b;
    }
    .error-box {
        background-color: #fee2e2;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ef4444;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# TITLE & HEADER
# ============================================================================

st.markdown('<h1 class="main-header">AutoHedge Pro</h1>', unsafe_allow_html=True)
st.markdown("### AI-Driven Trading & Risk Management System")

st.markdown("""
**Production Features:**
- **Real-Time Market Data** - RSI, ADX, ATR, Bollinger Bands, Volume Analysis
- **Enhanced Backtesting** - Stop-loss/take-profit execution, long/short support
- **Risk-Adjusted Metrics** - Sharpe Ratio, Sortino Ratio, Maximum Drawdown
- **AI-Powered Analysis** - Structured trade ideas with Groq LLMs
- **Custom Risk Controls** - Position sizing, notional limits
- **Alpaca Integration** - Paper trading execution
""")

# ============================================================================
# LOAD DATA
# ============================================================================

df_all = load_runs()

# ============================================================================
# SIDEBAR - FILTERS
# ============================================================================

st.sidebar.header("Filters & Settings")

selected_stock = None
df = df_all.copy()

if df_all.empty:
    st.sidebar.info("No runs yet. Create one in the 'New Run' tab!")
else:
    # Stock filter
    if "current_stock" in df_all.columns:
        available_stocks = sorted(df_all["current_stock"].dropna().unique())
    else:
        available_stocks = []
    
    if available_stocks:
        selected_stock = st.sidebar.selectbox(
            "Select Stock",
            options=["All"] + available_stocks,
            index=0
        )
        
        if selected_stock != "All":
            df = df_all[df_all["current_stock"] == selected_stock]
    
    # Date range filter
    if "run_time" in df_all.columns and not df_all["run_time"].isna().all():
        min_date = df_all["run_time"].min()
        max_date = df_all["run_time"].max()
        
        if pd.notna(min_date) and pd.notna(max_date):
            date_range = st.sidebar.date_input(
                "Date Range",
                value=[min_date.date(), max_date.date()],
                max_value=datetime.now().date()
            )
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                df = df[
                    (df["run_time"].dt.date >= start_date) &
                    (df["run_time"].dt.date <= end_date)
                ]

st.sidebar.markdown("---")
st.sidebar.markdown("### Dashboard Stats")
if not df_all.empty:
    st.sidebar.metric("Total Runs", len(df_all))
    if "custom_risk_approved" in df_all.columns:
        approved = df_all["custom_risk_approved"].sum()
        st.sidebar.metric("Approved Trades", f"{approved}/{len(df_all)}")

# ============================================================================
# MAIN TABS
# ============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Latest Analysis",
    "History",
    "Backtest",
    "Alpaca",
    "New Run"
])

# ============================================================================
# TAB 1: LATEST ANALYSIS
# ============================================================================

with tab1:
    st.markdown("## Latest AutoHedge Analysis")
    
    if df.empty or (selected_stock == "All" and not df_all.empty):
        st.info("Select a specific stock from the sidebar to view detailed analysis.")
    elif selected_stock is None or selected_stock == "All":
        st.info("No runs available. Create one in the 'New Run' tab.")
    else:
        latest = df.sort_values("run_time", ascending=False).iloc[0]
        
        # Header
        col_h1, col_h2, col_h3 = st.columns([2, 1, 1])
        with col_h1:
            st.markdown(f"### {latest.get('current_stock', 'N/A')}")
        with col_h2:
            st.markdown(f"**Run:** {latest['run_time'].strftime('%Y-%m-%d %H:%M')}")
        with col_h3:
            risk_status = "Approved" if latest.get("custom_risk_approved") else "Rejected"
            st.markdown(f"**Risk:** {risk_status}")
        
        # Market Data Snapshot
        if "market_data_snapshot" in latest and isinstance(latest["market_data_snapshot"], dict):
            md = latest["market_data_snapshot"]
            
            if "error" not in md:
                st.markdown("#### Market Data Snapshot")
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                
                with col_m1:
                    price_delta = md.get('price_change_pct', 0)
                    st.metric(
                        "Current Price",
                        f"${md.get('current_price', 0):.2f}",
                        f"{price_delta:+.2f}%",
                        delta_color="normal" if price_delta >= 0 else "inverse"
                    )
                with col_m2:
                    rsi = md.get('rsi_14')
                    rsi_label = "Oversold" if rsi and rsi < 30 else "Overbought" if rsi and rsi > 70 else "Neutral"
                    st.metric("RSI (14)", f"{rsi:.1f}" if rsi else "N/A", rsi_label)
                with col_m3:
                    adx = md.get('adx_14')
                    trend = "Strong" if adx and adx > 25 else "Weak" if adx else "N/A"
                    st.metric("ADX (14)", f"{adx:.1f}" if adx else "N/A", trend)
                with col_m4:
                    vol_ratio = md.get('volume_ratio')
                    st.metric("Volume Ratio", f"{vol_ratio:.2f}x" if vol_ratio else "N/A")
        
        st.markdown("---")
        
        # Thesis
        st.markdown("#### Investment Thesis")
        thesis = latest.get("thesis", "No thesis available")
        st.markdown(f'<div class="metric-card">{thesis}</div>', unsafe_allow_html=True)
        
        # Quant Analysis
        st.markdown("#### Quantitative Analysis")
        qa = latest.get("quant_analysis", {})
        
        if isinstance(qa, dict) and qa:
            col_q1, col_q2, col_q3, col_q4 = st.columns(4)
            
            with col_q1:
                tech_score = qa.get('technical_score', 0)
                st.metric("Technical Score", f"{tech_score*100:.1f}%" if tech_score else "N/A")
            with col_q2:
                trend = qa.get('trend_strength', 0)
                st.metric("Trend Strength", f"{trend*100:.1f}%" if trend else "N/A")
            with col_q3:
                vol_score = qa.get('volume_score', 0)
                st.metric("Volume Score", f"{vol_score*100:.1f}%" if vol_score else "N/A")
            with col_q4:
                prob = qa.get('probability_score', 0)
                st.metric("Win Probability", f"{prob*100:.1f}%" if prob else "N/A")
            
            # Key Levels
            key_levels = qa.get("key_levels", {})
            if isinstance(key_levels, dict) and key_levels:
                st.markdown("**Key Technical Levels:**")
                col_k1, col_k2, col_k3 = st.columns(3)
                
                with col_k1:
                    support = key_levels.get('support')
                    st.metric("Support", f"${support:.2f}" if support else "N/A")
                with col_k2:
                    pivot = key_levels.get('pivot')
                    st.metric("Pivot", f"${pivot:.2f}" if pivot else "N/A")
                with col_k3:
                    resistance = key_levels.get('resistance')
                    st.metric("Resistance", f"${resistance:.2f}" if resistance else "N/A")
        
        st.markdown("---")
        
        # Risk Assessment
        st.markdown("#### Risk Assessment")
        ra = latest.get("risk_assessment", {})
        
        if isinstance(ra, dict) and ra:
            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            
            with col_r1:
                pos_size = ra.get('position_size')
                st.metric("Position Size", f"${pos_size:,.0f}" if pos_size else "N/A")
            with col_r2:
                max_dd = ra.get('max_drawdown_risk')
                st.metric("Max DD Risk", f"{max_dd*100:.1f}%" if max_dd else "N/A")
            with col_r3:
                mkt_exp = ra.get('market_risk_exposure')
                st.metric("Market Exposure", f"{mkt_exp*100:.1f}%" if mkt_exp else "N/A")
            with col_r4:
                overall = ra.get('overall_risk_score')
                st.metric("Overall Risk", f"{overall*100:.1f}%" if overall else "N/A")
        
        st.markdown("---")
        
        # Order Details
        st.markdown("#### Recommended Order")
        
        col_o1, col_o2 = st.columns([2, 1])
        with col_o1:
            approved = latest.get('custom_risk_approved')
            reason = latest.get('custom_risk_reason', 'N/A')
            
            if approved:
                st.markdown(f'<div class="success-box"><strong>Risk Check: APPROVED</strong><br>{reason}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="warning-box"><strong>Risk Check: REJECTED</strong><br>{reason}</div>', unsafe_allow_html=True)
        
        # Order metrics
        col_ord1, col_ord2, col_ord3 = st.columns(3)
        
        with col_ord1:
            side = latest.get("order_side", "N/A")
            entry = latest.get("order_entry_price")
            st.metric("Side", side)
            st.metric("Entry Price", f"${entry:.2f}" if entry else "N/A")
        
        with col_ord2:
            qty = latest.get("order_quantity")
            sl = latest.get("order_stop_loss")
            st.metric("Quantity", f"{qty:.4f}" if qty else "N/A")
            st.metric("Stop Loss", f"${sl:.2f}" if sl else "N/A")
        
        with col_ord3:
            notional = latest.get("order_notional")
            tp = latest.get("order_take_profit")
            st.metric("Notional", f"${notional:,.2f}" if notional else "N/A")
            st.metric("Take Profit", f"${tp:.2f}" if tp else "N/A")
        
        # Execute on Alpaca
        st.markdown("---")
        st.markdown("#### Execute Trade")
        
        col_exec1, col_exec2 = st.columns([3, 1])
        with col_exec1:
            st.info("This will place a LIVE order on your Alpaca paper trading account.")
        with col_exec2:
            if st.button("Send to Alpaca", type="primary", use_container_width=True):
                if not latest.get("order_side") or not latest.get("order_quantity"):
                    st.error("Order missing required fields.")
                elif not latest.get("custom_risk_approved"):
                    st.warning("Order not approved by risk controls!")
                else:
                    try:
                        placed = alpaca_place_market_order(
                            symbol=selected_stock,
                            side=str(latest["order_side"]),
                            qty=float(latest["order_quantity"])
                        )
                        st.success(f"Order placed! ID: {placed.id}")
                    except Exception as e:
                        st.error(f"Error: {e}")

# ============================================================================
# TAB 2: HISTORY
# ============================================================================

with tab2:
    st.markdown("## Historical Runs")
    
    if df_all.empty:
        st.info("No historical runs yet.")
    else:
        # Summary metrics
        col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
        
        with col_sum1:
            st.metric("Total Runs", len(df_all))
        with col_sum2:
            if "custom_risk_approved" in df_all.columns:
                approved_pct = (df_all["custom_risk_approved"].sum() / len(df_all)) * 100
                st.metric("Approval Rate", f"{approved_pct:.1f}%")
        with col_sum3:
            if "order_side" in df_all.columns:
                longs = (df_all["order_side"].astype(str).str.upper().isin(["BUY", "LONG"])).sum()
                st.metric("Long Positions", longs)
        with col_sum4:
            if "order_side" in df_all.columns:
                shorts = (df_all["order_side"].astype(str).str.upper().isin(["SELL", "SHORT"])).sum()
                st.metric("Short Positions", shorts)
        
        st.markdown("---")
        
        # Data table
        display_cols = [
            col for col in [
                "run_time", "current_stock", "order_side", "order_quantity",
                "order_entry_price", "order_stop_loss", "order_take_profit",
                "order_notional", "custom_risk_approved"
            ] if col in df_all.columns
        ]
        
        display_df = df_all[display_cols].sort_values("run_time", ascending=False).head(50)
        
        # Format display
        if "run_time" in display_df.columns:
            display_df["run_time"] = display_df["run_time"].dt.strftime("%Y-%m-%d %H:%M")
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

# ============================================================================
# TAB 3: BACKTEST
# ============================================================================

with tab3:
    st.markdown("## Enhanced Backtest Engine")
    
    if df.empty or selected_stock is None or selected_stock == "All":
        st.info("Select a specific stock from the sidebar to run backtest.")
    else:
        st.markdown("### Configuration")
        
        col_bt1, col_bt2, col_bt3 = st.columns(3)
        
        with col_bt1:
            start_capital = st.number_input(
                "Starting Capital ($)",
                min_value=1_000.0,
                max_value=10_000_000.0,
                value=DEFAULT_START_CAPITAL,
                step=1_000.0
            )
        
        with col_bt2:
            risk_pct = st.slider(
                "Risk per Trade (%)",
                min_value=1.0,
                max_value=50.0,
                value=5.0,
                step=1.0
            )
        
        with col_bt3:
            holding_days = st.slider(
                "Max Holding Period (days)",
                min_value=1,
                max_value=30,
                value=5,
                step=1
            )
        
        if st.button("Run Backtest", type="primary", use_container_width=True):
            with st.spinner("Running backtest with stop-loss/take-profit logic..."):
                metrics, trades_df, equity_series = run_enhanced_backtest(
                    df_runs=df,
                    ticker=selected_stock,
                    start_capital=start_capital,
                    risk_per_trade_pct=risk_pct / 100.0,
                    holding_period_days=holding_days
                )
            
            if metrics is None:
                st.warning("No valid trade signals to backtest.")
            else:
                st.markdown("### Performance Metrics")
                
                # Main metrics
                col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
                
                with col_m1:
                    st.metric(
                        "End Capital",
                        f"${metrics['end_capital']:,.0f}",
                        f"{metrics['total_return']*100:+.1f}%"
                    )
                with col_m2:
                    cagr = metrics.get('cagr')
                    st.metric("CAGR", f"{cagr*100:.2f}%" if cagr else "N/A")
                with col_m3:
                    win_rate = metrics.get('win_rate')
                    st.metric("Win Rate", f"{win_rate*100:.1f}%" if win_rate else "N/A")
                with col_m4:
                    pf = metrics.get('profit_factor')
                    st.metric("Profit Factor", f"{pf:.2f}" if pf else "N/A")
                with col_m5:
                    st.metric("Trades", metrics['num_trades'])
                
                st.markdown("### Risk-Adjusted Performance")
                
                col_r1, col_r2, col_r3 = st.columns(3)
                
                with col_r1:
                    mdd = metrics.get('max_drawdown')
                    st.metric("Max Drawdown", f"{mdd*100:.1f}%" if mdd else "N/A")
                with col_r2:
                    sharpe = metrics.get('sharpe_ratio')
                    st.metric(
                        "Sharpe Ratio",
                        f"{sharpe:.2f}" if sharpe else "N/A",
                        help="Risk-adjusted return (>1 good, >2 excellent)"
                    )
                with col_r3:
                    sortino = metrics.get('sortino_ratio')
                    st.metric(
                        "Sortino Ratio",
                        f"{sortino:.2f}" if sortino else "N/A",
                        help="Return vs downside risk"
                    )
                
                # Exit breakdown
                if 'exit_breakdown' in metrics and metrics['exit_breakdown']:
                    st.markdown("### Exit Analysis")
                    exit_data = pd.DataFrame([
                        {"Exit Type": k, "Count": v}
                        for k, v in metrics['exit_breakdown'].items()
                    ])
                    
                    col_e1, col_e2 = st.columns([1, 2])
                    with col_e1:
                        st.dataframe(exit_data, use_container_width=True, hide_index=True)
                    with col_e2:
                        st.bar_chart(exit_data.set_index("Exit Type"))
                
                # Equity curve
                st.markdown("### Equity Curve")
                st.line_chart(equity_series)
                
                # Trade log
                st.markdown("### Trade Log")
                trades_display = trades_df[[
                    'run_time', 'side', 'entry_price', 'exit_price',
                    'stop_loss', 'take_profit', 'pnl', 'return_pct', 'exit_reason'
                ]].copy()
                
                # Format
                trades_display['pnl'] = trades_display['pnl'].apply(lambda x: f"${x:,.2f}")
                trades_display['return_pct'] = trades_display['return_pct'].apply(lambda x: f"{x*100:.2f}%")
                
                st.dataframe(trades_display, use_container_width=True, hide_index=True)

# ============================================================================
# TAB 4: ALPACA
# ============================================================================

with tab4:
    st.markdown("## Alpaca Paper Trading Account")
    
    try:
        acct = alpaca_get_account()
    except Exception as e:
        acct = None
        st.error(f"Could not connect to Alpaca: {e}")
    
    if acct:
        # Account metrics
        col_a1, col_a2, col_a3, col_a4 = st.columns(4)
        
        with col_a1:
            st.metric("Equity", f"${float(acct.equity):,.2f}")
        with col_a2:
            st.metric("Cash", f"${float(acct.cash):,.2f}")
        with col_a3:
            st.metric("Portfolio Value", f"${float(acct.portfolio_value):,.2f}")
        with col_a4:
            st.metric("Buying Power", f"${float(acct.buying_power):,.2f}")
        
        st.markdown("---")
        
        # Positions
        positions = alpaca_get_positions()
        
        if positions:
            st.markdown("### Open Positions")
            
            pos_data = []
            for p in positions:
                pos_data.append({
                    "Symbol": p.symbol,
                    "Qty": float(p.qty),
                    "Avg Entry": f"${float(p.avg_entry_price):.2f}",
                    "Current Value": f"${float(p.market_value):,.2f}",
                    "Unrealized P&L": f"${float(p.unrealized_pl):,.2f}",
                    "P&L %": f"{(float(p.unrealized_plpc)*100):.2f}%"
                })
            
            st.dataframe(pd.DataFrame(pos_data), use_container_width=True, hide_index=True)
        else:
            st.info("No open positions.")
    else:
        st.warning("Alpaca API keys not configured. Set APCA_API_KEY_ID and APCA_API_SECRET_KEY in .env file.")

# ============================================================================
# TAB 5: NEW RUN
# ============================================================================

with tab5:
    st.markdown("## Run New AutoHedge Analysis")
    
    with st.form("new_run_form"):
        st.markdown("### Configuration")
        
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            tickers_input = st.text_input(
                "Tickers (comma-separated)",
                value="TSLA",
                help="Enter one or more stock tickers separated by commas"
            )
            
            allocation = st.number_input(
                "Allocation ($)",
                min_value=1_000.0,
                max_value=10_000_000.0,
                value=10_000.0,
                step=1_000.0
            )
            
            strategy = st.selectbox(
                "Strategy Type",
                ["momentum", "mean-reversion", "trend-following", "value"],
                help="Trading strategy to apply"
            )
        
        with col_f2:
            risk_level = st.slider(
                "Risk Level (1-10)",
                min_value=1,
                max_value=10,
                value=5,
                help="1 = Very conservative, 10 = Very aggressive"
            )
            
            target_return = st.slider(
                "Target Return (%)",
                min_value=1.0,
                max_value=50.0,
                value=10.0,
                step=1.0,
                help="Target return percentage"
            )
            
            max_risk = st.slider(
                "Maximum Risk (%)",
                min_value=0.5,
                max_value=10.0,
                value=2.0,
                step=0.5,
                help="Maximum acceptable loss percentage"
            )
        
        submitted = st.form_submit_button(
            "Run AutoHedge Analysis",
            type="primary",
            use_container_width=True
        )
    
    if submitted:
        tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
        
        if not tickers:
            st.error("Please provide at least one valid ticker.")
        else:
            with st.spinner(f"Analyzing {', '.join(tickers)}... Fetching market data and running AI analysis..."):
                try:
                    result = run_autohedge(
                        stocks=tickers,
                        allocation_usd=allocation,
                        strategy_type=strategy,
                        risk_level=risk_level,
                        target_return_pct=target_return / 100.0,
                        max_risk_pct=max_risk / 100.0
                    )
                    
                    st.success("Analysis completed and saved!")
                    
                    # Show key results
                    col_res1, col_res2 = st.columns(2)
                    
                    with col_res1:
                        st.markdown("#### Results Summary")
                        st.write(f"**Stock:** {result.get('current_stock')}")
                        st.write(f"**Side:** {result.get('order_side')}")
                        st.write(f"**Entry:** ${result.get('order_entry_price', 0):.2f}")
                        st.write(f"**Risk Approved:** {'Yes' if result.get('custom_risk_approved') else 'No'}")
                    
                    with col_res2:
                        st.markdown("#### Thesis")
                        st.write(result.get('thesis', 'No thesis'))
                    
                    with st.expander("View Full JSON Output"):
                        st.json(result)
                    
                    st.info("Go to 'Latest Analysis' tab to see full details, or select the stock from sidebar.")
                    
                except Exception as e:
                    st.error(f"Error running AutoHedge: {e}")
                    st.exception(e)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>AutoHedge Pro</strong> - AI-Driven Trading & Risk Management System</p>
    <p>Built with Streamlit • Powered by Groq LLMs • Alpaca Paper Trading</p>
    <p style='font-size: 0.8em;'>For educational and research purposes only. Not financial advice.</p>
</div>
""", unsafe_allow_html=True)