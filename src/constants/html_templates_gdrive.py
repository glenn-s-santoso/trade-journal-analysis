"""
HTML template constants for report generation with Google Drive support
"""

REPORT_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Trading Performance Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1, h2, h3 {{
            color: #0066cc;
        }}
        .metric-box {{
            background-color: #f5f5f5;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        .metrics {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }}
        .metric {{
            flex: 1;
            min-width: 200px;
            padding: 15px;
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        .positive {{
            color: green;
        }}
        .negative {{
            color: red;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f8f8;
        }}
        tr:hover {{
            background-color: #f1f1f1;
        }}
        .chart-container {{
            margin: 30px 0;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
        .llm-analysis {{
            background-color: #f8f9fa;
            border-left: 5px solid #0066cc;
        }}
        .analysis-section {{
            margin-bottom: 20px;
            padding-left: 10px;
        }}
        .strengths {{
            border-left: 3px solid green;
        }}
        .improvements {{
            border-left: 3px solid #e74c3c;
        }}
        .recommendations {{
            border-left: 3px solid #f39c12;
            background-color: #fffbf0;
        }}
        .error-box {{
            border-left: 5px solid #e74c3c;
            background-color: #fdf7f7;
        }}
        .note {{
            font-size: 0.9em;
            color: #666;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Bybit Trading Performance Report</h1>
        <p>Period: {period_start} to {period_end}</p>
        <p>Report generated on: {generation_time}</p>
        
        <div class="metric-box">
            <h2>Overall Performance Summary</h2>
            <div class="metrics">
                <div class="metric">
                    <h3>Total PnL</h3>
                    <p class="{pnl_class}">{total_pnl:.2f} USDT</p>
                </div>
                <div class="metric">
                    <h3>Win Rate</h3>
                    <p>{win_rate:.2f}% ({winning_trades}/{total_trades})</p>
                </div>
                <div class="metric">
                    <h3>Win/Loss Count</h3>
                    <p>Win: {winning_trades}, Loss: {losing_trades}</p>
                </div>
                <div class="metric">
                    <h3>Avg Win/Loss</h3>
                    <p>{avg_win:.2f}/{avg_loss_abs:.2f} USDT</p>
                </div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>Cumulative PnL Over Time</h2>
            <img src="{cumulative_pnl_url}" alt="Cumulative PnL Chart">
        </div>
        
        <div class="chart-container">
            <h2>Daily PnL</h2>
            <img src="{daily_pnl_url}" alt="Daily PnL Chart">
        </div>
        
        <h2>Symbol Performance</h2>
        <table>
            <tr>
                <th>Symbol</th>
                <th>Win Rate</th>
                <th>Avg PnL</th>
                <th>Total PnL</th>
                <th>Total Trades</th>
            </tr>
            {symbol_stats_rows}
        </table>
        
        <div class="chart-container">
            <h2>PnL Distribution</h2>
            <img src="{pnl_distribution_url}" alt="PnL Distribution">
        </div>
        
        <div class="chart-container">
            <h2>Trade Duration Distribution</h2>
            <img src="{duration_distribution_url}" alt="Duration Distribution">
        </div>
        
        <div class="chart-container">
            <h2>Hourly Performance Heatmap</h2>
            <img src="{hourly_heatmap_url}" alt="Hourly Heatmap">
        </div>
        
        <h2>Recommendations</h2>
        <div class="metric-box">
            <ul>
                {recommendation_items}
            </ul>
        </div>
        
        {user_sections}
    </div>
</body>
</html>
"""

SYMBOL_STATS_ROW_TEMPLATE = """
            <tr>
                <td>{symbol}</td>
                <td>{win_rate:.2f}%</td>
                <td class="{avg_pnl_class}">{avg_pnl:.2f}</td>
                <td class="{total_pnl_class}">{total_pnl:.2f}</td>
                <td>{trade_count}</td>
            </tr>
"""

USER_REFLECTION_TEMPLATE = """
        <div class="metric-box">
            <h2>Personal Reflection</h2>
            <p style="white-space: pre-line;">{reflection_text}</p>
        </div>
"""

STRATEGY_SECTION_TEMPLATE = """
        <div class="metric-box">
            <h2>Trading Strategy</h2>
            <ul>
                {strategy_items}
            </ul>
        </div>
"""

PSYCHOLOGY_SECTION_TEMPLATE = """
        <div class="metric-box">
            <h2>Trading Psychology Issues</h2>
            <ul>
                {psychology_items}
            </ul>
        </div>
"""

IMPROVEMENTS_SECTION_TEMPLATE = """
        <div class="metric-box">
            <h2>Improvement Goals</h2>
            <ul>
                {improvement_items}
            </ul>
        </div>
"""

RR_SECTION_TEMPLATE = """
    <div class="metric-box">
        <h2>Risk-Reward Analysis</h2>
        <div class="metrics">
            <div class="metric">
                <h3>Average Win</h3>
                <p>{avg_win_r:.1f}R (${avg_win_usd:.2f})</p>
            </div>
            <div class="metric">
                <h3>Average Loss</h3>
                <p>{avg_loss_r:.1f}R (${avg_loss_usd:.2f})</p>
            </div>
            <div class="metric">
                <h3>Biggest Win</h3>
                <p>{biggest_win_r:.1f}R (${biggest_win_usd:.2f})</p>
            </div>
            <div class="metric">
                <h3>Stop Loss Stats</h3>
                <p>Full stops: {full_stops}, Partial stops: {partial_stops}</p>
            </div>
        </div>
        <p class="note">Note: Full stops are losses within 5% of your standard risk (${standard_risk:.2f}).</p>
    </div>
"""
