import logging
from config import MIN_RR_RATIO

logger = logging.getLogger(__name__)

def validate_trade_plan(plan, snapshot=None) -> bool:
    """
    Validates a TradePlan object to ensure SL/TP logic, RR, and trend alignment is sound.
    If invalid, returns False.
    """
    if plan.action == "WAIT":
        return True
        
    if plan.exact_entry_price <= 0 or plan.stop_loss <= 0 or plan.take_profit_1 <= 0:
        logger.error("Prices must be greater than 0.")
        return False

    # Hard trend alignment check (Strict No-Counter-Trend Rule)
    if snapshot and getattr(snapshot, "trend_structure", None):
        trend = (snapshot.trend_structure or "").lower()
        if "bearish" in trend and plan.action == "BUY":
            logger.error("Trend is Bearish (price below SMA20); counter-trend BUY is strictly forbidden to prevent catching falling knives.")
            return False
        elif "bullish" in trend and plan.action == "SELL":
            logger.error("Trend is Bullish (price above SMA20); counter-trend SELL is strictly forbidden to prevent fighting an uptrend.")
            return False

    # Calculate Risk
    risk = abs(plan.exact_entry_price - plan.stop_loss)
    if risk == 0:
        logger.error("Risk cannot be 0.")
        return False
        
    # Calculate Reward
    reward = abs(plan.take_profit_1 - plan.exact_entry_price)
    rr_ratio = reward / risk
    
    if risk < 5.0:
        logger.error(f"Stop Loss distance (${risk:.2f}) is too tight (< $5.00) for Gold volatility; high risk of stop hunt.")
        return False

    if rr_ratio < MIN_RR_RATIO:
        logger.error(f"Risk/Reward Ratio {rr_ratio:.2f} is below minimum {MIN_RR_RATIO}.")
        return False

    if plan.action == "BUY":
        if not (plan.stop_loss < plan.exact_entry_price < plan.take_profit_1):
            logger.error("Invalid BUY setup: must be SL < Entry < TP")
            return False
            
    elif plan.action == "SELL":
        if not (plan.take_profit_1 < plan.exact_entry_price < plan.stop_loss):
            logger.error("Invalid SELL setup: must be TP < Entry < SL")
            return False
            
    return True
