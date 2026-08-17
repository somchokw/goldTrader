import pytest
from unittest.mock import patch, MagicMock
from market_data import fetch_gold_news, fetch_macro_data

@patch("market_data._fetch_rss_news")
def test_fetch_gold_news_success(mock_fetch):
    mock_fetch.return_value = [
        "• Gold hits record high\n  Date: 2026-08-18\n  URL: http://example.com/gold1\n"
    ]
    result = fetch_gold_news()
    assert "Gold hits record high" in result
    assert "http://example.com/gold1" in result

@patch("market_data._fetch_rss_news")
def test_fetch_gold_news_fallback_when_first_empty(mock_fetch):
    # First call returns empty, second call returns news
    mock_fetch.side_effect = [
        [],
        ["• Gold surges on inflation data\n  Date: 2026-08-18\n  URL: http://example.com/gold2\n"]
    ]
    result = fetch_gold_news()
    assert "Gold surges on inflation data" in result

@patch("market_data._fetch_rss_news")
def test_fetch_gold_news_all_failed(mock_fetch):
    mock_fetch.return_value = []
    result = fetch_gold_news()
    assert "ไม่สามารถโหลดข่าวสารล่าสุดได้ในขณะนี้" in result

@patch("market_data.requests.post")
def test_fetch_macro_data_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {"s": "TVC:DXY", "d": [104.5]},
            {"s": "TVC:US10Y", "d": [4.25]}
        ]
    }
    mock_post.return_value = mock_resp
    data = fetch_macro_data()
    assert data.get("dxy_close") == 104.5
    assert data.get("us10y_yield") == 4.25
