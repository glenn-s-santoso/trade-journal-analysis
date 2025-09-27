"""
Generate a detailed trading performance report from the Bybit closed PnL data
"""
import os
from typing import Dict, List, Optional, Any
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import seaborn as sns

from src.util.llm_report_section import create_llm_analysis_section
from src.constants.html_templates import (
    REPORT_HTML_TEMPLATE, SYMBOL_STATS_ROW_TEMPLATE, USER_REFLECTION_TEMPLATE,
    STRATEGY_SECTION_TEMPLATE, PSYCHOLOGY_SECTION_TEMPLATE, IMPROVEMENTS_SECTION_TEMPLATE, RR_SECTION_TEMPLATE
)

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = [12, 8]
plt.rcParams['font.size'] = 12

def generate_html_report(pnl_data: List[Dict[str, Any]], output_file: str = "trading_report.html", user_data: Optional[Dict[str, any]] = None):
    """Generate an HTML report with trading performance analysis"""
    
    if not pnl_data:
        print("No data available to generate report")
        return
        
    # Convert to DataFrame
    df = pd.DataFrame(pnl_data)
    
    # Convert string values to appropriate types
    df['closedPnl'] = df['closedPnl'].astype(float)
    
    # Fix FutureWarning by explicitly converting to numeric before to_datetime
    df['createdTime'] = pd.to_datetime(pd.to_numeric(df['createdTime']), unit='ms')
    df['updatedTime'] = pd.to_datetime(pd.to_numeric(df['updatedTime']), unit='ms')
    
    try:
        df['avgEntryPrice'] = df['avgEntryPrice'].astype(float)
        df['avgExitPrice'] = df['avgExitPrice'].astype(float)
        df['qty'] = df['qty'].astype(float)
        df['closedSize'] = df['closedSize'].astype(float)
        df['cumEntryValue'] = df['cumEntryValue'].astype(float)
        df['cumExitValue'] = df['cumExitValue'].astype(float)
        df['leverage'] = df['leverage'].astype(float)
    except (KeyError, ValueError) as e:
        print(f"Warning: Some fields could not be converted: {e}")
    
    # Additional columns for analysis
    df['duration_seconds'] = (df['updatedTime'] - df['createdTime']).dt.total_seconds()
    df['duration_hours'] = df['duration_seconds'] / 3600
    df['date'] = df['createdTime'].dt.date
    df['hour_of_day'] = df['createdTime'].dt.hour
    df['profit_flag'] = df['closedPnl'] > 0
    df['cumulative_pnl'] = df['closedPnl'].cumsum()
    
    # Create plots in a temp directory
    os.makedirs('output/report_plots', exist_ok=True)
    
    # 1. Cumulative PnL Chart
    plt.figure()
    plt.plot(df['createdTime'], df['cumulative_pnl'], linewidth=2)
    plt.title('Cumulative PnL Over Time')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('output/report_plots/cumulative_pnl.png')
    plt.close()
    
    # 2. Daily PnL Chart
    daily_pnl = df.groupby('date')['closedPnl'].sum()
    plt.figure()
    daily_pnl.plot(kind='bar', color=[('green' if x > 0 else 'red') for x in daily_pnl])
    plt.title('Daily PnL')
    plt.grid(axis='y')
    plt.tight_layout()
    plt.savefig('output/report_plots/daily_pnl.png')
    plt.close()
    
    # 3. Win/Loss Distribution
    plt.figure()
    plt.hist(df['closedPnl'], bins=20, alpha=0.7, color='blue', edgecolor='black')
    plt.axvline(x=0, color='red', linestyle='--')
    plt.title('PnL Distribution')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('output/report_plots/pnl_distribution.png')
    plt.close()
    
    # 4. Trade Duration Analysis
    plt.figure()
    plt.hist(df['duration_hours'], bins=20, alpha=0.7, color='purple', edgecolor='black')
    plt.title('Trade Duration Distribution (hours)')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('output/report_plots/duration_distribution.png')
    plt.close()
    
    # 5. Win Rate by Symbol
    symbol_stats = {}
    for symbol in df['symbol'].unique():
        symbol_df = df[df['symbol'] == symbol]
        wins = (symbol_df['closedPnl'] > 0).sum()
        total = len(symbol_df)
        win_rate = wins / total if total > 0 else 0
        avg_pnl = symbol_df['closedPnl'].mean()
        symbol_stats[symbol] = {
            'win_rate': win_rate * 100,
            'avg_pnl': avg_pnl,
            'total_trades': total,
            'total_pnl': symbol_df['closedPnl'].sum()
        }
    
    # Convert to DataFrame for the HTML report
    symbol_stats_df = pd.DataFrame.from_dict(symbol_stats, orient='index')
    
    # 6. Hourly Performance Heatmap
    hourly_performance = df.groupby('hour_of_day')['closedPnl'].agg(['mean', 'sum', 'count']).reset_index()
    plt.figure()
    sns.heatmap(hourly_performance.pivot_table(index='hour_of_day', values='mean'), cmap='RdYlGn', annot=True)
    plt.title('Average PnL by Hour of Day')
    plt.tight_layout()
    plt.savefig('output/report_plots/hourly_heatmap.png')
    plt.close()
    
    # Calculate overall performance metrics
    total_pnl = df['closedPnl'].sum()
    win_rate = (df['closedPnl'] > 0).mean() * 100
    total_trades = len(df)
    winning_trades = (df['closedPnl'] > 0).sum()
    losing_trades = (df['closedPnl'] < 0).sum()
    
    avg_win = df.loc[df['closedPnl'] > 0, 'closedPnl'].mean() if len(df[df['closedPnl'] > 0]) > 0 else 0
    avg_loss = df.loc[df['closedPnl'] < 0, 'closedPnl'].mean() if len(df[df['closedPnl'] < 0]) > 0 else 0
    
    # Prepare template parameters
    template_params = {
        'period_start': df['createdTime'].min().strftime('%Y-%m-%d'),
        'period_end': df['createdTime'].max().strftime('%Y-%m-%d'),
        'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'total_pnl': total_pnl,
        'pnl_class': 'positive' if total_pnl > 0 else 'negative',
        'win_rate': win_rate,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'total_trades': total_trades,
        'avg_win': avg_win,
        'avg_loss_abs': abs(avg_loss)
    }
    
    # Generate symbol stats rows
    symbol_stats_rows = ""
    for symbol, stats in sorted(symbol_stats.items(), key=lambda x: x[1]['total_pnl'], reverse=True):
        symbol_stats_rows += SYMBOL_STATS_ROW_TEMPLATE.format(
            symbol=symbol,
            win_rate=stats['win_rate'],
            avg_pnl=stats['avg_pnl'],
            avg_pnl_class='positive' if stats['avg_pnl'] > 0 else 'negative',
            total_pnl=stats['total_pnl'],
            total_pnl_class='positive' if stats['total_pnl'] > 0 else 'negative',
            trade_count=stats['total_trades']
        )
    template_params['symbol_stats_rows'] = symbol_stats_rows
    
    # Generate recommendations
    recommendation_items = ""
    
    # Add dynamic recommendations based on data
    if win_rate < 50:
        recommendation_items += "<li>Your win rate is below 50%. Consider reviewing your entry and exit criteria.</li>"
    
    # Find best performing symbols
    best_symbol = symbol_stats_df['total_pnl'].idxmax() if not symbol_stats_df.empty else "None"
    if best_symbol != "None":
        recommendation_items += f"<li>Your best performing symbol is {best_symbol}. Consider focusing more on this market.</li>"
    
    # Find best time of day
    if not hourly_performance.empty:
        best_hour = hourly_performance.loc[hourly_performance['mean'].idxmax(), 'hour_of_day']
        recommendation_items += f"<li>Your most profitable hour appears to be {best_hour}:00. Consider trading more during this time.</li>"
    
    # Check if holding time for winning trades differs significantly from losing trades
    avg_win_duration = df.loc[df['closedPnl'] > 0, 'duration_hours'].mean() if len(df[df['closedPnl'] > 0]) > 0 else 0
    avg_loss_duration = df.loc[df['closedPnl'] < 0, 'duration_hours'].mean() if len(df[df['closedPnl'] < 0]) > 0 else 0
    
    if avg_win_duration > avg_loss_duration * 1.5:
        recommendation_items += "<li>Your winning trades last significantly longer than your losing trades. Consider letting your profitable trades run longer.</li>"
    elif avg_loss_duration > avg_win_duration * 1.5:
        recommendation_items += "<li>Your losing trades last significantly longer than your winning trades. Consider cutting losses earlier.</li>"
        
    template_params['recommendation_items'] = recommendation_items
    
    # Handle user sections
    user_sections = ""
    if user_data:
        # Add strategy section
        user_sections += _create_strategy_section(user_data.get("strategy"))
        
        # Add psychology section
        user_sections += _create_psychology_section(user_data.get("psychology"))
        
        # Add R-multiple analysis section if available
        standard_risk = user_data.get("RISK_MANAGEMENT", {}).get("standard_risk_per_trade", 9)
        # Pass both the user input data AND the actual trade data to auto-calculate R values
        user_sections += _create_rr_section(standard_risk, df=df)
        
        # Add improvement goals
        user_sections += _create_improvements_section(user_data.get("improvements"))
        
        # Add personal reflection
        if user_data.get("reflection"):
            user_sections += USER_REFLECTION_TEMPLATE.format(
                reflection_text=user_data.get("reflection")
            )
        
        # Add LLM analysis if available
        if user_data.get("llm_analysis"):
            user_sections += create_llm_analysis_section(user_data.get("llm_analysis"))
            
    template_params['user_sections'] = user_sections
    
    # Generate final HTML using the template
    html_content = REPORT_HTML_TEMPLATE.format(**template_params)
    
    # Write HTML to file
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"HTML report generated: {output_file}")
    print("Report plots saved in the 'report_plots' directory")

