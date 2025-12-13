# ============================================================================
# FILE 5: data_manager.py
# Data persistence and loading
# ============================================================================

import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from config import RESULTS_FILE
from risk_management import apply_custom_risk_rules


def save_result(autohedge_result, capital_assumed: float = 100_000.0):
    """
    Save AutoHedge result with risk evaluation.
    """
    # Normalize to dict
    if isinstance(autohedge_result, dict):
        data = autohedge_result
    elif isinstance(autohedge_result, str):
        try:
            data = json.loads(autohedge_result)
        except:
            data = {"raw_output": autohedge_result}
    else:
        data = getattr(autohedge_result, "__dict__", {"result": autohedge_result})
    
    # Apply risk rules
    order = data.get("order")
    if isinstance(order, dict):
        risk_eval = apply_custom_risk_rules(order, capital=capital_assumed)
    else:
        risk_eval = {
            "approved": False,
            "reason": "No valid order.",
            "adjusted_order": None
        }
    
    # Add risk evaluation to data
    data["custom_risk_approved"] = risk_eval["approved"]
    data["custom_risk_reason"] = risk_eval["reason"]
    data["custom_risk_capital_assumed"] = capital_assumed
    data["custom_risk_order"] = risk_eval["adjusted_order"]
    
    # Extract order fields
    adj_order = risk_eval["adjusted_order"] or (order if isinstance(order, dict) else {})
    data["order_side"] = adj_order.get("side") or adj_order.get("action")
    data["order_quantity"] = adj_order.get("quantity") or adj_order.get("qty")
    data["order_entry_price"] = adj_order.get("entry_price") or adj_order.get("price")
    data["order_stop_loss"] = adj_order.get("stop_loss")
    data["order_take_profit"] = adj_order.get("take_profit")
    
    # Calculate notional
    if data.get("order_entry_price") and data.get("order_quantity"):
        try:
            data["order_notional"] = float(data["order_entry_price"]) * float(data["order_quantity"])
        except:
            data["order_notional"] = None
    
    # Add timestamp
    data["run_time"] = datetime.utcnow().isoformat()
    
    # Save to JSONL
    with open(RESULTS_FILE, "a") as f:
        f.write(json.dumps(data) + "\n")
    
    return data


def load_runs() -> pd.DataFrame:
    """
    Load all AutoHedge runs from JSONL file.
    """
    path = Path(RESULTS_FILE)
    if not path.exists():
        return pd.DataFrame()
    
    records = []
    with path.open() as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line))
                except:
                    pass
    
    if not records:
        return pd.DataFrame()
    
    df = pd.DataFrame(records)
    
    # Parse timestamps
    if "run_time" in df.columns:
        df["run_time"] = pd.to_datetime(df["run_time"], errors="coerce")
    
    # Flatten stocks list
    if "stocks" in df.columns:
        df["stocks_str"] = df["stocks"].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else str(x)
        )
    
    # Ensure order columns exist
    for col in ["order_side", "order_quantity", "order_entry_price", 
                "order_notional", "order_stop_loss", "order_take_profit"]:
        if col not in df.columns:
            df[col] = None
    
    return df