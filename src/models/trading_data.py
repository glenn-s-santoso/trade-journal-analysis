"""Pydantic models for trading data structures"""
from datetime import datetime
from typing import Dict, List, Optional, Union, Literal, Any
from pydantic import BaseModel, Field, model_validator
import pandas as pd

class RawTradeData(BaseModel):
    """Raw trade data from Bybit API"""
    symbol: str
    side: Literal["Buy", "Sell"]
    closedPnl: str  # Will be converted to float
    createdTime: str  # Timestamp in milliseconds as string
    updatedTime: str  # Timestamp in milliseconds as string
    avgEntryPrice: Optional[str] = None
    avgExitPrice: Optional[str] = None
    qty: Optional[str] = None
    closedSize: Optional[str] = None
    cumEntryValue: Optional[str] = None
    cumExitValue: Optional[str] = None
    leverage: Optional[str] = None
    orderId: Optional[str] = None
    orderLinkId: Optional[str] = None
    
    model_config = {
        "extra": "allow"  # Allow extra fields from the API
    }

class ProcessedTradeData(BaseModel):
    """Processed trade data with derived fields"""
    # Original fields (converted)
    symbol: str
    side: Literal["Buy", "Sell"]
    closedPnl: float
    createdTime: datetime
    updatedTime: datetime
    avgEntryPrice: Optional[float] = None
    avgExitPrice: Optional[float] = None
    qty: Optional[float] = None
    closedSize: Optional[float] = None
    cumEntryValue: Optional[float] = None
    cumExitValue: Optional[float] = None
    leverage: Optional[float] = None
    orderId: Optional[str] = None
    orderLinkId: Optional[str] = None
    
    # Derived fields
    duration_seconds: float = Field(..., description="Trade duration in seconds")
    duration_hours: float = Field(..., description="Trade duration in hours")
    date: date = Field(..., description="Trade date")
    hour: int = Field(..., description="Hour of day (0-23)")
    day_of_week: str = Field(..., description="Day of the week name")
    profit_flag: bool = Field(..., description="True if trade was profitable")
    
    @model_validator(mode='before')
    def set_profit_flag(cls, data: Any) -> Any:
        """Set profit flag based on closedPnl"""
        if isinstance(data, dict) and 'closedPnl' in data:
            data['profit_flag'] = data['closedPnl'] > 0
        return data

class SymbolPerformance(BaseModel):
    """Performance metrics for a trading symbol"""
    total_pnl: float
    trade_count: int
    win_rate: float
    avg_profit: float

class TradingSummary(BaseModel):
    """Summary of trading performance"""
    period: Dict[str, Union[str, int]] = Field(..., description="Trading period information")
    overall_performance: Dict[str, float] = Field(..., description="Overall performance metrics")
    risk_reward: Dict[str, float] = Field(..., description="Risk-reward metrics")
    symbols: Dict[str, SymbolPerformance] = Field(..., description="Performance by symbol")
    time_patterns: Dict[str, Optional[Union[int, float, str]]] = Field(..., description="Time-based patterns")
    
    # Optional user reflections
    user_reflections: Optional[Dict[str, Union[List[str], str]]] = None

def convert_raw_to_processed(raw_data: List[RawTradeData]) -> List[ProcessedTradeData]:
    """Convert raw trade data to processed format with derived fields"""
    # Convert to DataFrame for easier processing
    df = pd.DataFrame([data.model_dump() for data in raw_data])
    
    # Convert string values to appropriate types
    df['closedPnl'] = df['closedPnl'].astype(float)
    df['createdTime'] = pd.to_datetime(pd.to_numeric(df['createdTime']), unit='ms')
    df['updatedTime'] = pd.to_datetime(pd.to_numeric(df['updatedTime']), unit='ms')
    
    # Convert optional numeric fields
    numeric_fields = ['avgEntryPrice', 'avgExitPrice', 'qty', 'closedSize', 
                     'cumEntryValue', 'cumExitValue', 'leverage']
    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors='coerce')
    
    # Add derived columns
    df['duration_seconds'] = (df['updatedTime'] - df['createdTime']).dt.total_seconds()
    df['duration_hours'] = df['duration_seconds'] / 3600
    df['date'] = df['createdTime'].dt.date
    df['hour'] = df['createdTime'].dt.hour
    df['day_of_week'] = df['createdTime'].dt.day_name()
    df['profit_flag'] = df['closedPnl'] > 0
    
    # Convert back to Pydantic models
    processed_data = []
    for _, row in df.iterrows():
        try:
            processed_data.append(ProcessedTradeData.model_validate(row.to_dict()))
        except Exception as e:
            print(f"Warning: Could not convert row to ProcessedTradeData: {e}")
            # You could add fallback handling here if needed
        
    return processed_data