def _analyze_stop_loss_data(df, standard_risk=9.0):
    """Analyze trade data to determine full vs partial stop losses"""
    # Get losing trades
    losing_trades = df[df['closedPnl'] < 0]
    
    # Consider a full stop as a loss within 5% of the standard risk (to account for small variations)
    full_stop_threshold = 0.05  # 5% tolerance
    full_stop_min = standard_risk * (1 - full_stop_threshold)
    full_stop_max = standard_risk * (1 + full_stop_threshold)
    
    # Count full stops (losses close to standard_risk)
    full_stops = losing_trades[
        (abs(losing_trades['closedPnl']) >= full_stop_min) & 
        (abs(losing_trades['closedPnl']) <= full_stop_max)
    ].shape[0]
    
    # Count partial stops (all other losses)
    partial_stops = losing_trades.shape[0] - full_stops
    
    return full_stops, partial_stops

def _create_rr_section(standard_risk, df=None):
    """Create HTML content for risk-reward analysis section"""
    if df is None:
        return ""
        
    # Calculate average win and loss in R multiples
    avg_win_usd = df.loc[df['closedPnl'] > 0, 'closedPnl'].mean() if len(df[df['closedPnl'] > 0]) > 0 else 0
    avg_loss_usd = abs(df.loc[df['closedPnl'] < 0, 'closedPnl'].mean()) if len(df[df['closedPnl'] < 0]) > 0 else 0
    biggest_win_usd = df.loc[df['closedPnl'] > 0, 'closedPnl'].max() if len(df[df['closedPnl'] > 0]) > 0 else 0
    
    # Convert to R multiples
    avg_win_r = avg_win_usd / standard_risk if standard_risk > 0 else 0
    avg_loss_r = avg_loss_usd / standard_risk if standard_risk > 0 else 0
    biggest_win_r = biggest_win_usd / standard_risk if standard_risk > 0 else 0
    
    # Analyze stop loss data
    full_stops, partial_stops = _analyze_stop_loss_data(df, standard_risk)
    
    return RR_SECTION_TEMPLATE.format(
        avg_win_r=avg_win_r,
        avg_win_usd=avg_win_usd,
        avg_loss_r=avg_loss_r,
        avg_loss_usd=avg_loss_usd,
        biggest_win_r=biggest_win_r,
        biggest_win_usd=biggest_win_usd,
        full_stops=full_stops,
        partial_stops=partial_stops,
        standard_risk=standard_risk
    )

def _create_strategy_section(strategy_list):
    """Create HTML content for strategy section"""
    if not strategy_list:
        return ""
    
    strategy_items = ""
    for item in strategy_list:
        strategy_items += f"<li>{item}</li>"
    
    return STRATEGY_SECTION_TEMPLATE.format(strategy_items=strategy_items)

def _create_psychology_section(issues_list):
    """Create HTML content for psychology section"""
    if not issues_list:
        return ""
    
    psychology_items = ""
    for item in issues_list:
        psychology_items += f"<li>{item}</li>"
    
    return PSYCHOLOGY_SECTION_TEMPLATE.format(psychology_items=psychology_items)

def _create_improvements_section(goals_list):
    """Create HTML content for improvements section"""
    if not goals_list:
        return ""
    
    improvement_items = ""
    for item in goals_list:
        improvement_items += f"<li>{item}</li>"
    
    return IMPROVEMENTS_SECTION_TEMPLATE.format(improvement_items=improvement_items)
