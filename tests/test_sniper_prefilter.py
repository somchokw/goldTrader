import pytest
from datetime import datetime, timezone
from models import MarketSnapshot
from indicators import evaluate_market_readiness
from scheduler import get_quota_status

def test_market_readiness_none():
    ready, bias, reason = evaluate_market_readiness(None)
    assert ready is False
    assert bias == "WAIT"

def test_market_readiness_bearish_pullback_sell():
    # Downtrend, price pulled back up to SMA20 / upper BB, Stoch >= 65 -> high probability SELL
    snapshot = MarketSnapshot(
        symbol="XAUUSD",
        timeframe="15m",
        timestamp=datetime.now(timezone.utc).isoformat(),
        close_price=4405.0,
        high_price=4410.0,
        low_price=4400.0,
        sma_20=4404.0,
        rsi_14=62.0,
        macd=-0.5,
        macd_signal=-0.8,
        bb_lower=4390.0,
        bb_upper=4415.0,
        atr=10.0,
        trend_structure="Bearish",
        stoch_k=75.0,
        stoch_d=70.0
    )
    ready, bias, reason = evaluate_market_readiness(snapshot)
    assert ready is True
    assert bias == "SELL"

def test_market_readiness_prevent_oversold_sell():
    # Downtrend, but price crashed into lower BB, Stoch is 15 -> DO NOT SELL BOTTOM!
    snapshot = MarketSnapshot(
        symbol="XAUUSD",
        timeframe="15m",
        timestamp=datetime.now(timezone.utc).isoformat(),
        close_price=4388.0,
        high_price=4395.0,
        low_price=4387.0,
        sma_20=4405.0,
        rsi_14=28.0,
        macd=-2.5,
        macd_signal=-1.8,
        bb_lower=4388.0,
        bb_upper=4420.0,
        atr=10.0,
        trend_structure="Bearish",
        stoch_k=18.0,
        stoch_d=22.0
    )
    ready, bias, reason = evaluate_market_readiness(snapshot)
    assert ready is False
    assert bias == "WAIT"
    assert "oversold" in reason.lower()

def test_market_readiness_bullish_dip_buy():
    # Uptrend, price dipped near SMA20 / lower BB, Stoch <= 35 -> high probability BUY
    snapshot = MarketSnapshot(
        symbol="XAUUSD",
        timeframe="15m",
        timestamp=datetime.now(timezone.utc).isoformat(),
        close_price=4402.0,
        high_price=4415.0,
        low_price=4400.0,
        sma_20=4403.0,
        rsi_14=38.0,
        macd=1.2,
        macd_signal=0.9,
        bb_lower=4395.0,
        bb_upper=4425.0,
        atr=10.0,
        trend_structure="Bullish",
        stoch_k=30.0,
        stoch_d=32.0
    )
    ready, bias, reason = evaluate_market_readiness(snapshot)
    assert ready is True
    assert bias == "BUY"

def test_market_readiness_prevent_overbought_buy():
    # Uptrend, but price is at upper BB peak, Stoch is 85 -> DO NOT BUY TOP!
    snapshot = MarketSnapshot(
        symbol="XAUUSD",
        timeframe="15m",
        timestamp=datetime.now(timezone.utc).isoformat(),
        close_price=4424.0,
        high_price=4426.0,
        low_price=4415.0,
        sma_20=4405.0,
        rsi_14=72.0,
        macd=2.8,
        macd_signal=2.1,
        bb_lower=4395.0,
        bb_upper=4425.0,
        atr=10.0,
        trend_structure="Bullish",
        stoch_k=85.0,
        stoch_d=80.0
    )
    ready, bias, reason = evaluate_market_readiness(snapshot)
    assert ready is False
    assert bias == "WAIT"
    assert "overbought" in reason.lower()

def test_quota_status():
    quota = get_quota_status()
    assert "sent" in quota
    assert quota["max"] == 10
    assert quota["remaining"] <= 10

def test_scheduler_quota_limit(monkeypatch):
    import scheduler
    scheduler.daily_signals_sent = 10
    scheduler.last_signal_date = datetime.now(timezone.utc).date()
    
    # Run cycle when quota is reached
    res = scheduler.run_trading_cycle(is_routine=False)
    assert res is None

def test_scheduler_cooldown_active(monkeypatch):
    import scheduler
    from unittest.mock import MagicMock
    
    scheduler.daily_signals_sent = 2
    scheduler.last_signal_date = datetime.now(timezone.utc).date()
    scheduler.last_signal_time = datetime.now(timezone.utc)
    scheduler.last_signal_price = 4400.0
    
    # Mock snapshot with price only $2 away (below 5.0 threshold)
    mock_snapshot = MagicMock()
    mock_snapshot.close_price = 4402.0
    monkeypatch.setattr(scheduler, "fetch_technical_data", lambda tf: mock_snapshot)
    
    res = scheduler.run_trading_cycle(is_routine=False)
    assert res is None

def test_market_readiness_htf_conflict_bearish_15m_bullish_1h():
    # 15m is Bearish, but 1H HTF is Bullish -> Must block SELL!
    snapshot = MarketSnapshot(
        symbol="XAUUSD",
        timeframe="15m",
        timestamp=datetime.now(timezone.utc).isoformat(),
        close_price=4405.0,
        high_price=4410.0,
        low_price=4400.0,
        sma_20=4404.0,
        rsi_14=62.0,
        macd=-0.5,
        macd_signal=-0.8,
        bb_lower=4390.0,
        bb_upper=4415.0,
        atr=10.0,
        trend_structure="Bearish",
        htf_trend_1h="Bullish",
        stoch_k=75.0,
        stoch_d=70.0,
        adx=30.0
    )
    ready, bias, reason = evaluate_market_readiness(snapshot)
    assert ready is False
    assert bias == "WAIT"
    assert "htf conflict" in reason.lower()

