"""Generate a detailed trading performance report from the Bybit closed PnL data.

Creates HTML reports with trading metrics, charts, and analysis.
"""
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.constants.html_templates import (
    IMPROVEMENTS_SECTION_TEMPLATE,
    PSYCHOLOGY_SECTION_TEMPLATE,
    REPORT_HTML_TEMPLATE,
    RR_SECTION_TEMPLATE,
    STRATEGY_SECTION_TEMPLATE,
    SYMBOL_STATS_ROW_TEMPLATE,
    USER_REFLECTION_TEMPLATE,
)
from src.util.llm_report_section import create_llm_analysis_section

sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = [12, 8]
plt.rcParams["font.size"] = 12


def generate_html_report(
    pnl_data: List[Dict[str, Any]],
    output_file: str = "trading_report.html",
    date: str = "",
    user_data: Optional[Dict[str, Any]] = None,
) -> None:
    """Generate an HTML report with trading performance analysis.

    Args:
        pnl_data: List of PnL data dictionaries from Bybit API
        output_file: Path where HTML report will be saved
        date: Date string for report identification
        user_data: Optional dictionary containing user input data
    """
    if not pnl_data:
        print("No data available to generate report")
        return

    print("Processing closed PnL data...")

    # Convert to DataFrame
    df = pd.DataFrame(pnl_data)

    # Convert string values to appropriate types
    df["closedPnl"] = df["closedPnl"].astype(float)

    # Fix FutureWarning by explicitly converting to numeric before to_datetime
    df["createdTime"] = pd.to_datetime(pd.to_numeric(df["createdTime"]), unit="ms")
    df["updatedTime"] = pd.to_datetime(pd.to_numeric(df["updatedTime"]), unit="ms")

    # Convert timestamps from UTC to UTC+7 (Southeast Asia timezone)
    df["createdTime"] = (
        df["createdTime"].dt.tz_localize("UTC").dt.tz_convert("Asia/Bangkok")
    )
    df["updatedTime"] = (
        df["updatedTime"].dt.tz_localize("UTC").dt.tz_convert("Asia/Bangkok")
    )

    try:
        df["avgEntryPrice"] = df["avgEntryPrice"].astype(float)
        df["avgExitPrice"] = df["avgExitPrice"].astype(float)
        df["qty"] = df["qty"].astype(float)
        df["closedSize"] = df["closedSize"].astype(float)
        df["cumEntryValue"] = df["cumEntryValue"].astype(float)
        df["cumExitValue"] = df["cumExitValue"].astype(float)
        df["leverage"] = df["leverage"].astype(float)
    except (KeyError, ValueError) as e:
        print(f"Warning: Some fields could not be converted: {e}")

    # Additional columns for analysis
    df["duration_seconds"] = (df["updatedTime"] - df["createdTime"]).dt.total_seconds()
    df["duration_hours"] = df["duration_seconds"] / 3600
    df["date"] = df["createdTime"].dt.date
    df["hour_of_day"] = df["createdTime"].dt.hour
    df["profit_flag"] = df["closedPnl"] > 0
    df["cumulative_pnl"] = df["closedPnl"].cumsum()

    global report_plots_folder

    if output_file and output_file != "trading_report.html":
        output_dir = os.path.dirname(output_file)
        report_plots_folder = os.path.join(output_dir, "report_plots")
    else:
        report_plots_folder = f"output/{date}/report_plots"

    print(f"Saving plots to: {report_plots_folder}")
    os.makedirs(report_plots_folder, exist_ok=True)

    report_plots_folder += "/{filename}.png"

    _make_cumulative_pnl_plot(df)

    _make_daily_pnl_plot(df)

    _make_pnl_distribution_plot(df)

    _make_duration_distribution_plot(df)
    # 5. Win Rate by Symbol
    symbol_stats = {}
    for symbol in df["symbol"].unique():
        symbol_df = df[df["symbol"] == symbol]
        wins = (symbol_df["closedPnl"] > 0).sum()
        total = len(symbol_df)
        win_rate = wins / total if total > 0 else 0
        avg_pnl = symbol_df["closedPnl"].mean()
        symbol_stats[symbol] = {
            "win_rate": win_rate * 100,
            "avg_pnl": avg_pnl,
            "total_trades": total,
            "total_pnl": symbol_df["closedPnl"].sum(),
        }

    # Convert to DataFrame for the HTML report
    symbol_stats_df = pd.DataFrame.from_dict(symbol_stats, orient="index")

    hourly_performance = _make_hourly_heatmap(df)

    # Calculate overall performance metrics
    total_pnl = df["closedPnl"].sum()
    win_rate = (df["closedPnl"] > 0).mean() * 100
    total_trades = len(df)
    winning_trades = (df["closedPnl"] > 0).sum()
    losing_trades = (df["closedPnl"] < 0).sum()

    avg_win = (
        df.loc[df["closedPnl"] > 0, "closedPnl"].mean()
        if len(df[df["closedPnl"] > 0]) > 0
        else 0
    )
    avg_loss = (
        df.loc[df["closedPnl"] < 0, "closedPnl"].mean()
        if len(df[df["closedPnl"] < 0]) > 0
        else 0
    )

    # Prepare template parameters
    template_params = {
        "period_start": df["createdTime"].min().strftime("%Y-%m-%d"),
        "period_end": df["createdTime"].max().strftime("%Y-%m-%d"),
        "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_pnl": total_pnl,
        "pnl_class": "positive" if total_pnl > 0 else "negative",
        "win_rate": win_rate,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "total_trades": total_trades,
        "avg_win": avg_win,
        "avg_loss_abs": abs(avg_loss),
    }

    # Generate symbol stats rows
    symbol_stats_rows = ""
    for symbol, stats in sorted(
        symbol_stats.items(), key=lambda x: x[1]["total_pnl"], reverse=True
    ):
        symbol_stats_rows += SYMBOL_STATS_ROW_TEMPLATE.format(
            symbol=symbol,
            win_rate=stats["win_rate"],
            avg_pnl=stats["avg_pnl"],
            avg_pnl_class="positive" if stats["avg_pnl"] > 0 else "negative",
            total_pnl=stats["total_pnl"],
            total_pnl_class="positive" if stats["total_pnl"] > 0 else "negative",
            trade_count=stats["total_trades"],
        )
    template_params["symbol_stats_rows"] = symbol_stats_rows

    # Generate recommendations
    recommendation_items = ""

    # Add dynamic recommendations based on data
    if win_rate < 50:
        recommendation_items += (
            "<li>Your win rate is below 50%. ",
            "Consider reviewing your entry and exit criteria.</li>",
        )

    # Find best performing symbols
    best_symbol = (
        symbol_stats_df["total_pnl"].idxmax() if not symbol_stats_df.empty else "None"
    )
    if best_symbol != "None":
        recommendation_items += (
            "<li>Your best performing symbol is ",
            best_symbol,
            ". Consider focusing more on this market.</li>",
        )

    # Find best time of day
    if not hourly_performance.empty:
        best_hour = hourly_performance.loc[
            hourly_performance["mean"].idxmax(), "hour_of_day"
        ]
        recommendation_items += (
            "<li>Your most profitable hour appears to be ",
            best_hour,
            ":00. Consider trading more during this time.</li>",
        )

    # Check if holding time for winning trades differs significantly from losing trades
    avg_win_duration = (
        df.loc[df["closedPnl"] > 0, "duration_hours"].mean()
        if len(df[df["closedPnl"] > 0]) > 0
        else 0
    )
    avg_loss_duration = (
        df.loc[df["closedPnl"] < 0, "duration_hours"].mean()
        if len(df[df["closedPnl"] < 0]) > 0
        else 0
    )

    if avg_win_duration > avg_loss_duration * 1.5:
        recommendation_items += (
            "<li>Your winning trades last significantly longer than your losing trades. ",
            "Consider letting your profitable trades run longer.</li>",
        )
    elif avg_loss_duration > avg_win_duration * 1.5:
        recommendation_items += (
            "<li>Your losing trades last significantly longer than your winning trades. ",
            "Consider cutting losses earlier.</li>",
        )

    template_params["recommendation_items"] = recommendation_items

    # Handle user sections
    user_sections = ""
    if user_data:
        # Add strategy section
        user_sections += _create_strategy_section(user_data.get("strategy"))

        # Add psychology section
        user_sections += _create_psychology_section(user_data.get("psychology"))

        # Add R-multiple analysis section if available
        standard_risk = user_data.get("RISK_MANAGEMENT", {}).get(
            "standard_risk_per_trade", 9
        )
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

    template_params["user_sections"] = user_sections
    # Generate final HTML using the template
    html_content = REPORT_HTML_TEMPLATE.format(**template_params)

    # Write HTML to file
    with open(f"{output_file}", "w") as f:
        f.write(html_content)

    print(f"Report plots saved in the 'output/{date}/report_plots' directory")


