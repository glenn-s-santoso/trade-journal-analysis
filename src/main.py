"""Generate a comprehensive trading report with LLM analysis"""
import os
from datetime import datetime
from src.constants.user_input import (
    THIS_WEEK_STRATEGY, OVERTRADING, RISK_MANAGEMENT, 
    IMPROVEMENT_GOALS, PERSONAL_REFLECTION
)
from src.constants.env import OPENROUTER_API_KEY
from src.util import get_closed_pnl, get_llm_analysis, generate_html_report


def main():
    """Generate a comprehensive trading report with LLM analysis"""
    print("Fetching closed PnL data from Bybit...")
    pnl_data = get_closed_pnl()
    
    if not pnl_data:
        print("No closed PnL data found for the specified period.")
        return
    
    print(f"Found {len(pnl_data)} closed trades.")
    
    # Get user input data if available
    try:
        
        user_data = {
            "strategy": THIS_WEEK_STRATEGY,
            "psychology": OVERTRADING,
            "RISK_MANAGEMENT": RISK_MANAGEMENT,
            "reflection": PERSONAL_REFLECTION,
            "improvements": IMPROVEMENT_GOALS
        }
        has_user_input = True
    except ImportError:
        user_data = {}
        has_user_input = False
    
    date = datetime.now().strftime('%Y%m%d_%H%M%S')
    # Check if OpenRouter API key is available
    if not OPENROUTER_API_KEY:
        print("Warning: OpenRouter API key not found. LLM analysis will be skipped.")
        print("Please set OPENROUTER_API_KEY in your .env file.")
        print("Generating report without LLM analysis...")
        
        # Generate report without LLM analysis
        if has_user_input:
            generate_html_report(pnl_data, date=date, user_data=user_data)
        else:
            generate_html_report(pnl_data, date=date)
        return
    
    print("Getting LLM analysis of your trading performance...")
    llm_analysis = get_llm_analysis(pnl_data, date, user_data if has_user_input else None)
    
    if "error" in llm_analysis:
        print(f"Error getting LLM analysis: {llm_analysis['error']}")
        print("Generating report without LLM analysis...")
        
        # Generate report without LLM analysis
        if has_user_input:
            generate_html_report(pnl_data, date=date, user_data=user_data)
        else:
            generate_html_report(pnl_data, date=date)
        return
    
    print("LLM analysis complete. Generating enhanced report...")
    
    # Add LLM analysis to user data
    if has_user_input:
        user_data["llm_analysis"] = llm_analysis
    else:
        user_data = {"llm_analysis": llm_analysis}
    
    # Create output directory if it doesn't exist
    output_dir = "output"
    if not os.path.exists(f"{output_dir}/{date}"):
        os.makedirs(f"{output_dir}/{date}")
        print(f"Created output directory: {output_dir}/{date}")
    
    # Generate report with LLM analysis
    output_file = f"{output_dir}/{date}/trading_report.html"
    generate_html_report(pnl_data, output_file=output_file, date=date, user_data=user_data)
    
    print(f"HTML report generated: {output_file}")

if __name__ == "__main__":
    main()
