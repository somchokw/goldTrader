import logging
from datetime import datetime, timezone
import yfinance as yf
from curl_cffi import requests
from config import SYMBOL
from models import MarketSnapshot
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def get_spot_gold_price() -> float:
    """Fetch real-time Spot Gold (TVC:GOLD) price bypassing Cloudflare using curl_cffi."""
    try:
        data = {
            'symbols': {'tickers': ['TVC:GOLD'], 'query': {'types': []}},
            'columns': ['close']
        }
        r = requests.post(
            'https://scanner.tradingview.com/global/scan', 
            json=data, 
            impersonate='chrome110',
            timeout=10
        )
        if r.status_code == 200:
            json_data = r.json()
            if 'data' in json_data and len(json_data['data']) > 0:
                return float(json_data['data'][0]['d'][0])
    except Exception as e:
        logger.error(f"Failed to fetch Spot Gold price from TradingView scanner: {e}")
    return None

def fetch_technical_data(interval: str, period: str = None) -> MarketSnapshot:
    """Fetch technical data using yfinance (Futures) and adjust to Spot Gold price."""
    try:
        # 1. Fetch real Spot Gold price
        spot_price = get_spot_gold_price()
        if not spot_price:
            logger.error("Could not retrieve Spot Gold price. Aborting technical data fetch.")
            return None

        # 2. Fetch Gold Futures (GC=F) history for indicators (never blocked)
        yf_interval = "15m" if interval == "15m" else "1d"
        ticker = yf.Ticker("GC=F")
        hist = ticker.history(period="1mo", interval=yf_interval)
        
        if hist.empty or len(hist) < 26:
            logger.error(f"Insufficient historical data from yfinance for {interval}")
            return None
            
        futures_close = float(hist['Close'].iloc[-1])
        futures_high = float(hist['High'].iloc[-1])
        futures_low = float(hist['Low'].iloc[-1])
        volume = float(hist['Volume'].iloc[-1])
        
        # 3. Calculate Spread
        spread = futures_close - spot_price
        logger.info(f"Gold Futures: {futures_close}, Spot Gold: {spot_price}, Spread: {spread}")
        
        # Adjust current candle prices
        close_price = spot_price
        high_price = futures_high - spread
        low_price = futures_low - spread
        
        # SMA 20
        sma20_series = hist['Close'].rolling(window=20).mean()
        sma20 = (float(sma20_series.iloc[-1]) - spread) if not pd.isna(sma20_series.iloc[-1]) else close_price
        
        # Trend Structure
        trend = "Bullish" if close_price > sma20 else "Bearish"
        
        # Bollinger Bands (20, 2)
        std20 = hist['Close'].rolling(window=20).std()
        bb_upper = (float((sma20_series + (std20 * 2)).iloc[-1]) - spread) if not pd.isna(std20.iloc[-1]) else close_price
        bb_lower = (float((sma20_series - (std20 * 2)).iloc[-1]) - spread) if not pd.isna(std20.iloc[-1]) else close_price
        
        # RSI 14 (Wilder's Smoothing) - Oscillator, no adjustment needed
        delta = hist['Close'].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=13, adjust=False).mean()
        ema_down = down.ewm(com=13, adjust=False).mean()
        rs = ema_up / ema_down
        rsi_series = 100 - (100 / (1 + rs))
        rsi_14 = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50.0
        
        # MACD (12, 26, 9) - Oscillator, no adjustment needed
        ema_12 = hist['Close'].ewm(span=12, adjust=False).mean()
        ema_26 = hist['Close'].ewm(span=26, adjust=False).mean()
        macd_series = ema_12 - ema_26
        macd_signal_series = macd_series.ewm(span=9, adjust=False).mean()
        macd = float(macd_series.iloc[-1]) if not pd.isna(macd_series.iloc[-1]) else 0.0
        macd_signal = float(macd_signal_series.iloc[-1]) if not pd.isna(macd_signal_series.iloc[-1]) else 0.0
        
        # ATR 14 - Spread invariant (difference between High and Low)
        high_low = hist['High'] - hist['Low']
        high_close = (hist['High'] - hist['Close'].shift()).abs()
        low_close = (hist['Low'] - hist['Close'].shift()).abs()
        ranges = [high_low, high_close, low_close]
        tr = pd.concat(ranges, axis=1).max(axis=1)
        atr_series = tr.rolling(window=14).mean()
        atr = float(atr_series.iloc[-1]) if not pd.isna(atr_series.iloc[-1]) else 0.0
        
        # Swing High / Swing Low (Past 20 periods) - Adjust by spread
        recent_20 = hist.tail(20)
        swing_high = float(recent_20['High'].max()) - spread
        swing_low = float(recent_20['Low'].min()) - spread
        
        # Stochastic (8, 3, 3) - Oscillator, no adjustment needed
        low_8 = hist['Low'].rolling(window=8).min()
        high_8 = hist['High'].rolling(window=8).max()
        fast_k = 100 * ((hist['Close'] - low_8) / (high_8 - low_8))
        slow_k = fast_k.rolling(window=3).mean()
        slow_d = slow_k.rolling(window=3).mean()
        stoch_k = float(slow_k.iloc[-1]) if not pd.isna(slow_k.iloc[-1]) else None
        stoch_d = float(slow_d.iloc[-1]) if not pd.isna(slow_d.iloc[-1]) else None

        snapshot = MarketSnapshot(
            symbol=SYMBOL,
            timeframe=interval,
            timestamp=datetime.now(timezone.utc).isoformat(),
            close_price=close_price,
            high_price=high_price,
            low_price=low_price,
            sma_20=sma20,
            rsi_14=rsi_14,
            macd=macd,
            macd_signal=macd_signal,
            bb_lower=bb_lower,
            bb_upper=bb_upper,
            atr=atr,
            volume=volume,
            trend_structure=trend,
            swing_high=swing_high,
            swing_low=swing_low,
            stoch_k=stoch_k,
            stoch_d=stoch_d
        )
        
        return snapshot
        
    except Exception as e:
        logger.error(f"Error calculating technical data for {interval}: {e}", exc_info=True)
        return None
