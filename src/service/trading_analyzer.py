"""Trading analyzer module using Large Language Models for trading performance analysis.

Provides TradingAnalyzer class to analyze closed PnL data and generate insights.
"""

import json
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from src.constants.env import (
    OPENROUTER_API_BASE,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    STANDARD_RISK,
)
from src.constants.prompt import ANALYZER_PROMPT


class TradingAnalyzer:
    """Trading performance analyzer using LLM."""

    def __init__(self):
        """Initialize the analyzer with API settings."""
        self.api_key = OPENROUTER_API_KEY
        self.api_base = OPENROUTER_API_BASE
        self.model = OPENROUTER_MODEL

    def analyze_trading_data(
        self, trading_data: Dict[str, Any], user_notes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze trading data and generate insights.

        Args:
            trading_data: Dictionary containing trading performance data
            user_notes: User's own notes about their trading

        Returns:
            Analysis results with insights and recommendations
        """
        if not self.api_key:
            return {
                "error": "OpenRouter API key not found. Please set OPENROUTER_API_KEY in .env file."
            }

        # Prepare the prompt with trading data
        prompt = self._create_prompt(trading_data, user_notes)

        try:
            # Call the OpenRouter API
            response = self._call_openrouter_api(prompt)
            return self._process_response(response)
        except Exception as e:
            return {"error": f"API call failed: {str(e)}"}

    def _create_prompt(
        self, trading_data: Dict[str, Any], user_notes: Optional[Dict[str, Any]]
    ) -> str:
        """Create a structured prompt for the LLM."""
        prompt = ANALYZER_PROMPT.format(
            trading_data=json.dumps(trading_data, indent=2),
            user_notes=json.dumps(user_notes, indent=2)
            if user_notes
            else "None provided",
        )
        return prompt

    def _call_openrouter_api(self, prompt: str) -> Dict[str, Any]:
        """Make the actual API call to OpenRouter.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            The response from the LLM

        Raises:
            Exception: If the API call fails
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional trading coach with expertise in analyzing trading performance data.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        response = requests.post(
            f"{self.api_base}/chat/completions", headers=headers, json=data
        )

        if response.status_code != 200:
            raise Exception(
                f"API request failed with status {response.status_code}: {response.text}"
            )

        return response.json()

    def _process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process the API response and extract the analysis.

        Args:
            response: The API response from OpenRouter

        Returns:
            The processed analysis results

        Raises:
            Exception: If the response cannot be processed
        """
        try:
            content = response["choices"][0]["message"]["content"]

            try:
                # Find JSON in the response (it might be wrapped in markdown code blocks)
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0]
                else:
                    json_str = content

                analysis = json.loads(json_str)
            except json.JSONDecodeError:
                # If JSON parsing fails, return the raw text
                analysis = {"raw_analysis": content}

            return analysis
        except Exception as e:
            return {
                "error": f"Failed to process response: {str(e)}",
                "raw_response": response,
            }

    def prepare_trading_data_summary(
        self,
        pnl_data: List[Dict[str, Any]],
        user_input: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Prepare a summary of trading data for LLM analysis.

        Args:
            pnl_data: Raw PnL data from Bybit API
            user_input: User's input data with reflections

        Returns:
            Structured summary of trading performance
        """
        # Convert raw data to Pydantic models
        try:
            # Convert to DataFrame for analysis
            df = pd.DataFrame(pnl_data)

            # Basic type conversions
            df["closedPnl"] = df["closedPnl"].astype(float)
            df["createdTime"] = pd.to_datetime(
                pd.to_numeric(df["createdTime"]), unit="ms"
            )
            df["updatedTime"] = pd.to_datetime(
                pd.to_numeric(df["updatedTime"]), unit="ms"
            )

            # Add derived columns
            df["duration_hours"] = (
                df["updatedTime"] - df["createdTime"]
            ).dt.total_seconds() / 3600
            df["duration_seconds"] = (
                df["updatedTime"] - df["createdTime"]
            ).dt.total_seconds()
            df["date"] = df["createdTime"].dt.date
            df["hour"] = df["createdTime"].dt.hour
            df["day_of_week"] = df["createdTime"].dt.day_name()
            df["profit_flag"] = df["closedPnl"] > 0
        except Exception as e:
            print(f"Warning: Could not fully parse trade data as Pydantic models: {e}")
            # Fallback to DataFrame approach
            df = pd.DataFrame(pnl_data)

            # Basic type conversions
            df["closedPnl"] = df["closedPnl"].astype(float)
            df["createdTime"] = pd.to_datetime(
                pd.to_numeric(df["createdTime"]), unit="ms"
            )
            df["updatedTime"] = pd.to_datetime(
                pd.to_numeric(df["updatedTime"]), unit="ms"
            )

            # Add derived columns
            df["duration_hours"] = (
                df["updatedTime"] - df["createdTime"]
            ).dt.total_seconds() / 3600
            df["duration_seconds"] = (
                df["updatedTime"] - df["createdTime"]
            ).dt.total_seconds()
            df["date"] = df["createdTime"].dt.date
            df["hour"] = df["createdTime"].dt.hour
            df["day_of_week"] = df["createdTime"].dt.day_name()
            df["profit_flag"] = df["closedPnl"] > 0

        # Calculate performance metrics
        total_pnl = df["closedPnl"].sum()
        win_count = (df["closedPnl"] > 0).sum()
        loss_count = (df["closedPnl"] < 0).sum()
        total_trades = len(df)
        win_rate = win_count / total_trades if total_trades > 0 else 0

        avg_win = (
            df.loc[df["closedPnl"] > 0, "closedPnl"].mean() if win_count > 0 else 0
        )
        avg_loss = (
            df.loc[df["closedPnl"] < 0, "closedPnl"].mean() if loss_count > 0 else 0
        )

        standard_risk = STANDARD_RISK

        if user_input and "RISK_MANAGEMENT" in user_input:
            standard_risk = user_input["RISK_MANAGEMENT"].get(
                "standard_risk_per_trade", 9
            )

        avg_win_r = avg_win / standard_risk if standard_risk > 0 else 0
        avg_loss_r = abs(avg_loss) / standard_risk if standard_risk > 0 else 0
        profit_factor = (
            abs(
                df[df["closedPnl"] > 0]["closedPnl"].sum()
                / df[df["closedPnl"] < 0]["closedPnl"].sum()
            )
            if df[df["closedPnl"] < 0]["closedPnl"].sum() != 0
            else float("inf")
        )

        # Symbols analysis
        symbol_performance = {}
        for symbol in df["symbol"].unique():
            symbol_df = df[df["symbol"] == symbol]
            symbol_win_rate = (symbol_df["closedPnl"] > 0).mean()
            symbol_performance[symbol] = {
                "total_pnl": symbol_df["closedPnl"].sum(),
                "trade_count": len(symbol_df),
                "win_rate": symbol_win_rate,
                "avg_profit": symbol_df["closedPnl"].mean(),
            }

        # Time-based analysis
        hourly_pnl = (
            df.groupby("hour")["closedPnl"].agg(["mean", "sum", "count"]).to_dict()
        )
        daily_pnl = (
            df.groupby("day_of_week")["closedPnl"]
            .agg(["mean", "sum", "count"])
            .to_dict()
        )

        # Trading patterns
        win_durations = (
            df.loc[df["closedPnl"] > 0, "duration_hours"].mean() if win_count > 0 else 0
        )
        loss_durations = (
            df.loc[df["closedPnl"] < 0, "duration_hours"].mean()
            if loss_count > 0
            else 0
        )

        # Create structured summary dict
        summary_dict = {
            "period": {
                "start": df["createdTime"].min().strftime("%Y-%m-%d"),
                "end": df["createdTime"].max().strftime("%Y-%m-%d"),
                "days": (df["createdTime"].max() - df["createdTime"].min()).days + 1,
            },
            "overall_performance": {
                "total_pnl": float(total_pnl),
                "win_rate": float(win_rate),
                "total_trades": int(total_trades),
                "winning_trades": int(win_count),
                "losing_trades": int(loss_count),
                "profit_factor": float(profit_factor),
            },
            "risk_reward": {
                "avg_win": float(avg_win),
                "avg_loss": float(avg_loss),
                "avg_win_r": float(avg_win_r),
                "avg_loss_r": float(avg_loss_r),
                "reward_risk_ratio": float(abs(avg_win / avg_loss))
                if avg_loss != 0
                else float("inf"),
            },
            "symbols": symbol_performance,
            "time_patterns": {
                "best_hour": int(df.groupby("hour")["closedPnl"].mean().idxmax())
                if not df.groupby("hour")["closedPnl"].mean().empty
                else None,
                "worst_hour": int(df.groupby("hour")["closedPnl"].mean().idxmin())
                if not df.groupby("hour")["closedPnl"].mean().empty
                else None,
                "best_day": df.groupby("day_of_week")["closedPnl"].mean().idxmax()
                if not df.groupby("day_of_week")["closedPnl"].mean().empty
                else None,
                "worst_day": df.groupby("day_of_week")["closedPnl"].mean().idxmin()
                if not df.groupby("day_of_week")["closedPnl"].mean().empty
                else None,
                "win_duration_hours": float(win_durations),
                "loss_duration_hours": float(loss_durations),
                "hourly_performance": hourly_pnl,
                "daily_performance": daily_pnl,
            },
        }

        # Add user reflections if available
        if user_input:
            user_reflections = {
                "strategy": user_input.get("strategy", []),
                "psychological_issues": user_input.get("psychology", []),
                "PERSONAL_REFLECTION": user_input.get("reflection", ""),
                "IMPROVEMENT_GOALS": user_input.get("improvements", []),
            }
            summary_dict["user_reflections"] = user_reflections

        return summary_dict
