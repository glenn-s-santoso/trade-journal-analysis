"""LLM Trading Analysis Module - Uses OpenRouter API to analyze trading performance.

Provides functions to analyze trading data using Large Language Models via OpenRouter.
"""
import json
import os
from typing import Any, Dict, List, Optional

from src.service.trading_analyzer import TradingAnalyzer


def get_llm_analysis(
    pnl_data: List[Dict[str, Any]],
    date: str,
    user_input: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Get LLM analysis of trading performance.

    Args:
        pnl_data: Raw PnL data from Bybit API
        date: Date string for the analysis
        user_input: User's input data with reflections

    Returns:
        Dictionary containing LLM analysis results
    """
    if pnl_data:
        analyzer = TradingAnalyzer()

        # Prepare trading data summary
        trading_summary = analyzer.prepare_trading_data_summary(pnl_data, user_input)

        # Get analysis
        analysis = analyzer.analyze_trading_data(trading_summary)

        # Print results
        print("\n===== LLM Trading Analysis =====\n")
        if "error" in analysis:
            print(f"Error: {analysis['error']}")
        else:
            print(json.dumps(analysis, indent=2))

        os.makedirs("output", exist_ok=True)
        os.makedirs(f"output/{date}/llm_analysis", exist_ok=True)

        # Save to file
        with open(f"output/{date}/llm_analysis/llm_analysis.json", "w") as f:
            json.dump(analysis, f, indent=2)
        print(f"\nAnalysis saved to output/{date}/llm_analysis/llm_analysis.json")
    else:
        print("No PnL data available for analysis.")

    return analysis
