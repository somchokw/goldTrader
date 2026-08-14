import logging
from typing import List, Dict
from curl_cffi import requests
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

def fetch_macro_data() -> Dict:
    """Fetch DXY and US 10Y Yield directly from TradingView Scanner API."""
    data = {}
    try:
        payload = {
            'symbols': {'tickers': ['TVC:DXY', 'TVC:US10Y'], 'query': {'types': []}},
            'columns': ['close']
        }
        r = requests.post(
            'https://scanner.tradingview.com/global/scan', 
            json=payload, 
            impersonate='chrome110',
            timeout=10
        )
        if r.status_code == 200:
            json_data = r.json()
            for item in json_data.get('data', []):
                symbol = item.get('s')
                close_price = item.get('d', [None])[0]
                
                if symbol == 'TVC:DXY':
                    data['dxy_close'] = float(close_price) if close_price else None
                elif symbol == 'TVC:US10Y':
                    data['us10y_yield'] = float(close_price) if close_price else None
        else:
            logger.error(f"TradingView Scanner returned status {r.status_code}")
            data['dxy_close'] = None
            data['us10y_yield'] = None
            
    except Exception as e:
        logger.error(f"Error fetching macro data from TradingView: {e}")
        data['error'] = str(e)
        
    return data

def fetch_gold_news() -> str:
    """Fetch latest gold news from Investing.com RSS feed."""
    try:
        r = requests.get(
            'https://www.investing.com/rss/news_11.rss',
            impersonate='chrome110',
            timeout=10
        )
        
        if r.status_code != 200:
            return "ไม่สามารถโหลดข่าวสารล่าสุดได้ในขณะนี้"
            
        root = ET.fromstring(r.text)
        news_items = []
        
        for item in root.findall('./channel/item')[:5]:
            title = item.find('title').text if item.find('title') is not None else "No Title"
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            
            # Format pubDate if necessary, but Investing.com gives standard RSS format
            news_items.append(f"• {title}\n  Date: {pub_date}\n  URL: {link}\n")
            
        if not news_items:
             return "No valid news titles found."
             
        news_summary = "\n".join([f"{idx+1}. {txt}" for idx, txt in enumerate(news_items)])
        return f"ข่าวล่าสุดเกี่ยวกับทองคำ (อ้างอิงจาก Investing.com):\n{news_summary}"
        
    except Exception as e:
        logger.error(f"Error fetching gold news from RSS: {e}")
        return f"Error fetching news: {e}"