def test_market_readiness_htf_conflict_bullish_15m_bearish_1h():
    # 15m is Bullish, but 1H HTF is Bearish -> Must block BUY!
    snapshot = MarketSnapshot(
        symbol="XAUUSD",
        timeframe="15m",
        timestamp=datetime.now(timezone.utc).isoformat(),
        close_price=4402.0,
        high_price=4415.0,
        low_price=4400.0,
        sma_20=4403.0,
        rsi_14=38.0,
        macd=1.2,
        macd_signal=0.9,
        bb_lower=4395.0,
        bb_upper=4425.0,
        atr=10.0,
        trend_structure="Bullish",
        htf_trend_1h="Bearish",
        stoch_k=30.0,
        stoch_d=32.0,
        adx=28.0
    )
    ready, bias, reason = evaluate_market_readiness(snapshot)
    assert ready is False
    assert bias == "WAIT"
    assert "htf conflict" in reason.lower()

def test_market_readiness_adx_filter():
    # ADX < 20 (choppy sideways) -> Must block entry!
    snapshot = MarketSnapshot(
        symbol="XAUUSD",
        timeframe="15m",
        timestamp=datetime.now(timezone.utc).isoformat(),
        close_price=4405.0,
        high_price=4410.0,
        low_price=4400.0,
        sma_20=4404.0,
        rsi_14=62.0,
        macd=-0.5,
        macd_signal=-0.8,
        bb_lower=4390.0,
        bb_upper=4415.0,
        atr=10.0,
        trend_structure="Bearish",
        htf_trend_1h="Bearish",
        stoch_k=75.0,
        stoch_d=70.0,
        adx=16.5
    )
    ready, bias, reason = evaluate_market_readiness(snapshot)
    assert ready is False
    assert bias == "WAIT"
    assert "adx" in reason.lower()

def test_calculate_adx():
    import pandas as pd
    from indicators import calculate_adx
    
    # Strong upward trend
    high = pd.Series([10 + i for i in range(30)])
    low = pd.Series([8 + i for i in range(30)])
    close = pd.Series([9.5 + i for i in range(30)])
    df = pd.DataFrame({'High': high, 'Low': low, 'Close': close})
    
    adx_val, di_plus, di_minus = calculate_adx(df, period=14)
    assert adx_val > 25.0
    assert di_plus > di_minus

def test_detect_rsi_divergence():
    import pandas as pd
    from indicators import detect_rsi_divergence
    
    # Bearish divergence: price high 132 > 120, but RSI was 75 at 120 and 60 at 132
    c = pd.Series([100, 102, 105, 103, 108, 107, 110, 112, 115, 114, 116, 118, 120, 119, 118, 122, 121, 120, 125, 124, 123, 126, 125, 124, 128, 127, 129, 130, 131, 132])
    rsi = pd.Series([50]*12 + [75] + [65]*15 + [60, 58])
    res = detect_rsi_divergence(c, rsi, lookback=30)
    assert res == "Bearish Divergence"

def test_detect_candlestick_pattern():
    import pandas as pd
    from indicators import detect_candlestick_pattern
    
    df_pin = pd.DataFrame([
        {'Open': 100, 'High': 105, 'Low': 99, 'Close': 104},
        {'Open': 104, 'High': 115, 'Low': 103, 'Close': 105}
    ])
    res = detect_candlestick_pattern(df_pin)
    assert res == "Bearish Rejection Pin Bar"

def test_news_guard_active():
    from datetime import datetime, timezone
    from config import is_news_guard_active
    
    # 13:30 UTC on Wednesday (Weekday) -> Inside window (13:15 - 14:45)
    dt_active = datetime(2026, 9, 9, 13, 30, tzinfo=timezone.utc)
    assert is_news_guard_active(dt_active) is True
    
    # 12:00 UTC on Wednesday -> Outside window
    dt_inactive = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
    assert is_news_guard_active(dt_inactive) is False
    
    # 13:30 UTC on Saturday -> Weekend, should be inactive
    dt_weekend = datetime(2026, 9, 12, 13, 30, tzinfo=timezone.utc)
    assert is_news_guard_active(dt_weekend) is False

def test_directional_cooldown(monkeypatch):
    import scheduler
    from unittest.mock import MagicMock
    from datetime import datetime, timezone, timedelta
    
    now = datetime.now(timezone.utc)
    scheduler.daily_signals_sent = 1
    scheduler.last_signal_date = now.date()
    scheduler.last_signal_time = now - timedelta(minutes=30)  # 30 mins ago (< 90m)
    scheduler.last_signal_price = 4400.0
    scheduler.last_signal_action = "SELL"
    
    mock_snapshot = MagicMock()
    mock_snapshot.close_price = 4380.0  # Price moved significantly ($20)
    mock_snapshot.trend_structure = "Bearish"
    monkeypatch.setattr(scheduler, "fetch_technical_data", lambda tf: mock_snapshot)
    monkeypatch.setattr(scheduler, "evaluate_market_readiness", lambda snap: (True, "SELL", "Pullback SELL"))
    
    # Running cycle should be suppressed by Directional Cooldown for SELL
    res = scheduler.run_trading_cycle(is_routine=False)
    assert res is None


