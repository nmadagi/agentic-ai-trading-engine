"""
autohedge_agent.py
Core AI agent using Groq LLM for trade generation
"""

import json
from groq import Groq
from config import GROQ_API_KEY
from market_data import fetch_market_data_context, format_market_data_for_llm
from data_manager import save_result

groq_client = Groq(api_key=GROQ_API_KEY)


def run_autohedge(
    stocks,
    allocation_usd: float,
    strategy_type: str = "momentum",
    risk_level: int = 5,
    target_return_pct: float = 0.10,
    max_risk_pct: float = 0.02
):
    """
    Run AutoHedge AI analysis with real-time market data.
    
    Args:
        stocks: List of tickers or single ticker string
        allocation_usd: Capital allocation in USD
        strategy_type: Trading strategy (momentum, mean-reversion, etc.)
        risk_level: Risk level 1-10
        target_return_pct: Target return as decimal (0.10 = 10%)
        max_risk_pct: Maximum risk as decimal (0.02 = 2%)
    
    Returns:
        dict: Complete trade recommendation with thesis, analysis, and order
    """
    stock = stocks[0] if isinstance(stocks, list) and stocks else stocks
    
    # Fetch real-time market data
    market_data = fetch_market_data_context(stock, days_back=30)
    market_context = format_market_data_for_llm(market_data)
    
    task = (
        f"Analyze {stock} and provide a complete trading recommendation. "
        f"We have ${allocation_usd:,.0f} allocation with a {strategy_type} strategy "
        f"and risk level {risk_level}/10. "
        f"Target return: {target_return_pct*100:.1f}%, Maximum risk: {max_risk_pct*100:.1f}%. "
        "Act as a professional hedge fund trading desk."
    )
    
    system_prompt = """
You are an elite AI trading desk combining expertise from:
- Investment Director (strategic thesis)
- Quantitative Analyst (technical signals)
- Risk Manager (position sizing, stops)
- Execution Trader (precise entry/exit)

You MUST respond with valid JSON containing these exact keys:

{
  "thesis": "string - clear 2-3 sentence investment thesis",
  "quant_analysis": {
    "technical_score": float (0-1),
    "volume_score": float (0-1),
    "trend_strength": float (0-1),
    "volatility": float,
    "probability_score": float (0-1),
    "key_levels": {
      "support": float,
      "resistance": float,
      "pivot": float
    }
  },
  "risk_assessment": {
    "position_size": float,
    "max_drawdown_risk": float (0-1),
    "market_risk_exposure": float (0-1),
    "overall_risk_score": float (0-1)
  },
  "order": {
    "side": "buy" | "sell" | "flat",
    "quantity": int,
    "entry_price": float,
    "stop_loss": float,
    "take_profit": float,
    "target_return_pct": float,
    "max_risk_pct": float
  }
}

CRITICAL RULES:
1. Use the REAL-TIME MARKET DATA provided to make informed decisions
2. Set stop_loss and take_profit based on technical levels (support/resistance, ATR)
3. For LONG positions: stop_loss < entry_price < take_profit
4. For SHORT positions: take_profit < entry_price < stop_loss
5. If market conditions are unfavorable, set side="flat" and explain in thesis
6. target_return_pct should reflect distance from entry to take_profit
7. max_risk_pct should reflect distance from entry to stop_loss
8. ALWAYS fill every numeric field with reasonable values
9. Output ONLY valid JSON, no markdown, no explanations
"""
    
    user_content = f"""
Stock: {stock}
Allocation: ${allocation_usd:,.0f}
Strategy: {strategy_type}
Risk Level: {risk_level}/10
Target Return: {target_return_pct*100:.1f}%
Max Risk: {max_risk_pct*100:.1f}%

{market_context}

Task: {task}

Provide your complete analysis as a JSON object.
"""
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Add metadata
        result["stocks"] = [stock]
        result["current_stock"] = stock
        result["task"] = task
        result["market_data_snapshot"] = market_data
        result["strategy_type"] = strategy_type
        result["risk_level"] = risk_level
        
        # Save result with risk evaluation
        saved = save_result(result, capital_assumed=allocation_usd)
        return saved
        
    except Exception as e:
        error_result = {
            "error": str(e),
            "stocks": [stock],
            "current_stock": stock,
            "task": task,
            "thesis": f"Error generating analysis: {str(e)}",
            "quant_analysis": {},
            "risk_assessment": {},
            "order": {"side": "flat", "quantity": 0, "entry_price": 0}
        }
        return save_result(error_result, capital_assumed=allocation_usd)


def run_portfolio_analysis(tickers: list, allocation_usd: float, strategy_type: str = "hedged"):
    """
    Advanced: Analyze multiple tickers for portfolio construction.
    Generates hedged portfolio recommendations.
    """
    stock = ", ".join(tickers)
    
    # Fetch data for all tickers
    market_data_all = {}
    for ticker in tickers:
        market_data_all[ticker] = fetch_market_data_context(ticker, days_back=30)
    
    # Format for LLM
    market_context = "\n\n".join([
        f"=== {ticker} ===\n{format_market_data_for_llm(data)}"
        for ticker, data in market_data_all.items()
    ])
    
    task = (
        f"Analyze portfolio consisting of {stock}. "
        f"Total allocation: ${allocation_usd:,.0f}. "
        f"Strategy: {strategy_type}. "
        "Recommend a hedged portfolio with long/short positions to maximize returns while minimizing risk."
    )
    
    system_prompt = """
You are a portfolio manager. Analyze multiple assets and recommend:
1. Position sizing for each asset
2. Long/short allocation
3. Hedging strategy
4. Overall portfolio risk assessment

Respond with JSON:
{
  "thesis": "portfolio strategy explanation",
  "positions": [
    {"ticker": "string", "side": "buy/sell", "allocation_pct": float, "rationale": "string"}
  ],
  "portfolio_metrics": {
    "expected_return": float,
    "portfolio_beta": float,
    "diversification_score": float (0-1)
  },
  "risk_assessment": {
    "overall_risk_score": float (0-1),
    "hedge_ratio": float
  }
}
"""
    
    user_content = f"{market_context}\n\nTask: {task}"
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7,
            max_tokens=3000,
        )
        
        result = json.loads(response.choices[0].message.content)
        result["stocks"] = tickers
        result["task"] = task
        result["strategy_type"] = strategy_type
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "thesis": f"Error generating portfolio analysis: {str(e)}",
            "positions": [],
            "portfolio_metrics": {},
            "risk_assessment": {}
        }