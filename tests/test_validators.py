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
    # Risk = 10, Reward = 10, RR = 1.0 (Less than 1.5 minimum)
    plan = TradePlan(
        action="BUY",
        exact_entry_price=2000.0,
        stop_loss=1990.0,
        take_profit_1=2010.0,
        rationale="Test"
    )
    assert validate_trade_plan(plan) == False
