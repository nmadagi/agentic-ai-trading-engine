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
        start = end - timedelta(days=days_back + 20)
        
        df = yf.download(ticker, start=start, end=end, progress=False)
        
        if df.empty:
            return {"error": f"No data available for {ticker}"}
        
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
        dx = (abs(plus_di - minus_di) / (plus_pi + minus_di)) * 100
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
            spy = yf.download("SPY", start=start, end=end, progress=False)
            if not spy.empty:
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
    
    text = f"""
REAL-TIME MARKET DATA FOR {market_data['ticker']}:

Current Price: ${market_data['current_price']:.2f} ({market_data['price_change_pct']:+.2f}% from previous close)

Last 10 Trading Days Closes: {', '.join([f'${x:.2f}' for x in market_data['recent_closes']])}

TECHNICAL INDICATORS:
- RSI (14-day): {market_data['rsi_14']:.2f if market_data['rsi_14'] else 'N/A'}
- SMA (20-day): ${market_data['sma_20']:.2f if market_data['sma_20'] else 'N/A'}
- SMA (50-day): ${market_data['sma_50']:.2f if market_data['sma_50'] else 'N/A'}
- EMA (20-day): ${market_data['ema_20']:.2f if market_data['ema_20'] else 'N/A'}
- Bollinger Bands: Upper ${market_data['bb_upper']:.2f if market_data['bb_upper'] else 'N/A'}, Lower ${market_data['bb_lower']:.2f if market_data['bb_lower'] else 'N/A'}

VOLATILITY & MOMENTUM:
- ATR (14-day): ${market_data['atr_14']:.2f if market_data['atr_14'] else 'N/A'}
- ADX (14-day): {market_data['adx_14']:.2f if market_data['adx_14'] else 'N/A'} (trend strength)

VOLUME ANALYSIS:
- Current Volume: {market_data['current_volume']:,.0f}
- 20-day Avg Volume: {market_data['avg_volume_20d']:,.0f}
- Volume Ratio: {market_data['volume_ratio']:.2f}x average

KEY LEVELS:
- Resistance: ${market_data['resistance_level']:.2f}
- Support: ${market_data['support_level']:.2f}
"""
    
    if 'spy_change_pct' in market_data:
        text += f"\nMARKET CONTEXT:\n- SPY (S&P 500) today: {market_data['spy_change_pct']:+.2f}%"
    
    return text


def get_yfinance_price_series(ticker: str, days_back: int = 60):
    """Get historical price data for charting."""
    end = datetime.now()
    start = end - timedelta(days=days_back)
    df = yf.download(ticker, start=start, end=end, progress=False)
    return None if df.empty else df