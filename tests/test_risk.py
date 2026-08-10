import pytest
from risk import calculate_lot_size
import config

def test_calculate_lot_size_safe():
    # Balance $1000, Risk 1% = $10
    # Entry $2300, SL $2290 -> Risk per oz = $10
    # Risk per standard lot = $10 * 100 = $1000
    # Raw Lot = 10 / 1000 = 0.01
    
    config.CONTRACT_SIZE = 100.0
    config.LOT_STEP = 0.01
    config.MIN_LOT = 0.01
    
    lot = calculate_lot_size(1000.0, 1.0, 2300.0, 2290.0)
    assert lot == 0.01

def test_calculate_lot_size_sniper():
    # Balance $100, Risk 50% = $50
    # Entry $2344, SL $2339.5 = $4.5
    # Risk per standard lot = $4.5 * 100 = $450
    # Raw Lot = 50 / 450 = 0.1111... -> rounded down to 0.11
    
    lot = calculate_lot_size(100.0, 50.0, 2344.0, 2339.5)
    assert lot == 0.11

def test_calculate_lot_size_too_small():
    # Balance 100, Risk 1% = 1
    # Risk per lot = 450
    # Raw = 1 / 450 = 0.0022 -> less than 0.01 -> 0
    
    lot = calculate_lot_size(100.0, 1.0, 2344.0, 2339.5)
    assert lot == 0.0
