# ============================================================================
# FILE 2: market_data.py
# Real-time market data fetching and technical indicators
# ============================================================================

from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf


def fetch_market_data_context(ticker: str, days_back: int = 30) -> dict:
    """
    Fetch comprehensive market data with technical indicators.
    """
    try:
        end = datetime.now()
        # 50-day SMA and 14-day ADX need about 65 trading days of history
        start = end - timedelta(days=days_back + 90)
        
        df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
        
        if df.empty:
            return {"error": f"No data available for {ticker}"}
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna(subset=['Close'])   # drop a partial bar for today
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']
        
        # RSI (14-day)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Moving Averages
        sma_20 = close.rolling(window=20).mean()
        sma_50 = close.rolling(window=50).mean()
        ema_20 = close.ewm(span=20, adjust=False).mean()
        
        # Bollinger Bands
        bb_std = close.rolling(window=20).std()
        bb_upper = sma_20 + (bb_std * 2)
        bb_lower = sma_20 - (bb_std * 2)
        
        # ATR (Average True Range)
        high_low = high - low
        high_close = (high - close.shift()).abs()
        low_close = (low - close.shift()).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=14).mean()
        
        # ADX (Average Directional Index)
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        atr_14 = true_range.rolling(window=14).mean()
        plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr_14)
        minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr_14)
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
        adx = dx.rolling(window=14).mean()
        
        latest_data = {
            "ticker": ticker,
            "current_price": float(close.iloc[-1]),
            "previous_close": float(close.iloc[-2]),
            "price_change_pct": float((close.iloc[-1] / close.iloc[-2] - 1) * 100),
            "recent_closes": [float(x) for x in close.tail(10).tolist()],
            "rsi_14": float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None,
            "sma_20": float(sma_20.iloc[-1]) if not pd.isna(sma_20.iloc[-1]) else None,
            "sma_50": float(sma_50.iloc[-1]) if not pd.isna(sma_50.iloc[-1]) else None,
            "ema_20": float(ema_20.iloc[-1]) if not pd.isna(ema_20.iloc[-1]) else None,
            "bb_upper": float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else None,
            "bb_lower": float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else None,
            "atr_14": float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else None,
            "adx_14": float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else None,
            "avg_volume_20d": float(volume.tail(20).mean()),
            "current_volume": float(volume.iloc[-1]),
            "volume_ratio": float(volume.iloc[-1] / volume.tail(20).mean()),
            "resistance_level": float(high.tail(20).max()),
            "support_level": float(low.tail(20).min()),
        }
        
        # Fetch SPY for market context
        try:
            spy = yf.download("SPY", start=start, end=end, progress=False, auto_adjust=True)
            if not spy.empty:
                if isinstance(spy.columns, pd.MultiIndex):
                    spy.columns = spy.columns.get_level_values(0)
                spy = spy.dropna(subset=['Close'])
                spy_change = (spy['Close'].iloc[-1] / spy['Close'].iloc[-2] - 1) * 100
                latest_data["spy_change_pct"] = float(spy_change)
        except:
            pass
        
        return latest_data
        
    except Exception as e:
        return {"error": str(e)}


def format_market_data_for_llm(market_data: dict) -> str:
    """
    Format market data into readable string for LLM.
    """
    if "error" in market_data:
        return f"Market data unavailable: {market_data['error']}"
    
    def money(v):
        return f"${v:.2f}" if v is not None else "N/A"

    def num(v):
        return f"{v:.2f}" if v is not None else "N/A"

    m = market_data
    text = f"""
REAL-TIME MARKET DATA FOR {m['ticker']}:

Current Price: ${m['current_price']:.2f} ({m['price_change_pct']:+.2f}% from previous close)

Last 10 Trading Days Closes: {', '.join([f'${x:.2f}' for x in m['recent_closes']])}

TECHNICAL INDICATORS:
- RSI (14-day): {num(m['rsi_14'])}
- SMA (20-day): {money(m['sma_20'])}
- SMA (50-day): {money(m['sma_50'])}
- EMA (20-day): {money(m['ema_20'])}
- Bollinger Bands: Upper {money(m['bb_upper'])}, Lower {money(m['bb_lower'])}

VOLATILITY & MOMENTUM:
- ATR (14-day): {money(m['atr_14'])}
- ADX (14-day): {num(m['adx_14'])} (trend strength)

VOLUME ANALYSIS:
- Current Volume: {m['current_volume']:,.0f}
- 20-day Avg Volume: {m['avg_volume_20d']:,.0f}
- Volume Ratio: {m['volume_ratio']:.2f}x average

KEY LEVELS:
- Resistance: ${m['resistance_level']:.2f}
- Support: ${m['support_level']:.2f}
"""
    
    if 'spy_change_pct' in market_data:
        text += f"\nMARKET CONTEXT:\n- SPY (S&P 500) today: {market_data['spy_change_pct']:+.2f}%"
    
    return text


def get_yfinance_price_series(ticker: str, days_back: int = 60):
    """Get historical price data for charting."""
    end = datetime.now()
    start = end - timedelta(days=days_back)
    df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
    if not df.empty and isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return None if df.empty else df