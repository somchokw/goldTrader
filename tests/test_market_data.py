import pytest
from unittest.mock import patch, MagicMock
from market_data import fetch_gold_news

@patch("market_data.yf.Ticker")
def test_fetch_gold_news_new_schema(mock_ticker):
    mock_gold = MagicMock()
    # New yfinance schema puts stuff inside 'content'
    mock_gold.news = [
        {
            "content": {
                "title": "Gold hits record high",
                "provider": {"displayName": "Reuters"},
                "pubDate": "2024-01-01T12:00:00Z",
                "clickThroughUrl": "http://example.com/news1"
            }
        }
    ]
    mock_ticker.return_value = mock_gold
    
    result = fetch_gold_news()
    assert "Gold hits record high" in result
    assert "Reuters" in result
    assert "http://example.com/news1" in result

@patch("market_data.yf.Ticker")
def test_fetch_gold_news_old_schema(mock_ticker):
    mock_gold = MagicMock()
    # Old yfinance schema
    mock_gold.news = [
        {
            "title": "Gold price falls",
            "publisher": "Bloomberg",
            "pubDate": "2024-01-02T12:00:00Z",
            "link": "http://example.com/news2"
        }
    ]
    mock_ticker.return_value = mock_gold
    
    result = fetch_gold_news()
    assert "Gold price falls" in result
    assert "Bloomberg" in result
    assert "http://example.com/news2" in result

@patch("market_data.yf.Ticker")
def test_fetch_gold_news_no_title(mock_ticker):
    mock_gold = MagicMock()
    # Malformed news
    mock_gold.news = [
        {
            "content": {
                "provider": {"displayName": "Reuters"},
                "pubDate": "2024-01-01T12:00:00Z",
                "clickThroughUrl": "http://example.com/news1"
            }
        }
    ]
    mock_ticker.return_value = mock_gold
    
    result = fetch_gold_news()
    assert "No valid news titles found" in result
