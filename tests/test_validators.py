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
    assert validate_trade_plan(plan, snapshot=mock_snapshot) == True


