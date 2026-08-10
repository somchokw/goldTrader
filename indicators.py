import yfinance as yf
import pandas_ta as ta
import pandas as pd
import logging
from datetime import datetime, timezone, timedelta
from config import SYMBOL, STALE_DATA_THRESHOLD_MINUTES
from models import MarketSnapshot

logger = logging.getLogger(__name__)

def is_candle_closed(df: pd.DataFrame, interval: str) -> pd.DataFrame:
    """Remove the last candle if it is not yet closed."""
    if df.empty:
        return df
        
    last_idx = df.index[-1]
    now = datetime.now(timezone.utc)
    
    # Calculate approximate expected close time for the last candle
    # Note: This is simplified. True market hours would require exchange calendar.
    if interval == "1d":
        # Usually daily candle is closed if it's the previous day
        if last_idx.date() >= now.date():
             # If today's candle, drop it (unless market is closed, but this is a safe assumption)
             return df.iloc[:-1]
    elif interval == "15m":
        # 15m candle closes at last_idx + 15 mins
        close_time = last_idx + timedelta(minutes=15)
        if now < close_time:
            return df.iloc[:-1]
            
    return df

def validate_dataframe(df: pd.DataFrame, min_bars: int = 50) -> bool:
    if df.empty or len(df) < min_bars:
        return False
    # Check for NaN in critical columns
    if df[['Close', 'High', 'Low']].isna().any().any():
        return False
    return True

def check_freshness(df: pd.DataFrame) -> bool:
    if df.empty:
        return False
    last_idx = df.index[-1]
    now = datetime.now(timezone.utc)
    diff = now - last_idx
    if diff.total_seconds() / 60 > STALE_DATA_THRESHOLD_MINUTES:
        logger.warning(f"Data is stale. Last update: {last_idx}")
        return False
    return True

def fetch_technical_data(interval: str, period: str = "3mo") -> MarketSnapshot:
    """Fetch and compute technical data."""
    ticker = yf.Ticker(SYMBOL)
    df = ticker.history(period=period, interval=interval)
    
    if not validate_dataframe(df):
        logger.error(f"INSUFFICIENT_DATA for {interval}")
        return None
        
    df = is_candle_closed(df, interval)
    if df.empty:
        return None
        
    if interval == "15m" and not check_freshness(df):
        logger.error("INSUFFICIENT_DATA: Data is stale")
        return None

    # Compute Indicators
    df.ta.macd(append=True)
    df.ta.rsi(length=14, append=True)
    df.ta.bbands(length=20, std=2, append=True)
    df.ta.atr(length=14, append=True)
    df["SMA_20"] = df.ta.sma(length=20)
    
    # Find dynamic column names
    cols = df.columns
    macd_col = next((c for c in cols if c.startswith("MACD_")), None)
    macds_col = next((c for c in cols if c.startswith("MACDs_")), None)
    bbl_col = next((c for c in cols if c.startswith("BBL_")), None)
    bbu_col = next((c for c in cols if c.startswith("BBU_")), None)
    atr_col = next((c for c in cols if c.startswith("ATRr_")), None)
    
    if not all([macd_col, macds_col, bbl_col, bbu_col]):
        logger.error("Failed to compute required indicators.")
        return None

    latest = df.iloc[-1]
    
    # Evaluate Trend Structure
    close_price = latest['Close']
    sma20 = latest['SMA_20']
    trend = "Bullish" if close_price > sma20 else "Bearish"

    snapshot = MarketSnapshot(
        symbol=SYMBOL,
        timeframe=interval,
        timestamp=str(df.index[-1]),
        close_price=float(close_price),
        high_price=float(latest['High']),
        low_price=float(latest['Low']),
        sma_20=float(sma20),
        rsi_14=float(latest.get("RSI_14", 50.0)),
        macd=float(latest.get(macd_col, 0.0)),
        macd_signal=float(latest.get(macds_col, 0.0)),
        bb_lower=float(latest.get(bbl_col, 0.0)),
        bb_upper=float(latest.get(bbu_col, 0.0)),
        atr=float(latest.get(atr_col, 0.0)) if atr_col else None,
        volume=float(latest.get("Volume", 0.0)),
        trend_structure=trend
    )
    
    return snapshot
