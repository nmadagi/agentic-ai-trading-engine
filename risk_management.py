# ============================================================================
# FILE 4: risk_management.py
# Custom risk rules and position sizing
# ============================================================================


def apply_custom_risk_rules(
    order: dict, 
    capital: float,
    max_position_pct: float = 0.1,
    min_trade_notional: float = 1000.0
) -> dict:
    """
    Apply custom risk management rules to orders.
    
    Args:
        order: Order dict from AI
        capital: Total capital available
        max_position_pct: Maximum position size as % of capital
        min_trade_notional: Minimum trade size in dollars
    
    Returns:
        Dict with approved status, adjusted order, and reason
    """
    if not order or not isinstance(order, dict):
        return {
            "approved": False,
            "adjusted_order": None,
            "reason": "No valid order provided."
        }
    
    side = str(order.get("side") or order.get("action") or "").upper()
    price = order.get("entry_price") or order.get("price")
    quantity = order.get("quantity") or order.get("qty")
    
    # Validate side
    if side not in {"BUY", "SELL", "LONG", "SHORT"}:
        return {
            "approved": False,
            "adjusted_order": None,
            "reason": f"Unsupported side '{side}'."
        }
    
    # Validate price
    if not price or price <= 0:
        return {
            "approved": False,
            "adjusted_order": None,
            "reason": "Missing or invalid price."
        }
    
    # Calculate maximum notional allowed
    max_notional = capital * max_position_pct
    
    # Calculate quantity if not provided
    if not quantity or quantity <= 0:
        quantity = max_notional / price
    
    notional = quantity * price
    
    # Check minimum notional
    if notional < min_trade_notional:
        return {
            "approved": False,
            "adjusted_order": None,
            "reason": f"Trade notional ${notional:.2f} below minimum ${min_trade_notional:.2f}."
        }
    
    # Cap at maximum position size
    if notional > max_notional:
        quantity = max_notional / price
        notional = quantity * price
    
    # Create adjusted order
    adjusted_order = dict(order)
    adjusted_order["side"] = side
    adjusted_order["quantity"] = quantity
    adjusted_order["notional"] = notional
    
    return {
        "approved": True,
        "adjusted_order": adjusted_order,
        "reason": f"Order approved. Capped at {max_position_pct*100:.1f}% of capital."
    }