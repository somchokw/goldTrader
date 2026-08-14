import yfinance as yf
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

import sys
import io

def fetch_macro_data() -> Dict:
    """Fetch DXY and US 10Y Yield, suppressing Cloudflare HTML spam."""
    data = {}
    
    # Suppress stderr to hide Yahoo Finance Cloudflare HTML spam
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        # DXY (US Dollar Index)
        dxy = yf.Ticker("DX-Y.NYB")
        dxy_hist = dxy.history(period="1d")
        if not dxy_hist.empty:
            data['dxy_close'] = float(dxy_hist['Close'].iloc[-1])
        else:
            data['dxy_close'] = None
            
        # US 10-Year Treasury Yield (^TNX)
        tnx = yf.Ticker("^TNX")
        tnx_hist = tnx.history(period="1d")
        if not tnx_hist.empty:
            data['us10y_yield'] = float(tnx_hist['Close'].iloc[-1])
        else:
            data['us10y_yield'] = None
            
    except Exception as e:
        logger.error(f"Error fetching macro data (likely blocked): {e}")
        data['error'] = str(e)
    finally:
        sys.stderr = original_stderr
        
    return data

def fetch_gold_news() -> str:
    """Fetch latest gold news using new yfinance schema."""
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    try:
        gold = yf.Ticker("GC=F")
        news_items = gold.news
        if not news_items:
            return "ไม่มีข่าวสารล่าสุดในระบบ yfinance"
        
        news_summary = ""
        for idx, item in enumerate(news_items[:5], 1):
            # Support both old and new schema
            content = item.get("content", item)
            
            title = content.get("title", "No Title")
            provider = content.get("provider", {}).get("displayName", "Unknown") if isinstance(content.get("provider"), dict) else content.get("publisher", "Unknown")
            pub_date = content.get("pubDate", "")
            url = content.get("clickThroughUrl", content.get("link", ""))
            
            if title == "No Title":
                continue # Skip invalid items per spec
                
            news_summary += f"{idx}. {title}\n   Provider: {provider} | Date: {pub_date}\n   URL: {url}\n\n"
            
        if not news_summary:
             return "No valid news titles found."
             
        return f"ข่าวล่าสุดเกี่ยวกับทองคำ (อ้างอิงจากข้อมูลจริงเท่านั้น):\n{news_summary}"
    except Exception as e:
        logger.error(f"Error fetching gold news (likely blocked): {e}")
        return f"Error fetching news: {e}"
    finally:
        sys.stderr = original_stderr
