import logging
import math
from typing import List, Dict
from config import CONTRACT_SIZE, MIN_LOT, LOT_STEP, HIGH_RISK_MODE_ENABLED, DEFAULT_RISK_PERCENT, HIGH_RISK_PERCENT

logger = logging.getLogger(__name__)

def calculate_lot_size(balance: float, risk_percent: float, entry: float, stop_loss: float) -> float:
    risk_amount = balance * (risk_percent / 100.0)
    risk_per_unit = abs(entry - stop_loss)
    
    if risk_per_unit == 0:
        return 0.0
        
    risk_per_lot = risk_per_unit * CONTRACT_SIZE
    
    if risk_per_lot == 0:
         return 0.0
         
    raw_lot = risk_amount / risk_per_lot
    
    # Round down to nearest LOT_STEP
    lot_multiplier = 1.0 / LOT_STEP
    lot_size = math.floor(raw_lot * lot_multiplier) / lot_multiplier
    
    if lot_size < MIN_LOT:
        return 0.0
        
    return lot_size

def generate_risk_matrix(entry: float, stop_loss: float) -> Dict:
    matrix = {
        "safe_mode": [],
        "sniper_mode": []
    }
    
    # Safe Mode (1-2%)
    safe_balances = [1000.0, 3000.0, 5000.0]
    for bal in safe_balances:
        lot = calculate_lot_size(bal, DEFAULT_RISK_PERCENT, entry, stop_loss)
        risk_amt = bal * (DEFAULT_RISK_PERCENT / 100.0)
        matrix["safe_mode"].append({"balance": bal, "lot_size": lot, "risk_amount": risk_amt})
        
    # Sniper Mode (50%) - Feature Flag
    if HIGH_RISK_MODE_ENABLED:
        sniper_balances = [30.0, 50.0, 100.0]
        for bal in sniper_balances:
            lot = calculate_lot_size(bal, HIGH_RISK_PERCENT, entry, stop_loss)
            risk_amt = bal * (HIGH_RISK_PERCENT / 100.0)
            matrix["sniper_mode"].append({"balance": bal, "lot_size": lot, "risk_amount": risk_amt})
            
    return matrix
