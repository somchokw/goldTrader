from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

class MarketSnapshot(BaseModel):
    symbol: str
    timeframe: str
    timestamp: str
    close_price: float
    high_price: float
    low_price: float
    sma_20: float
    rsi_14: float
    macd: float
    macd_signal: float
    bb_lower: float
    bb_upper: float
    atr: Optional[float] = None
    volume: Optional[float] = None
    trend_structure: str = "Neutral"

class TradePlan(BaseModel):
    action: str = Field(description="BUY, SELL, or WAIT")
    exact_entry_price: float = Field(description="Exact entry price level")
    stop_loss: float = Field(description="Stop loss level")
    take_profit_1: float = Field(description="First take profit level")
    take_profit_2: Optional[float] = Field(None, description="Second take profit level (optional)")
    rationale: str = Field(description="Reasoning behind the trade plan")

    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        v = v.upper()
        if v not in ["BUY", "SELL", "WAIT"]:
            raise ValueError('Action must be BUY, SELL, or WAIT')
        return v