def _analyze_stop_loss_data(
    df: pd.DataFrame, standard_risk: float = 9.0
) -> Tuple[int, int]:
    """Analyze trade data to determine full vs partial stop losses.

    Args:
        df: DataFrame with trading data
        standard_risk: Standard risk amount per trade in USD

    Returns:
        Tuple containing count of full stops and partial stops
    """
    # Get losing trades
    losing_trades = df[df["closedPnl"] < 0]

    # Consider a full stop as a loss within 5% of the standard risk (to account for small variations)
    full_stop_threshold = 0.05  # 5% tolerance
    full_stop_min = standard_risk * (1 - full_stop_threshold)
    full_stop_max = standard_risk * (1 + full_stop_threshold)

    # Count full stops (losses close to standard_risk)
    full_stops = losing_trades[
        (abs(losing_trades["closedPnl"]) >= full_stop_min)
        & (abs(losing_trades["closedPnl"]) <= full_stop_max)
    ].shape[0]

    # Count partial stops (all other losses)
    partial_stops = losing_trades.shape[0] - full_stops

    return full_stops, partial_stops


def _create_rr_section(standard_risk: float, df: Optional[pd.DataFrame] = None) -> str:
    """Create HTML content for risk-reward analysis section.

    Args:
        standard_risk: Standard risk amount per trade in USD
        df: DataFrame containing trade data

    Returns:
        HTML string for risk-reward analysis section
    """
    if df is None:
        return ""

    # Calculate average win and loss in R multiples
    avg_win_usd = (
        df.loc[df["closedPnl"] > 0, "closedPnl"].mean()
        if len(df[df["closedPnl"] > 0]) > 0
        else 0
    )
    avg_loss_usd = (
        abs(df.loc[df["closedPnl"] < 0, "closedPnl"].mean())
        if len(df[df["closedPnl"] < 0]) > 0
        else 0
    )
    biggest_win_usd = (
        df.loc[df["closedPnl"] > 0, "closedPnl"].max()
        if len(df[df["closedPnl"] > 0]) > 0
        else 0
    )

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
        standard_risk=standard_risk,
    )


