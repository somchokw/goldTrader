import logging
from datetime import datetime, timezone
from typing import Optional
try:
    from curl_cffi import requests
except ImportError:
    import requests

from config import SYMBOL
from models import MarketSnapshot
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def _get_request(url: str, **kwargs):
    """Helper to perform GET requests with curl_cffi impersonation if available."""
    headers = kwargs.pop('headers', {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    timeout = kwargs.pop('timeout', 10)
    req_kwargs = {'headers': headers, 'timeout': timeout, **kwargs}
    if hasattr(requests, 'get') and 'impersonate' in requests.get.__code__.co_varnames:
        req_kwargs['impersonate'] = 'chrome110'
    return requests.get(url, **req_kwargs)

def _post_request(url: str, **kwargs):
    """Helper to perform POST requests with curl_cffi impersonation if available."""
    headers = kwargs.pop('headers', {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    timeout = kwargs.pop('timeout', 10)
    req_kwargs = {'headers': headers, 'timeout': timeout, **kwargs}
    if hasattr(requests, 'post') and 'impersonate' in requests.post.__code__.co_varnames:
        req_kwargs['impersonate'] = 'chrome110'
    return requests.post(url, **req_kwargs)

def get_spot_gold_price() -> Optional[float]:
    """Fetch real-time Spot Gold price from TradingView scanner API."""
    try:
        data = {
            'symbols': {'tickers': ['TVC:GOLD', 'OANDA:XAUUSD', 'FOREXCOM:XAUUSD'], 'query': {'types': []}},
            'columns': ['close']
        }
        r = _post_request('https://scanner.tradingview.com/global/scan', json=data, timeout=10)
        if r.status_code == 200:
            json_data = r.json()
            for item in json_data.get('data', []):
                close_val = item.get('d', [None])[0]
                if close_val is not None:
                    return float(close_val)
    except Exception as e:
        logger.error(f"Failed to fetch Spot Gold price from TradingView scanner: {e}")
    return None

def fetch_technical_data(interval: str, period: str = None) -> Optional[MarketSnapshot]:
    """Fetch technical data using Binance (PAXG) and adjust to Spot Gold price."""
    try:
        # 1. Fetch real Spot Gold price
        spot_price = get_spot_gold_price()
        
        # 2. Fetch Gold proxy (PAXGUSDT) history for indicators with multiple endpoint fallbacks
        binance_interval = "15m" if interval == "15m" else "1d"
        binance_endpoints = [
            f"https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval={binance_interval}&limit=500",
            f"https://data-api.binance.vision/api/v3/klines?symbol=PAXGUSDT&interval={binance_interval}&limit=500",
            f"https://api.binance.us/api/v3/klines?symbol=PAXGUSDT&interval={binance_interval}&limit=500"
        ]
        
        data = None
        for ep in binance_endpoints:
            try:
                r = _get_request(ep, timeout=10)
                if r.status_code == 200:
                    json_res = r.json()
                    if isinstance(json_res, list) and len(json_res) >= 26:
                        data = json_res
                        break
                else:
                    logger.warning(f"Binance endpoint {ep} returned status {r.status_code}")
            except Exception as ep_err:
                logger.warning(f"Error fetching from Binance endpoint {ep}: {ep_err}")

        if not data or len(data) < 26:
            logger.error(f"Insufficient historical data from Binance for {interval}")
            return None
            
        # Convert Binance data to DataFrame
        df = pd.DataFrame(data, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'])
        hist = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
            
        proxy_close = float(hist['Close'].iloc[-1])
        proxy_high = float(hist['High'].iloc[-1])
        proxy_low = float(hist['Low'].iloc[-1])
        volume = float(hist['Volume'].iloc[-1])
        
        # Fallback to proxy price if TradingView scanner failed
        if not spot_price:
            logger.warning("Could not retrieve Spot Gold price from TV. Falling back to PAXGUSDT price.")
            spot_price = proxy_close
        
        # 3. Calculate Spread
        spread = proxy_close - spot_price
        logger.info(f"PAXG Proxy: {proxy_close}, Spot Gold: {spot_price}, Spread: {spread}")
        
        # Adjust current candle prices
        close_price = spot_price
        high_price = proxy_high - spread
        low_price = proxy_low - spread
        
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
