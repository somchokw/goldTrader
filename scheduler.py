import time
import schedule
import logging
from datetime import datetime
from agents import create_gold_crew
from validators import validate_trade_plan
from risk import generate_risk_matrix
from notifications import send_discord_notify
from config import GEMINI_API_KEY, SYMBOL

logger = logging.getLogger(__name__)

def run_trading_cycle():
    logger.info(f"Starting Trading Cycle for {SYMBOL}...")
    try:
        crew = create_gold_crew()
        result = crew.kickoff()
        
        # CrewAI 0.28+ returns a CrewOutput object. The pydantic output is in result.pydantic
        trade_plan = getattr(result, 'pydantic', None)
        
        if not trade_plan:
             logger.error("Failed to parse TradePlan from Agent output.")
             send_discord_notify("❌ System Error: Agent failed to return a valid TradePlan.")
             return
             
        # Validate logic
        is_valid = validate_trade_plan(trade_plan)
        if not is_valid:
            logger.warning("Trade plan validation failed. Changing Action to WAIT.")
            trade_plan.action = "WAIT"
            
        # Calculate Risk Matrix
        risk_matrix_text = ""
        if trade_plan.action != "WAIT":
            matrix = generate_risk_matrix(trade_plan.exact_entry_price, trade_plan.stop_loss)
            
            risk_matrix_text = "\n### 🛡️ Risk Management (Deterministic Python Engine)\n"
            risk_matrix_text += f"* ระยะ Stop Loss: ${abs(trade_plan.exact_entry_price - trade_plan.stop_loss):.2f}/oz\n"
            
            risk_matrix_text += "\n**แบบที่ 1: Safe Mode (Risk 1%)**\n"
            for item in matrix["safe_mode"]:
                risk_matrix_text += f"- ทุน ${item['balance']} -> เปิด {item['lot_size']} Lots (เสี่ยง ${item['risk_amount']:.2f})\n"
                
            if matrix["sniper_mode"]:
                risk_matrix_text += "\n**แบบที่ 2: Sniper Mode (High Risk 50%)**\n"
                for item in matrix["sniper_mode"]:
                    risk_matrix_text += f"- ทุน ${item['balance']} -> เปิด {item['lot_size']} Lots (เสี่ยง ${item['risk_amount']:.2f})\n"
        
        # Build Final Message
        final_message = f"**Trade Plan for {SYMBOL}**\n\n"
        final_message += f"**Action:** {trade_plan.action}\n"
        
        if trade_plan.action != "WAIT":
            final_message += f"**Entry:** {trade_plan.exact_entry_price}\n"
            final_message += f"**Stop Loss:** {trade_plan.stop_loss}\n"
            final_message += f"**Take Profit 1:** {trade_plan.take_profit_1}\n"
            if trade_plan.take_profit_2:
                final_message += f"**Take Profit 2:** {trade_plan.take_profit_2}\n"
                
        final_message += f"\n**Rationale:**\n{trade_plan.rationale}\n"
        final_message += risk_matrix_text
        
        send_discord_notify(final_message)
        logger.info("Trading cycle completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during trading cycle: {e}", exc_info=True)
        send_discord_notify(f"❌ Exception in trading cycle: {e}")

def start_scheduler():
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is missing! Fail fast.")
        exit(1)
        
    logger.info("=== Gold Trading Bot Started ===")
    
    # Run once immediately
    run_trading_cycle()
    
    # Schedule every 4 hours
    schedule.every(4).hours.do(run_trading_cycle)
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Graceful shutdown requested. Exiting.")