def _create_strategy_section(strategy_list: Optional[List[str]]) -> str:
    """Create HTML content for strategy section.

    Args:
        strategy_list: List of strategy descriptions

    Returns:
        HTML string for strategy section
    """
    if not strategy_list:
        return ""

    strategy_items = ""
    for item in strategy_list:
        strategy_items += f"<li>{item}</li>"

    return STRATEGY_SECTION_TEMPLATE.format(strategy_items=strategy_items)


def _create_psychology_section(issues_list: Optional[List[str]]) -> str:
    """Create HTML content for psychology section.

    Args:
        issues_list: List of psychological observations

    Returns:
        HTML string for psychology section
    """
    if not issues_list:
        return ""

    psychology_items = ""
    for item in issues_list:
        psychology_items += f"<li>{item}</li>"

    return PSYCHOLOGY_SECTION_TEMPLATE.format(psychology_items=psychology_items)


def _create_improvements_section(goals_list: Optional[List[str]]) -> str:
    """Create HTML content for improvements section.

    Args:
        goals_list: List of improvement goals

    Returns:
        HTML string for improvements section
    """
    if not goals_list:
        return ""

    improvement_items = ""
    for item in goals_list:
        improvement_items += f"<li>{item}</li>"

    return IMPROVEMENTS_SECTION_TEMPLATE.format(improvement_items=improvement_items)


