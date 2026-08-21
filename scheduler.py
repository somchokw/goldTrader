import time
import schedule
import logging
from datetime import datetime
from agents import create_gold_crew
from validators import validate_trade_plan
from risk import generate_risk_matrix
from notifications import send_discord_notify
from config import GEMINI_API_KEY, SYMBOL, LLM_MODEL

logger = logging.getLogger(__name__)

def run_trading_cycle(is_routine: bool = False):
    cycle_type = "Routine Update" if is_routine else "Sniper Scanner"
    logger.info(f"Starting Trading Cycle ({cycle_type}) for {SYMBOL}...")
    
    candidate_models = [
        LLM_MODEL,
        "gemini/gemini-2.0-flash",
        "gemini/gemini-2.5-flash",
        "gemini/gemini-1.5-flash-latest",
        "gemini/gemini-1.5-flash-002",
        "gemini/gemini-1.5-flash-001",
        "gemini/gemini-flash-latest"
    ]
    models_to_try = []
    for m in candidate_models:
        if m and m not in models_to_try:
            models_to_try.append(m)

    trade_plan = None
    last_error = None

    for model_name in models_to_try:
        try:
            logger.info(f"Running trading cycle with model: {model_name}")
            crew = create_gold_crew(model_name=model_name)
            result = crew.kickoff()
            
            # CrewAI 0.28+ returns a CrewOutput object. The pydantic output is in result.pydantic
            trade_plan = getattr(result, 'pydantic', None)
            if trade_plan:
                logger.info(f"Successfully generated TradePlan using {model_name}")
                break
        except Exception as e:
            last_error = e
            logger.warning(f"Error with model {model_name}: {e}. Trying fallback model...")
            continue
            
    try:
        if not trade_plan:
             logger.error(f"Failed to parse TradePlan from Agent output (all candidate models tried). Last error: {last_error}")
             send_discord_notify(f"❌ Exception in trading cycle: {last_error or 'Agent failed to return a valid TradePlan.'}")
             return None
             
        # Validate logic
        is_valid = validate_trade_plan(trade_plan)
        if not is_valid:
            logger.warning("Trade plan validation failed. Changing Action to WAIT.")
            trade_plan.action = "WAIT"
            
        # Skip Risk Matrix text generation as requested by user
        pass
        
        # Build Final Message
        if trade_plan.action == "WAIT":
            if not is_routine:
                logger.info("Trade plan is WAIT (Scanner). Skipping Discord notification to avoid spam.")
                return trade_plan
            else:
                # Routine update for WAIT
                final_message = f"📊 **Routine Market Update (ทุก 4 ชม.)**\n"
                final_message += f"**Symbol:** {SYMBOL}\n"
                final_message += f"**Action:** WAIT (รอสัญญาณ)\n\n"
                final_message += f"**Rationale:**\n{trade_plan.rationale}\n\n"
                final_message += "*หมายเหตุ: ระบบ Sniper Scanner จะคอยจับตาดูตลาดทุก 15 นาที หากมีจังหวะเข้าทำกำไร จะแจ้งเตือนทันทีครับ*"
                send_discord_notify(final_message)
                logger.info("Sent Routine WAIT update.")
                return trade_plan

        # It's a BUY/SELL signal
        final_message = f"🚨 **Trade Signal Detected!** 🚨\n\n" if not is_routine else f"📊 **Routine Market Update (มีสัญญาณเข้าเทรด!)**\n\n"
        final_message += f"**Trade Plan for {SYMBOL}** (Patch 1.6.6)\n"
        final_message += f"**Action:** {trade_plan.action}\n"
        if getattr(trade_plan, 'trade_style', None):
            final_message += f"**รูปแบบแผน:** {trade_plan.trade_style}\n"
        
        if trade_plan.action != "WAIT":
            final_message += f"**Entry:** {trade_plan.exact_entry_price}\n"
            final_message += f"**Stop Loss:** {trade_plan.stop_loss}\n"
            final_message += f"**Take Profit 1:** {trade_plan.take_profit_1}\n"
            if trade_plan.take_profit_2:
                final_message += f"**Take Profit 2:** {trade_plan.take_profit_2}\n"
                
        final_message += f"\n**Rationale:**\n{trade_plan.rationale}\n"
        
        final_message += "\n---\n**โปรดให้คะแนนความแม่นยำและเหตุผลของแผนนี้ (0-10) โดยพิมพ์ตัวเลขลงในช่องแชทได้เลยครับ** 👇"
        
        send_discord_notify(final_message)
        logger.info("Trading cycle completed successfully. Notification sent.")
        return trade_plan
        
    except Exception as e:
        logger.error(f"Error during trading cycle: {e}", exc_info=True)
        send_discord_notify(f"❌ Exception in trading cycle: {e}")
        return None

def _run_scanner():
    run_trading_cycle(is_routine=False)

def _run_routine():
    run_trading_cycle(is_routine=True)

def start_scheduler():
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is missing! Fail fast.")
        exit(1)
        
    logger.info("=== Gold Trading Bot Started ===")
    
    # Run routine once immediately
    _run_routine()
    
    # Schedule Sniper Scanner every 15 minutes
    schedule.every(15).minutes.do(_run_scanner)
    
    # Schedule Routine Report every 4 hours
    schedule.every(4).hours.do(_run_routine)
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Graceful shutdown requested. Exiting.")
