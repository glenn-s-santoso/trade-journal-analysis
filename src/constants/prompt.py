"""LLM analyzer prompt."""

ANALYZER_PROMPT = """
You are a professional trading coach and analyst. I'll provide you with my trading performance data
and personal notes. Please analyze this information and provide insights in the following categories:

1. Overall Performance Assessment
2. Strategy Effectiveness
3. Psychological Patterns
4. Risk Management Analysis
5. Key Strengths Identified
6. Areas for Improvement
7. Actionable Recommendations

Please format your analysis in JSON, with keys corresponding to the categories above.

## Trading Performance Data:

{trading_data}

## Trader's Personal Notes:

{user_notes}

Based on this data, please provide your professional analysis in JSON format.
Focus especially on identifying patterns in profitable vs. unprofitable trades,
psychological issues that might be affecting performance, and concrete steps for improvement.
"""
