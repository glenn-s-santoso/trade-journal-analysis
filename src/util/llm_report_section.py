"""Helper module to create HTML sections for LLM analysis in trading reports.

Contains functions to format LLM analysis results into HTML sections for reports.
"""
from typing import Any


def format_content(content: Any) -> str:
    """Format content as HTML elements based on type.

    Args:
        content: Content to format (list or string)

    Returns:
        Formatted HTML content
    """
    if isinstance(content, list):
        formatted = "<ul>"
        for item in content:
            formatted += f"<li>{item}</li>"
        formatted += "</ul>"
        return formatted
    return f"<p>{content}</p>"


def create_llm_analysis_section(llm_analysis: dict[str, Any]) -> str:
    """Create HTML content for LLM analysis section.

    Args:
        llm_analysis: LLM analysis results dictionary

    Returns:
        HTML content for the LLM analysis section
    """
    if not llm_analysis:
        return ""

    # If there was an error, show error message
    if "error" in llm_analysis:
        return f"""
        <div class="metric-box error-box">
            <h2>LLM Analysis Error</h2>
            <p>{llm_analysis["error"]}</p>
        </div>
        """

    # Format overall assessment
    overall_assessment = llm_analysis.get(
        "Overall Performance Assessment",
        llm_analysis.get("overall_performance_assessment", "No assessment provided"),
    )

    # Format strategy assessment
    strategy_assessment = llm_analysis.get(
        "Strategy Effectiveness",
        llm_analysis.get("strategy_effectiveness", "No strategy assessment provided"),
    )

    # Format psychological patterns
    psych_patterns = llm_analysis.get(
        "Psychological Patterns",
        llm_analysis.get(
            "psychological_patterns", "No psychological analysis provided"
        ),
    )

    # Format risk management analysis
    risk_analysis = llm_analysis.get(
        "Risk Management Analysis",
        llm_analysis.get("risk_management_analysis", "No risk analysis provided"),
    )

    # Format strengths and improvements
    strengths = llm_analysis.get(
        "Key Strengths Identified",
        llm_analysis.get("key_strengths_identified", "No strengths identified"),
    )
    improvements = llm_analysis.get(
        "Areas for Improvement",
        llm_analysis.get(
            "areas_for_improvement", "No areas for improvement identified"
        ),
    )

    # Format recommendations
    recommendations = llm_analysis.get(
        "Actionable Recommendations",
        llm_analysis.get("actionable_recommendations", "No recommendations provided"),
    )

    # Create HTML content
    html = f"""
    <div class="metric-box llm-analysis">
        <h2>AI Trading Analysis</h2>

        <div class="analysis-section">
            <h3>Overall Performance Assessment</h3>
            {format_content(overall_assessment)}
        </div>

        <div class="analysis-section">
            <h3>Strategy Effectiveness</h3>
            {format_content(strategy_assessment)}
        </div>

        <div class="analysis-section">
            <h3>Psychological Patterns</h3>
            {format_content(psych_patterns)}
        </div>

        <div class="analysis-section">
            <h3>Risk Management Analysis</h3>
            {format_content(risk_analysis)}
        </div>

        <div class="analysis-section strengths">
            <h3>Key Strengths</h3>
            {format_content(strengths)}
        </div>

        <div class="analysis-section improvements">
            <h3>Areas for Improvement</h3>
            {format_content(improvements)}
        </div>

        <div class="analysis-section recommendations">
            <h3>Actionable Recommendations</h3>
            {format_content(recommendations)}
        </div>
    </div>
    """

    return html