def _make_cumulative_pnl_plot(df: pd.DataFrame) -> None:
    """Generate cumulative PnL plot and save to report plots folder.

    Args:
        df: DataFrame with trading data
    """
    global report_plots_folder
    # 1. Cumulative PnL Chart
    plt.figure(figsize=(14, 12))

    # Create a subplot layout: top for main chart, middle for individual trades, bottom for explanation
    gs = plt.GridSpec(3, 1, height_ratios=[4, 2, 2], hspace=0.4)

    # Main plot - Cumulative PnL
    ax1 = plt.subplot(gs[0])

    # Plot the cumulative PnL with clear markers for each trade
    ax1.plot(
        df["createdTime"],
        df["cumulative_pnl"],
        linewidth=3,
        color="blue",
        marker=".",
        markersize=8,
        label="Cumulative PnL",
    )

    ax1.scatter(
        df["createdTime"].iloc[0],
        df["cumulative_pnl"].iloc[0],
        color="green",
        s=120,
        label="Starting balance",
        zorder=5,
        marker="o",
    )

    # Ending point - current balance
    ax1.scatter(
        df["createdTime"].iloc[-1],
        df["cumulative_pnl"].iloc[-1],
        color="purple",
        s=120,
        label="Current balance",
        zorder=5,
        marker="s",
    )

    # Low point - worst performance
    low_idx = df["cumulative_pnl"].idxmin()
    ax1.scatter(
        df["createdTime"].iloc[low_idx],
        df["cumulative_pnl"].iloc[low_idx],
        color="red",
        s=120,
        label=f'Lowest point (${df["cumulative_pnl"].min():.2f})',
        zorder=5,
        marker="v",
    )

    # High point - best performance
    high_idx = df["cumulative_pnl"].idxmax()
    if high_idx != len(df) - 1:
        ax1.scatter(
            df["createdTime"].iloc[high_idx],
            df["cumulative_pnl"].iloc[high_idx],
            color="orange",
            s=120,
            label=f'Highest point (${df["cumulative_pnl"].max():.2f})',
            zorder=5,
            marker="^",
        )

    # Add a horizontal line at zero (breakeven point)
    ax1.axhline(y=0, color="red", linestyle="--", linewidth=2, label="Breakeven line")

    # Add clear annotations on the chart
    ax1.annotate(
        "Up = Profit",
        xy=(0.02, 0.95),
        xycoords="axes fraction",
        fontsize=12,
        color="green",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="green", alpha=0.8),
    )
    ax1.annotate(
        "Down = Loss",
        xy=(0.02, 0.05),
        xycoords="axes fraction",
        fontsize=12,
        color="red",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="red", alpha=0.8),
    )

    # Format the dates on the x-axis to be very clear
    date_format = mdates.DateFormatter("%b %d")
    ax1.xaxis.set_major_formatter(date_format)
    ax1.xaxis.set_major_locator(mdates.DayLocator())
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, fontsize=10)

    # Add annotations for start and end values
    start_val = df["cumulative_pnl"].iloc[0]
    end_val = df["cumulative_pnl"].iloc[-1]
    net_change = end_val - start_val

    # Set a more informative title and labels
    ax1.set_title(
        "Your Trading Account Balance Over Time", fontsize=16, fontweight="bold"
    )
    ax1.set_xlabel("Trading Date", fontsize=14)
    ax1.set_ylabel("Account Balance ($)", fontsize=14)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="upper right", fontsize=10)

    # Add Y-axis ticks with dollar signs for clarity
    formatter = plt.FuncFormatter(lambda x, pos: f"${x:.0f}")
    ax1.yaxis.set_major_formatter(formatter)

    # Add second plot showing individual trades
    ax2 = plt.subplot(gs[1])

    # Create bar chart of individual trade PnLs
    ax2.bar(
        df["createdTime"],
        df["closedPnl"],
        width=0.02,
        color=[("green" if x > 0 else "red") for x in df["closedPnl"]],
        alpha=0.7,
    )

    # Add horizontal line at zero
    ax2.axhline(y=0, color="black", linestyle="--", alpha=0.5)

    # Set labels
    ax2.set_title("Individual Trade Profits/Losses", fontsize=14)
    ax2.set_xlabel("Trade Date", fontsize=12)
    ax2.set_ylabel("Profit/Loss ($)", fontsize=12)

    # Format x-axis dates
    ax2.xaxis.set_major_formatter(date_format)
    ax2.xaxis.set_major_locator(mdates.DayLocator())
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, fontsize=10)

    # Format y-axis with dollar signs
    ax2.yaxis.set_major_formatter(formatter)

    # Add explanation panel
    ax3 = plt.subplot(gs[2])
    ax3.axis("off")  # Hide axes

    # Calculate key metrics
    total_trades = len(df)
    winning_trades = (df["closedPnl"] > 0).sum()
    losing_trades = (df["closedPnl"] < 0).sum()

    # Calculate drawdowns
    df["rolling_max"] = df["cumulative_pnl"].cummax()
    df["drawdown"] = df["rolling_max"] - df["cumulative_pnl"]
    max_drawdown = df["drawdown"].max()

    # Calculate average win and loss
    avg_win = (
        df.loc[df["closedPnl"] > 0, "closedPnl"].mean()
        if len(df[df["closedPnl"] > 0]) > 0
        else 0
    )
    avg_loss = (
        df.loc[df["closedPnl"] < 0, "closedPnl"].mean()
        if len(df[df["closedPnl"] < 0]) > 0
        else 0
    )

    # Create an explanation text box
    explanation_title = "HOW TO READ THIS CHART"
    explanation_text = (
        "The top chart shows your trading account balance over time:\n\n"
        "• X-axis (horizontal): Shows the dates when trades occurred\n"
        "• Y-axis (vertical): Shows your cumulative account balance in dollars\n\n"
        "• BLUE LINE: Your account balance changing with each trade\n"
        "• RED DASHED LINE: The breakeven point (zero profit/loss)\n\n"
        "• When the blue line goes UP, your account is growing (profitable trades)\n"
        "• When the blue line goes DOWN, your account is shrinking (losing trades)\n\n"
        "The middle chart shows your individual trades:\n\n"
        "• GREEN bars: Winning trades\n"
        "• RED bars: Losing trades\n"
    )

    # Create a summary stats text box
    stats_title = "YOUR TRADING SUMMARY"
    stats_text = (
        f"• Starting: ${start_val:.2f}\n"
        f"• Current: ${end_val:.2f}\n"
        f"• Total Change: {'+' if net_change >= 0 else ''}{net_change:.2f} USD\n\n"
        f"• Wins: {winning_trades} trades\n"
        f"• Losses: {losing_trades} trades\n"
        f"• Win Rate: {winning_trades/total_trades*100:.1f}%\n\n"
        f"• Average Win: ${avg_win:.2f}\n"
        f"• Average Loss: ${abs(avg_loss):.2f}\n"
        f"• Win/Loss Ratio: {abs(avg_win/avg_loss) if avg_loss != 0 else 0:.2f}\n\n"
        f"• Largest Drawdown: ${max_drawdown:.2f}\n"
        f"• Trading Period: {(df['createdTime'].iloc[-1] - df['createdTime'].iloc[0]).days + 1} days"
    )

    # Set up the explanation area with two columns
    ax3.text(
        0.01,
        0.99,
        explanation_title,
        fontsize=14,
        fontweight="bold",
        va="top",
        ha="left",
        transform=ax3.transAxes,
    )
    ax3.text(
        0.01,
        0.90,
        explanation_text,
        fontsize=12,
        va="top",
        ha="left",
        transform=ax3.transAxes,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#f0f0f0", alpha=0.8),
    )

    # Set up the stats area
    ax3.text(
        0.62,
        0.99,
        stats_title,
        fontsize=14,
        fontweight="bold",
        va="top",
        ha="left",
        transform=ax3.transAxes,
    )
    ax3.text(
        0.62,
        0.90,
        stats_text,
        fontsize=12,
        va="top",
        ha="left",
        transform=ax3.transAxes,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#e8f4f8", alpha=0.8),
    )

    plt.tight_layout()
    plt.savefig(report_plots_folder.format(filename="cumulative_pnl"), dpi=100)
    plt.close()


