import pytest
from validators import validate_trade_plan
from models import TradePlan

def test_validate_buy_plan():
    plan = TradePlan(
        action="BUY",
        exact_entry_price=2000.0,
        stop_loss=1990.0,
        take_profit_1=2020.0,
        rationale="Test"
    )
    assert validate_trade_plan(plan) == True
    
def test_validate_buy_plan_invalid_sl():
    # SL is above entry
    plan = TradePlan(
        action="BUY",
        exact_entry_price=2000.0,
        stop_loss=2010.0,
        take_profit_1=2020.0,
        rationale="Test"
    )
    assert validate_trade_plan(plan) == False

def test_validate_sell_plan():
    plan = TradePlan(
        action="SELL",
        exact_entry_price=2000.0,
        stop_loss=2010.0,
        take_profit_1=1980.0,
        rationale="Test"
    )
    assert validate_trade_plan(plan) == True

def test_validate_rr_ratio():
    # Risk = 10, Reward = 12, RR = 1.2 (Less than 1.5 minimum)
    plan = TradePlan(
        action="BUY",
        exact_entry_price=2000.0,
        stop_loss=1990.0,
        take_profit_1=2012.0,
        rationale="Test"
    )
    assert validate_trade_plan(plan) == False

def test_validate_counter_trend_buy_in_bearish():
    from unittest.mock import MagicMock
    plan = TradePlan(
        action="BUY",
        exact_entry_price=2000.0,
        stop_loss=1990.0,
        take_profit_1=2020.0,
        rationale="Test"
    )
    mock_snapshot = MagicMock()
    mock_snapshot.trend_structure = "Bearish"
    assert validate_trade_plan(plan, snapshot=mock_snapshot) == False

def test_validate_counter_trend_sell_in_bullish():
    from unittest.mock import MagicMock
    plan = TradePlan(
        action="SELL",
        exact_entry_price=2000.0,
        stop_loss=2010.0,
        take_profit_1=1980.0,
        rationale="Test"
    )
    mock_snapshot = MagicMock()
    mock_snapshot.trend_structure = "Bullish"
    assert validate_trade_plan(plan, snapshot=mock_snapshot) == False

def test_validate_trend_following_sell():
    from unittest.mock import MagicMock
    plan = TradePlan(
        action="SELL",
        exact_entry_price=2000.0,
        stop_loss=2010.0,
        take_profit_1=1980.0,
        rationale="Test"
    )
    mock_snapshot = MagicMock()
    mock_snapshot.trend_structure = "Bearish"
    mock_snapshot.htf_trend_1h = "Bearish"
    mock_snapshot.adx = 26.0
    assert validate_trade_plan(plan, snapshot=mock_snapshot) == True

def test_validate_htf_alignment_sell_rejected_when_htf_bullish():
    from unittest.mock import MagicMock
    plan = TradePlan(
        action="SELL",
        exact_entry_price=2000.0,
        stop_loss=2010.0,
        take_profit_1=1980.0,
        rationale="Test"
    )
    mock_snapshot = MagicMock()
    mock_snapshot.trend_structure = "Bearish"  # 15m is bearish
    mock_snapshot.htf_trend_1h = "Bullish"     # But 1H is bullish!
    assert validate_trade_plan(plan, snapshot=mock_snapshot) == False

def test_validate_htf_alignment_buy_rejected_when_htf_bearish():
    from unittest.mock import MagicMock
    plan = TradePlan(
        action="BUY",
        exact_entry_price=2000.0,
        stop_loss=1990.0,
        take_profit_1=2020.0,
        rationale="Test"
    )
    mock_snapshot = MagicMock()
    mock_snapshot.trend_structure = "Bullish"  # 15m is bullish
    mock_snapshot.htf_trend_1h = "Bearish"    # But 1H is bearish!
    assert validate_trade_plan(plan, snapshot=mock_snapshot) == False

def test_validate_adx_low_rejected():
    from unittest.mock import MagicMock
    plan = TradePlan(
        action="BUY",
        exact_entry_price=2000.0,
        stop_loss=1990.0,
        take_profit_1=2020.0,
        rationale="Test"
    )
    mock_snapshot = MagicMock()
    mock_snapshot.trend_structure = "Bullish"
    mock_snapshot.htf_trend_1h = "Bullish"
    mock_snapshot.adx = 17.5  # Below 20 threshold
    assert validate_trade_plan(plan, snapshot=mock_snapshot) == False



