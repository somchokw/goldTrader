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
    """Fetch real-time Spot Gold (XAUUSD) price from live financial feeds."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # Source 1: TradingView Scanner API (Direct Institutional Spot Gold - OANDA & TVC)
    try:
        tv_payload = {
            'symbols': {'tickers': ['OANDA:XAUUSD', 'TVC:GOLD', 'FX:XAUUSD'], 'query': {'types': []}},
            'columns': ['close']
        }
        r = _post_request('https://scanner.tradingview.com/global/scan', json=tv_payload, timeout=5)
        if r.status_code == 200:
            for item in r.json().get('data', []):
                val = item.get('d', [None])[0]
                if val is not None and float(val) > 0:
                    price = round(float(val), 2)
                    logger.info(f"Retrieved live Spot Gold price from TradingView ({item.get('s')}): {price}")
                    return price
    except Exception as e:
        logger.warning(f"Failed to fetch Spot Gold price from TradingView Scanner: {e}")

    # Source 2: Swissquote Real-time Institutional Forex & Gold Feed
    try:
        r = _get_request('https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD', headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                prices = data[0].get('spreadProfilePrices', [])
                for p in prices:
                    bid = p.get('bid')
                    ask = p.get('ask')
                    if bid and ask:
                        price = round((float(bid) + float(ask)) / 2.0, 2)
                        logger.info(f"Retrieved live Spot Gold price from Swissquote: {price}")
                        return price
    except Exception as e:
        logger.warning(f"Failed to fetch Spot Gold price from Swissquote: {e}")

    # Source 3: Yahoo Finance Gold Futures (GC=F) / XAUUSD
    try:
        r = _get_request('https://query2.finance.yahoo.com/v8/finance/chart/GC=F?interval=1m&range=1d', headers=headers, timeout=5)
        if r.status_code == 200:
            meta = r.json().get('chart', {}).get('result', [{}])[0].get('meta', {})
            price = meta.get('regularMarketPrice')
            if price:
                price = round(float(price), 2)
                logger.info(f"Retrieved live Gold price from Yahoo Finance: {price}")
                return price
    except Exception as e:
        logger.warning(f"Failed to fetch Gold price from Yahoo Finance: {e}")

    # Source 4: Kraken PAXGUSD Ticker
    try:
        r = _get_request('https://api.kraken.com/0/public/Ticker?pair=PAXGUSD', timeout=5)
        if r.status_code == 200:
            res = r.json().get('result', {}).get('PAXGUSD', {})
            price_arr = res.get('c', [])
            if price_arr and len(price_arr) > 0:
                price = round(float(price_arr[0]), 2)
                logger.info(f"Retrieved live Gold price from Kraken PAXG: {price}")
                return price
    except Exception as e:
        logger.warning(f"Failed to fetch Gold price from Kraken ticker: {e}")

    # Source 5: Binance PAXG Live Ticker
    try:
        r = _get_request('https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT', timeout=5)
        if r.status_code == 200:
            price = round(float(r.json().get('price')), 2)
            logger.info(f"Retrieved live Gold price from Binance PAXG: {price}")
            return price
    except Exception as e:
        logger.warning(f"Failed to fetch Gold price from Binance ticker: {e}")

    return None

def fetch_technical_data(interval: str, period: str = None) -> Optional[MarketSnapshot]:
    """Fetch technical data using multi-source feeds (Kraken / Binance PAXG) adjusted to live Spot Gold price."""
    try:
        # 1. Fetch real Spot Gold price
        spot_price = get_spot_gold_price()
        
        # 2. Fetch Gold proxy history for indicators with Kraken (primary, resilient to US cloud bans) and Binance
        hist = None
        
        # Source A: Kraken Public OHLC API
        try:
            kraken_interval = 15 if interval == "15m" else 1440
            r_kr = _get_request(f"https://api.kraken.com/0/public/OHLC?pair=PAXGUSD&interval={kraken_interval}", timeout=8)
            if r_kr.status_code == 200:
                k_data = r_kr.json().get("result", {}).get("PAXGUSD", [])
                if isinstance(k_data, list) and len(k_data) >= 26:
                    df_kr = pd.DataFrame(k_data, columns=["time", "Open", "High", "Low", "Close", "vwap", "Volume", "count"])
                    hist = df_kr[["Open", "High", "Low", "Close", "Volume"]].astype(float)
                    logger.info(f"Retrieved {len(hist)} historical candles from Kraken OHLC ({interval})")
        except Exception as e_kr:
            logger.warning(f"Kraken OHLC fetch error: {e_kr}")
            
        # Source B: Binance Fallback
        if hist is None or len(hist) < 26:
            binance_interval = "15m" if interval == "15m" else "1d"
            binance_endpoints = [
                f"https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval={binance_interval}&limit=500",
                f"https://data-api.binance.vision/api/v3/klines?symbol=PAXGUSDT&interval={binance_interval}&limit=500",
                f"https://api.binance.us/api/v3/klines?symbol=PAXGUSDT&interval={binance_interval}&limit=500"
            ]
            for ep in binance_endpoints:
                try:
                    r = _get_request(ep, timeout=8)
                    if r.status_code == 200:
                        json_res = r.json()
                        if isinstance(json_res, list) and len(json_res) >= 26:
                            df_bn = pd.DataFrame(json_res, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'])
                            hist = df_bn[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
                            logger.info(f"Retrieved {len(hist)} historical candles from Binance ({ep})")
                            break
                except Exception as ep_err:
                    logger.warning(f"Error fetching from Binance endpoint {ep}: {ep_err}")

        if hist is None or len(hist) < 26:
            logger.error(f"Insufficient historical data from all sources for {interval}")
            return None
            
        proxy_close = float(hist['Close'].iloc[-1])
        proxy_high = float(hist['High'].iloc[-1])
        proxy_low = float(hist['Low'].iloc[-1])
        volume = float(hist['Volume'].iloc[-1])
        
        # Fallback to proxy price if spot price feed failed
        if not spot_price:
            logger.warning("Could not retrieve Spot Gold price from feeds. Falling back to proxy price.")
            spot_price = proxy_close
        
        # 3. Calculate Spread
        spread = proxy_close - spot_price
        logger.info(f"Proxy Price: {proxy_close}, Spot Gold: {spot_price}, Spread: {spread:.2f}")
        
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


def evaluate_market_readiness(snapshot: MarketSnapshot) -> tuple[bool, str, str]:
    """
    Quantitative pre-filter (Zero-Cost LLM Saver).
    Evaluates whether the 15m market setup has high conviction (win rate >= 70%)
    warranting CrewAI LLM execution. Filters out low-probability chasing trades
    and saves API quota.
    
    Returns:
        (is_ready: bool, suggested_bias: str, reason: str)
    """
    if not snapshot:
        return False, "WAIT", "No market snapshot available"
        
    price = snapshot.close_price
    sma20 = snapshot.sma_20
    bb_upper = snapshot.bb_upper
    bb_lower = snapshot.bb_lower
    stoch_k = snapshot.stoch_k
    stoch_d = snapshot.stoch_d
    rsi = snapshot.rsi_14
    trend = (snapshot.trend_structure or "sideways").lower()
    
    # BB width & relative position (0.0 = lower band, 1.0 = upper band)
    bb_width = bb_upper - bb_lower if (bb_upper is not None and bb_lower is not None and bb_upper > bb_lower) else 10.0
    bb_pos = (price - bb_lower) / bb_width if bb_width > 0 else 0.5
    
    sk = stoch_k if stoch_k is not None else (rsi if rsi is not None else 50.0)

    # 1. BEARISH REGIME: Trade ONLY pullbacks to sell (Trend is your friend)
    if "bearish" in trend:
        # Pullback into resistance (near SMA20 or upper half) + Stoch >= 60
        if sk >= 60.0 and bb_pos >= 0.35:
            reason = f"High-probability BEARISH Pullback SELL: Stoch_K={sk:.1f}, BB_Pos={bb_pos*100:.1f}%, Price=${price:.2f} near resistance"
            return True, "SELL", reason
        elif sk < 35.0 or bb_pos < 0.25:
            reason = f"Avoid selling into bottom: Market is oversold in downtrend (Stoch_K={sk:.1f}, BB_Pos={bb_pos*100:.1f}%). Waiting for pullback."
            return False, "WAIT", reason
        else:
            reason = f"Bearish trend consolidation (Stoch_K={sk:.1f}, BB_Pos={bb_pos*100:.1f}%). Waiting for pullback to SMA20/resistance."
            return False, "WAIT", reason

    # 2. BULLISH REGIME: Trade ONLY dips to buy (Trend is your friend)
    elif "bullish" in trend:
        # Dip into support (near SMA20 or lower half) + Stoch <= 40
        if sk <= 40.0 and bb_pos <= 0.65:
            reason = f"High-probability BULLISH Dip BUY: Stoch_K={sk:.1f}, BB_Pos={bb_pos*100:.1f}%, Price=${price:.2f} near support"
            return True, "BUY", reason
        elif sk > 65.0 or bb_pos > 0.75:
            reason = f"Avoid buying into top: Market is overbought in uptrend (Stoch_K={sk:.1f}, BB_Pos={bb_pos*100:.1f}%). Waiting for pullback."
            return False, "WAIT", reason
        else:
            reason = f"Bullish trend consolidation (Stoch_K={sk:.1f}, BB_Pos={bb_pos*100:.1f}%). Waiting for dip to SMA20/support."
            return False, "WAIT", reason

    # 3. SIDEWAYS / RANGE REGIME: Trade range boundaries
    else:
        if bb_pos >= 0.75 and sk >= 70.0:
            reason = f"Range resistance SELL: Stoch_K={sk:.1f}, BB_Pos={bb_pos*100:.1f}%, Price=${price:.2f}"
            return True, "SELL", reason
        elif bb_pos <= 0.25 and sk <= 30.0:
            reason = f"Range support BUY: Stoch_K={sk:.1f}, BB_Pos={bb_pos*100:.1f}%, Price=${price:.2f}"
            return True, "BUY", reason
        else:
            reason = f"Range mid-zone (Stoch_K={sk:.1f}, BB_Pos={bb_pos*100:.1f}%). Waiting for boundary test."
            return False, "WAIT", reason