def _make_daily_pnl_plot(df: pd.DataFrame) -> None:
    """Generate daily PnL bar chart and save to report plots folder.

    Args:
        df: DataFrame with trading data
    """
    # 2. Daily PnL Chart
    daily_pnl = df.groupby("date")["closedPnl"].sum()
    plt.figure()
    daily_pnl.plot(kind="bar", color=[("green" if x > 0 else "red") for x in daily_pnl])
    plt.title("Daily PnL")
    plt.grid(axis="y")
    plt.tight_layout()
    plt.savefig(report_plots_folder.format(filename="daily_pnl"), dpi=100)
    plt.close()


def _make_pnl_distribution_plot(df: pd.DataFrame) -> None:
    """Generate PnL distribution histogram and save to report plots folder.

    Args:
        df: DataFrame with trading data
    """
    # 3. Win/Loss Distribution
    plt.figure()
    plt.hist(df["closedPnl"], bins=20, alpha=0.7, color="blue", edgecolor="black")
    plt.axvline(x=0, color="red", linestyle="--")
    plt.title("PnL Distribution")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(report_plots_folder.format(filename="pnl_distribution"), dpi=100)
    plt.close()


def _make_duration_distribution_plot(df: pd.DataFrame) -> None:
    """Generate trade duration distribution plot and save to report plots folder.

    Args:
        df: DataFrame with trading data
    """
    global report_plots_folder
    # 4. Trade Duration Analysis
    plt.figure(figsize=(12, 10))

    # Create a subplot layout: top for main chart, bottom for statistics
    gs = plt.GridSpec(2, 1, height_ratios=[3, 1], hspace=0.3)

    # Main histogram plot
    ax1 = plt.subplot(gs[0])

    # Use fewer bins for better readability and add KDE curve
    sns.histplot(
        df["duration_hours"],
        bins=10,
        kde=True,
        ax=ax1,
        color="purple",
        edgecolor="black",
        alpha=0.7,
    )

    # Calculate statistical values
    median_duration = df["duration_hours"].median()
    mean_duration = df["duration_hours"].mean()
    max_duration = df["duration_hours"].max()

    # Add vertical lines for mean and median
    ax1.axvline(
        x=median_duration,
        color="red",
        linestyle="--",
        linewidth=2,
        label=f"Median: {median_duration:.2f} hrs",
    )
    ax1.axvline(
        x=mean_duration,
        color="green",
        linestyle="--",
        linewidth=2,
        label=f"Mean: {mean_duration:.2f} hrs",
    )
    ax1.legend()

    # Set a more informative title and labels
    ax1.set_title("Trade Duration Distribution", fontsize=14, fontweight="bold")
    ax1.set_xlabel("Duration (hours)", fontsize=12)
    ax1.set_ylabel("Number of Trades", fontsize=12)
    ax1.grid(True, alpha=0.3)

    # Add annotations showing key metrics
    ax2 = plt.subplot(gs[1])
    ax2.axis("off")  # Hide axes

    # Create a text box with statistics
    stats_text = (
        f"Trade Duration Statistics:\n"
        f"• Short trades (<1 hour): {len(df[df['duration_hours'] < 1])} trades ({len(df[df['duration_hours'] < 1])/len(df)*100:.1f}%)\n"
        f"• Medium trades (1-24 hours): {len(df[(df['duration_hours'] >= 1) & (df['duration_hours'] < 24)])} trades "
        f"({len(df[(df['duration_hours'] >= 1) & (df['duration_hours'] < 24)])/len(df)*100:.1f}%)\n"
        f"• Long trades (>24 hours): {len(df[df['duration_hours'] >= 24])} trades ({len(df[df['duration_hours'] >= 24])/len(df)*100:.1f}%)\n"
        f"• Longest trade: {max_duration:.2f} hours ({max_duration/24:.1f} days)\n"
        f"• Shortest trade: {df['duration_hours'].min():.2f} hours ({df['duration_hours'].min()*60:.1f} minutes)"
    )

    ax2.text(
        0.5,
        0.5,
        stats_text,
        ha="center",
        va="center",
        fontsize=12,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.8),
    )

    plt.tight_layout()
    plt.savefig(report_plots_folder.format(filename="duration_distribution"), dpi=100)
    plt.close()


def _make_hourly_heatmap(df: pd.DataFrame) -> None:
    """Generate hourly performance heatmap and save to report plots folder.

    Args:
        df: DataFrame with trading data
    """
    global report_plots_folder
    # 6. Hourly Performance Heatmap
    hourly_performance = (
        df.groupby("hour_of_day")["closedPnl"]
        .agg(["mean", "sum", "count"])
        .reset_index()
    )
    plt.figure()
    sns.heatmap(
        hourly_performance.pivot_table(index="hour_of_day", values="mean"),
        cmap="RdYlGn",
        annot=True,
    )
    plt.title("Average PnL by Hour of Day")
    plt.tight_layout()
    plt.savefig(report_plots_folder.format(filename="hourly_heatmap"))
    plt.close()

    return hourly_performance
