import logging
from typing import List, Dict
import xml.etree.ElementTree as ET
try:
    from curl_cffi import requests
except ImportError:
    import requests

logger = logging.getLogger(__name__)

def _get_request(url: str, **kwargs):
    """Helper to perform GET requests with curl_cffi impersonation if available."""
    headers = kwargs.pop('headers', {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    timeout = kwargs.pop('timeout', 10)
    req_kwargs = {'headers': headers, 'timeout': timeout, **kwargs}
    try:
        post_func = getattr(requests, 'get', None)
        if post_func and hasattr(post_func, '__code__') and 'impersonate' in getattr(post_func.__code__, 'co_varnames', ()):
            req_kwargs['impersonate'] = 'chrome110'
    except Exception:
        pass
    return requests.get(url, **req_kwargs)

def _post_request(url: str, **kwargs):
    """Helper to perform POST requests with curl_cffi impersonation if available."""
    headers = kwargs.pop('headers', {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    timeout = kwargs.pop('timeout', 10)
    req_kwargs = {'headers': headers, 'timeout': timeout, **kwargs}
    try:
        post_func = getattr(requests, 'post', None)
        if post_func and hasattr(post_func, '__code__') and 'impersonate' in getattr(post_func.__code__, 'co_varnames', ()):
            req_kwargs['impersonate'] = 'chrome110'
    except Exception:
        pass
    return requests.post(url, **req_kwargs)

def fetch_macro_data() -> Dict:
    """Fetch DXY and US 10Y Yield directly from TradingView Scanner API."""
    data = {}
    try:
        payload = {
            'symbols': {'tickers': ['TVC:DXY', 'TVC:US10Y'], 'query': {'types': []}},
            'columns': ['close']
        }
        r = _post_request('https://scanner.tradingview.com/global/scan', json=payload, timeout=10)
        if r.status_code == 200:
            json_data = r.json()
            for item in json_data.get('data', []):
                symbol = item.get('s')
                close_price = item.get('d', [None])[0]
                
                if symbol == 'TVC:DXY':
                    data['dxy_close'] = float(close_price) if close_price is not None else None
                elif symbol == 'TVC:US10Y':
                    data['us10y_yield'] = float(close_price) if close_price is not None else None
        else:
            logger.error(f"TradingView Scanner returned status {r.status_code}")
            data['dxy_close'] = None
            data['us10y_yield'] = None
            
    except Exception as e:
        logger.error(f"Error fetching macro data from TradingView: {e}")
        data['error'] = str(e)
        
    return data

def _fetch_rss_news(url: str, source_name: str) -> List[str]:
    """Helper to fetch and parse RSS feeds."""
    try:
        r = _get_request(url, timeout=10)
        if r.status_code != 200:
            logger.warning(f"Failed to fetch RSS from {source_name}, status: {r.status_code}")
            return []

        root = ET.fromstring(r.text)
        news_items = []
        for item in root.findall('./channel/item')[:5]:
            title = item.find('title').text if item.find('title') is not None else "No Title"
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            news_items.append(f"• {title}\n  Date: {pub_date}\n  URL: {link}\n")
            
        return news_items
    except Exception as e:
        logger.warning(f"Error parsing RSS from {source_name}: {e}")
        return []

def fetch_gold_news() -> str:
    """Fetch real-time gold news for today with multi-source fallback (Google News RSS 1d & FXStreet RSS)."""
    # Source 1: Google News RSS for Gold / XAUUSD from the last 24 hours
    try:
        news_items = _fetch_rss_news(
            'https://news.google.com/rss/search?q=gold+price+OR+XAUUSD+when:1d&hl=en-US&gl=US&ceid=US:en',
            'Google News (Today)'
        )
        if news_items:
            news_summary = "\n".join([f"{idx+1}. {txt}" for idx, txt in enumerate(news_items)])
            return f"ข่าวราคาทองคำล่าสุดประจำวันนี้ (Google News):\n{news_summary}"
    except Exception as e:
        logger.warning(f"Error fetching gold news from Google News RSS: {e}")

    # Source 2: FXStreet Gold News RSS
    try:
        news_items = _fetch_rss_news(
            'https://www.fxstreet.com/rss/news',
            'FXStreet'
        )
        # Filter for gold/XAU/dollar mentions
        gold_items = [item for item in news_items if any(k in item.lower() for k in ['gold', 'xau', 'dollar', 'fed', 'treasury'])]
        if gold_items:
            news_summary = "\n".join([f"{idx+1}. {txt}" for idx, txt in enumerate(gold_items[:5])])
            return f"ข่าวการเงินและทองคำล่าสุด (FXStreet):\n{news_summary}"
    except Exception as e:
        logger.warning(f"Error fetching gold news from FXStreet RSS: {e}")

    # Source 3: Google News 2-Day Fallback
    try:
        news_items = _fetch_rss_news(
            'https://news.google.com/rss/search?q=gold+price+OR+XAUUSD+when:2d&hl=en-US&gl=US&ceid=US:en',
            'Google News (48h)'
        )
        if news_items:
            news_summary = "\n".join([f"{idx+1}. {txt}" for idx, txt in enumerate(news_items)])
            return f"ข่าวราคาทองคำล่าสุด (Google News):\n{news_summary}"
    except Exception as e:
        logger.warning(f"Error fetching 2-day gold news: {e}")

    return "ไม่สามารถโหลดข่าวสารล่าสุดได้ในขณะนี้"
