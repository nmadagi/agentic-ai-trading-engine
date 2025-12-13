# ============================================================================
# FILE 3: alpaca_trading.py
# Alpaca paper trading integration
# ============================================================================

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from config import APCA_API_KEY_ID, APCA_API_SECRET_KEY


def get_alpaca_client() -> TradingClient | None:
    """Initialize Alpaca trading client."""
    if not APCA_API_KEY_ID or not APCA_API_SECRET_KEY:
        return None
    return TradingClient(APCA_API_KEY_ID, APCA_API_SECRET_KEY, paper=True)


def alpaca_place_market_order(symbol: str, side: str, qty: float):
    """Place a market order via Alpaca."""
    client = get_alpaca_client()
    if client is None:
        raise RuntimeError("Alpaca API keys not set.")
    
    side_enum = OrderSide.BUY if side.upper() in ["BUY", "LONG"] else OrderSide.SELL
    order_req = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=side_enum,
        time_in_force=TimeInForce.DAY
    )
    return client.submit_order(order_req)


def alpaca_get_positions():
    """Get all open positions."""
    client = get_alpaca_client()
    return [] if client is None else client.get_all_positions()


def alpaca_get_account():
    """Get account information."""
    client = get_alpaca_client()
    return None if client is None else client.get_account()