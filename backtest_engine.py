# ============================================================================
# FILE 6: backtest_engine.py
# Enhanced backtesting with stop-loss and take-profit
# ============================================================================

from datetime import timedelta
import pandas as pd
import numpy as np
import yfinance as yf


def run_enhanced_backtest(
    df_runs: pd.DataFrame,
    ticker: str,
    start_capital: float = 100_000.0,
    risk_per_trade_pct: float = 0.05,
    holding_period_days: int = 5
):
    """
    Enhanced backtest with:
    - Long and short position support
    - Stop-loss and take-profit execution
    - Intraday price checking
    - Risk-adjusted metrics (Sharpe, Sortino)
    """
    if df_runs.empty:
        return None, None, None
    
    df = df_runs.copy()
    df = df[df["order_side"].astype(str).str.upper().isin(["BUY", "LONG", "SELL", "SHORT"])]
    if df.empty:
        return None, None, None
    
    df = df.sort_values("run_time")
    
    trades = []
    capital = start_capital
    equity = [capital]
    equity_dates = [df["run_time"].min()]
    
    for _, row in df.iterrows():
        run_time = row["run_time"]
        if pd.isna(run_time):
            continue
        
        side = str(row["order_side"]).upper()
        is_long = side in ["BUY", "LONG"]
        
        entry_day = run_time.date()
        exit_day = entry_day + timedelta(days=holding_period_days)
        
        # Fetch price data
        prices = yf.download(
            ticker,
            start=entry_day,
            end=exit_day + timedelta(days=3),
            progress=False
        )
        
        if prices.empty or len(prices) < 1:
            continue
        
        # Entry
        entry_ts = prices.index[0]
        entry_price = float(prices["Close"].iloc[0])
        
        # Position sizing
        position_notional = capital * risk_per_trade_pct
        if position_notional <= 0:
            continue
        
        quantity = position_notional / entry_price
        
        # Get AI-generated stops
        stop_loss = row.get("order_stop_loss")
        take_profit = row.get("order_take_profit")
        
        # Simulate intraday execution
        exit_price = None
        exit_ts = None
        exit_reason = "holding_period"
        
        for i in range(1, len(prices)):
            day_high = float(prices["High"].iloc[i])
            day_low = float(prices["Low"].iloc[i])
            day_close = float(prices["Close"].iloc[i])
            current_ts = prices.index[i]
            
            # Check stop loss
            if stop_loss and pd.notna(stop_loss):
                if is_long and day_low <= stop_loss:
                    exit_price = stop_loss
                    exit_ts = current_ts
                    exit_reason = "stop_loss"
                    break
                elif not is_long and day_high >= stop_loss:
                    exit_price = stop_loss
                    exit_ts = current_ts
                    exit_reason = "stop_loss"
                    break
            
            # Check take profit
            if take_profit and pd.notna(take_profit):
                if is_long and day_high >= take_profit:
                    exit_price = take_profit
                    exit_ts = current_ts
                    exit_reason = "take_profit"
                    break
                elif not is_long and day_low <= take_profit:
                    exit_price = take_profit
                    exit_ts = current_ts
                    exit_reason = "take_profit"
                    break
            
            # Check holding period
            if (current_ts.date() - entry_day).days >= holding_period_days:
                exit_price = day_close
                exit_ts = current_ts
                exit_reason = "holding_period"
                break
        
        # Default exit if no trigger
        if exit_price is None:
            exit_ts = prices.index[-1]
            exit_price = float(prices["Close"].iloc[-1])
        
        # Calculate P&L
        if is_long:
            pnl = quantity * (exit_price - entry_price)
        else:  # SHORT
            pnl = quantity * (entry_price - exit_price)
        
        capital_after = capital + pnl
        return_pct = pnl / position_notional if position_notional > 0 else 0
        
        trades.append({
            "run_time": run_time,
            "side": side,
            "entry_time": entry_ts,
            "exit_time": exit_ts,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "quantity": quantity,
            "position_notional": position_notional,
            "pnl": pnl,
            "return_pct": return_pct,
            "exit_reason": exit_reason,
            "capital_before": capital,
            "capital_after": capital_after,
        })
        
        capital = capital_after
        equity.append(capital)
        equity_dates.append(exit_ts)
    
    if not trades:
        return None, None, None
    
    trades_df = pd.DataFrame(trades)
    equity_series = pd.Series(equity[1:], index=equity_dates[1:], name="equity")
    
    # Calculate metrics
    total_return = capital / start_capital - 1.0
    start_date = trades_df["entry_time"].min()
    end_date = trades_df["exit_time"].max()
    days = (end_date - start_date).days if start_date and end_date else 0
    years = days / 365.25 if days > 0 else None
    cagr = (capital / start_capital) ** (1 / years) - 1 if years and years > 0 else None
    
    wins = (trades_df["pnl"] > 0).sum()
    losses = (trades_df["pnl"] < 0).sum()
    win_rate = wins / (wins + losses) if (wins + losses) > 0 else None
    
    avg_win = trades_df.loc[trades_df["pnl"] > 0, "pnl"].mean()
    avg_loss = trades_df.loc[trades_df["pnl"] < 0, "pnl"].mean()
    gross_profit = trades_df.loc[trades_df["pnl"] > 0, "pnl"].sum()
    gross_loss = trades_df.loc[trades_df["pnl"] < 0, "pnl"].sum()
    profit_factor = (gross_profit / abs(gross_loss)) if gross_loss < 0 else None
    
    # Max Drawdown
    equity_values = equity_series.values
    running_max = np.maximum.accumulate(equity_values)
    dd = equity_values / running_max - 1.0
    max_drawdown = dd.min() if len(dd) > 0 else None
    
    # Sharpe Ratio
    returns = trades_df["return_pct"].values
    sharpe_ratio = None
    sortino_ratio = None
    
    if len(returns) > 1:
        mean_return = np.mean(returns)
        std_return = np.std(returns, ddof=1)
        num_trades_per_year = 252 / holding_period_days if holding_period_days > 0 else 50
        annualized_return = mean_return * num_trades_per_year
        annualized_std = std_return * np.sqrt(num_trades_per_year)
        risk_free_rate = 0.02
        
        if annualized_std > 0:
            sharpe_ratio = (annualized_return - risk_free_rate) / annualized_std
        
        # Sortino Ratio
        negative_returns = returns[returns < 0]
        if len(negative_returns) > 1:
            downside_std = np.std(negative_returns, ddof=1)
            annualized_downside = downside_std * np.sqrt(num_trades_per_year)
            if annualized_downside > 0:
                sortino_ratio = (annualized_return - risk_free_rate) / annualized_downside
    
    exit_breakdown = trades_df["exit_reason"].value_counts().to_dict()
    
    metrics = {
        "start_capital": start_capital,
        "end_capital": capital,
        "total_return": total_return,
        "cagr": cagr,
        "num_trades": len(trades_df),
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "max_drawdown": max_drawdown,
        "sharpe_ratio": sharpe_ratio,
        "sortino_ratio": sortino_ratio,
        "exit_breakdown": exit_breakdown,
    }
    
    return metrics, trades_df, equity_series