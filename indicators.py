import logging
from datetime import datetime, timezone
from tradingview_ta import TA_Handler, Interval
import yfinance as yf
from config import SYMBOL, EXCHANGE, SCREENER
from models import MarketSnapshot

logger = logging.getLogger(__name__)

def fetch_technical_data(interval: str, period: str = None) -> MarketSnapshot:
    """Fetch technical data directly from TradingView API and yfinance for swing points."""
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
        
        # Fetch historical data for Swing High / Swing Low and Stochastic (8,3,3)
        swing_high = None
        swing_low = None
        stoch_k = None
        stoch_d = None
        try:
            yf_interval = "15m" if interval == "15m" else "1d"
            # Fetch past 1 month (plenty for 20 periods and stoch 8,3,3)
            ticker = yf.Ticker("GC=F")
            hist = ticker.history(period="1mo", interval=yf_interval)
            if not hist.empty and len(hist) >= 20:
                recent_20 = hist.tail(20)
                swing_high = float(recent_20['High'].max())
                swing_low = float(recent_20['Low'].min())
                
                # Calculate Stochastic (8,3,3)
                low_8 = hist['Low'].rolling(window=8).min()
                high_8 = hist['High'].rolling(window=8).max()
                fast_k = 100 * ((hist['Close'] - low_8) / (high_8 - low_8))
                
                slow_k = fast_k.rolling(window=3).mean()
                slow_d = slow_k.rolling(window=3).mean()
                
                stoch_k = float(slow_k.iloc[-1])
                stoch_d = float(slow_d.iloc[-1])
        except Exception as yf_err:
            logger.warning(f"Failed to fetch yfinance history for indicators calculation: {yf_err}")

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
            trend_structure=trend,
            swing_high=swing_high,
            swing_low=swing_low,
            stoch_k=stoch_k,
            stoch_d=stoch_d
        )
        
        return snapshot
        
    except Exception as e:
        logger.error(f"Error fetching TradingView data for {interval}: {e}", exc_info=True)
        return None
