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
    swing_high: Optional[float] = Field(None, description="The highest price in the recent N periods, acting as resistance.")
    swing_low: Optional[float] = Field(None, description="The lowest price in the recent N periods, acting as support.")

class TradePlan(BaseModel):
    action: str = Field(description="Must be exactly one of: 'BUY', 'SELL', 'WAIT'")
    exact_entry_price: float = Field(description="The exact recommended entry price to execute the trade.")
    stop_loss: float = Field(description="The exact stop loss price. Must be logically placed (below entry for BUY, above for SELL).")
    take_profit_1: float = Field(description="The primary target profit price.")
    take_profit_2: float = Field(description="An optional secondary target profit price (can be same as TP1 if not applicable).")
    rationale: str = Field(description="A comprehensive explanation of the trade setup in Thai, referencing technicals, macro, and risk parameters.")

    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        v = v.upper()
        if v not in ["BUY", "SELL", "WAIT"]:
            raise ValueError('Action must be BUY, SELL, or WAIT')
        return v

class TradeManagementPlan(BaseModel):
    action: str = Field(description="Must be exactly one of: 'HOLD', 'CLOSE', 'RAISE_SL', 'ADD_POSITION', 'CANCEL_PENDING', 'WAIT_PENDING'")
    suggested_sl: float = Field(description="The suggested new Stop Loss price. Use the current SL if no change is needed, or 0.0 if closing/canceling.")
    suggested_tp: float = Field(description="The suggested new Take Profit price. Use the current TP if no change is needed, or 0.0 if closing/canceling.")
    rationale: str = Field(description="A detailed explanation of why the action is recommended, analyzing current price action vs original entry, in Thai.")

    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        v = v.upper()
        if v not in ["HOLD", "CLOSE", "RAISE_SL", "ADD_POSITION", "CANCEL_PENDING", "WAIT_PENDING"]:
            raise ValueError('Action must be HOLD, CLOSE, RAISE_SL, ADD_POSITION, CANCEL_PENDING, or WAIT_PENDING')
        return v

class RecoveryPlan(BaseModel):
    action: str = Field(description="Must be exactly one of: 'REST', 'RECOVERY'")
    recovery_entry: float = Field(description="Suggested entry price for a recovery trade. 0.0 if action is REST.")
    recovery_sl: float = Field(description="Suggested Stop Loss for the recovery trade. 0.0 if action is REST.")
    recovery_tp: float = Field(description="Suggested Take Profit for the recovery trade. 0.0 if action is REST.")
    rationale: str = Field(description="A detailed explanation in Thai of why the original trade failed, and the justification for the recovery plan or resting.")

    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        v = v.upper()
        if v not in ["REST", "RECOVERY"]:
            raise ValueError('Action must be REST or RECOVERY')
        return v
