import logging
from datetime import datetime, timezone
from tradingview_ta import TA_Handler, Interval
from config import SYMBOL, EXCHANGE, SCREENER
from models import MarketSnapshot

logger = logging.getLogger(__name__)

def fetch_technical_data(interval: str, period: str = None) -> MarketSnapshot:
    """Fetch technical data directly from TradingView API."""
    try:
        # Map our internal interval string to TradingView TA Interval enum
        tv_interval = Interval.INTERVAL_15_MINUTES if interval == "15m" else Interval.INTERVAL_1_DAY
        
        handler = TA_Handler(
            symbol=SYMBOL,
            exchange=EXCHANGE,
            screener=SCREENER,
            interval=tv_interval,
        )
        
        analysis = handler.get_analysis()
        indicators = analysis.indicators
        
        if not indicators:
            logger.error(f"No indicators returned from TradingView for {interval}")
            return None
            
        close_price = indicators.get("close", 0.0)
        sma20 = indicators.get("SMA20", 0.0)
        
        # Determine Trend Structure based on SMA20
        trend = "Bullish" if close_price > sma20 else "Bearish"
        
        snapshot = MarketSnapshot(
            symbol=SYMBOL,
            timeframe=interval,
            timestamp=datetime.now(timezone.utc).isoformat(),
            close_price=float(close_price),
            high_price=float(indicators.get("high", close_price)),
            low_price=float(indicators.get("low", close_price)),
            sma_20=float(sma20),
            rsi_14=float(indicators.get("RSI", 50.0)),
            macd=float(indicators.get("MACD.macd", 0.0)),
            macd_signal=float(indicators.get("MACD.signal", 0.0)),
            bb_lower=float(indicators.get("BB.lower", 0.0)),
            bb_upper=float(indicators.get("BB.upper", 0.0)),
            atr=float(indicators.get("ATR", 0.0)) if "ATR" in indicators else None,
            volume=float(indicators.get("volume", 0.0)),
            trend_structure=trend
        )
        
        return snapshot
        
    except Exception as e:
        logger.error(f"Error fetching TradingView data for {interval}: {e}", exc_info=True)
        return None
