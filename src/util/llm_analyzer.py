"""
LLM Trading Analysis Module - Uses OpenRouter API to analyze trading performance
"""
import os
from typing import Optional
from src.service.trading_analyzer import TradingAnalyzer
import json

def get_llm_analysis(pnl_data: list[dict[str, any]], date: str, user_input: Optional[dict[str, any]] = None):
    """
    Get LLM analysis of trading performance
    
    Args:
        pnl_data (list): Raw PnL data from Bybit API
        user_input (dict, optional): User's input data with reflections
    
    Returns:
        dict: LLM analysis results
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
            
        os.makedirs('output', exist_ok=True)
        os.makedirs(f'output/{date}/llm_analysis', exist_ok=True)
        
        # Save to file
        with open(f"output/{date}/llm_analysis/llm_analysis.json", "w") as f:
            json.dump(analysis, f, indent=2)
        print(f"\nAnalysis saved to output/{date}/llm_analysis/llm_analysis.json")
    else:
        print("No PnL data available for analysis.")
    
    return analysis
