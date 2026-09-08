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

