import time
import schedule
import logging
from datetime import datetime, timezone
from agents import create_gold_crew
from validators import validate_trade_plan
from risk import generate_risk_matrix
from notifications import send_discord_notify
from config import (
    GEMINI_API_KEY, SYMBOL, LLM_MODEL,
    MAX_DAILY_SIGNALS, SIGNAL_COOLDOWN_MINUTES, MIN_PRICE_CHANGE_FOR_NEW_SIGNAL
)
from indicators import fetch_technical_data, evaluate_market_readiness

logger = logging.getLogger(__name__)

# Daily Quota & Anti-Spam Tracking State (Patch 1.7.3)
daily_signals_sent = 0
last_signal_date = None
last_signal_time = None
last_signal_price = None
last_signal_action = None

def get_quota_status() -> dict:
    """Returns the current day's signal quota and cooldown status."""
    global daily_signals_sent, last_signal_date, last_signal_time, last_signal_price, last_signal_action
    current_date = datetime.now(timezone.utc).date()
    if last_signal_date != current_date:
        daily_signals_sent = 0
        last_signal_date = current_date
    return {
        "sent": daily_signals_sent,
        "max": MAX_DAILY_SIGNALS,
        "remaining": max(0, MAX_DAILY_SIGNALS - daily_signals_sent),
        "last_time": last_signal_time.isoformat() if last_signal_time else None,
        "last_price": last_signal_price,
        "last_action": last_signal_action
    }

def run_trading_cycle(is_routine: bool = False):
    global daily_signals_sent, last_signal_date, last_signal_time, last_signal_price, last_signal_action

    current_time = datetime.now(timezone.utc)
    current_date = current_time.date()
    if last_signal_date != current_date:
        daily_signals_sent = 0
        last_signal_date = current_date
        logger.info(f"New trading day ({current_date}). Reset daily quota to 0/{MAX_DAILY_SIGNALS}.")

    cycle_type = "Routine Update" if is_routine else "Sniper Scanner"
    logger.info(f"Starting Trading Cycle ({cycle_type}) for {SYMBOL}. Quota today: {daily_signals_sent}/{MAX_DAILY_SIGNALS}")

    # 1. Daily Quota Cap (Max 10 signals per day)
    if daily_signals_sent >= MAX_DAILY_SIGNALS:
        msg = f"Daily signal limit reached ({daily_signals_sent}/{MAX_DAILY_SIGNALS}). Skipping cycle to protect capital and API quota."
        logger.info(msg)
        if is_routine:
            send_discord_notify(
                f"📊 **Routine Market Update**\n\n"
                f"📌 โควต้าสัญญาณรายวันครบ {daily_signals_sent}/{MAX_DAILY_SIGNALS} ไม้แล้วครับ เพื่อบริหารความเสี่ยงและรักษาเงินทุน ระบบจะเริ่มส่งสัญญาณใหม่อีกครั้งในวันพรุ่งนี้"
            )
        return None

    # 2. Fetch Live Technical Data (Free - Kraken/TradingView, zero LLM credit)
    snapshot = fetch_technical_data("15m")
    current_price = snapshot.close_price if snapshot else None

    # 3. Cooldown & Price Movement Anti-Spam Filter
    if last_signal_time is not None:
        elapsed_minutes = (current_time - last_signal_time).total_seconds() / 60.0
        if elapsed_minutes < SIGNAL_COOLDOWN_MINUTES:
            price_change = abs(current_price - last_signal_price) if (current_price and last_signal_price) else 999.0
            if price_change < MIN_PRICE_CHANGE_FOR_NEW_SIGNAL:
                logger.info(
                    f"Cooldown active ({elapsed_minutes:.1f}m < {SIGNAL_COOLDOWN_MINUTES}m) and price change (${price_change:.2f} < ${MIN_PRICE_CHANGE_FOR_NEW_SIGNAL:.2f}). "
                    f"Skipping cycle to prevent spamming duplicate trades."
                )
                return None

    # 4. Quantitative Pre-Filter (Zero-Cost LLM Saver)
    if not is_routine:
        if not snapshot:
            logger.warning("No technical snapshot available for pre-filter. Skipping scanner cycle.")
            return None
            
        is_ready, bias, readiness_reason = evaluate_market_readiness(snapshot)
        if not is_ready:
            logger.info(f"Pre-filter check: NOT READY ({readiness_reason}). Skipping LLM to save quota.")
            return None
        logger.info(f"Pre-filter PASSED: Suggested bias = {bias} ({readiness_reason}). Invoking CrewAI...")
    
    candidate_models = [
        LLM_MODEL,
        "gemini/gemini-3.6-flash",
        "gemini/gemini-3.5-flash",
        "gemini/gemini-flash-latest",
        "gemini/gemini-3.1-pro-preview"
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
            err_str = str(e)
            if "503" in err_str or "UNAVAILABLE" in err_str or "high demand" in err_str.lower():
                logger.warning(f"Model {model_name} is experiencing temporary 503 high demand spike. Waiting 2s before fallback...")
                time.sleep(2)
            else:
                logger.warning(f"Error with model {model_name}: {e}. Trying fallback model...")
            continue
            
    try:
        if not trade_plan:
             logger.error(f"Failed to parse TradePlan from Agent output (all candidate models tried). Last error: {last_error}")
             send_discord_notify(f"❌ Exception in trading cycle: {last_error or 'Agent failed to return a valid TradePlan.'}")
             return None
             
        # Validate logic (Enforces MIN_RR_RATIO >= 1.5 and SL >= $5.0)
        is_valid = validate_trade_plan(trade_plan)
        if not is_valid:
            logger.warning("Trade plan validation failed. Changing Action to WAIT.")
            trade_plan.action = "WAIT"
            
        # Build Final Message
        if trade_plan.action == "WAIT":
            if not is_routine:
                logger.info("Trade plan is WAIT (Scanner). Skipping Discord notification to avoid spam.")
                return trade_plan
            else:
                # Routine update for WAIT
                final_message = f"📊 **Routine Market Update (ทุก 4 ชม.)**\n"
                final_message += f"**Symbol:** {SYMBOL}\n"
                final_message += f"**Action:** WAIT (รอสัญญาณที่มีแต้มต่อสูง Win Rate ≥ 70%)\n"
                final_message += f"**Quota วันนี้:** {daily_signals_sent}/{MAX_DAILY_SIGNALS} ไม้\n\n"
                final_message += f"**Rationale:**\n{trade_plan.rationale}\n\n"
                final_message += "*หมายเหตุ: ระบบ Sniper Scanner จะคอยจับตาดูตลาดทุก 15 นาที หากมีจังหวะเข้าทำกำไร จะแจ้งเตือนทันทีครับ*"
                send_discord_notify(final_message)
                logger.info("Sent Routine WAIT update.")
                return trade_plan

        # It's a BUY/SELL signal!
        risk = abs(trade_plan.exact_entry_price - trade_plan.stop_loss)
        reward = abs(trade_plan.take_profit_1 - trade_plan.exact_entry_price)
        rr_ratio = reward / risk if risk > 0 else 0.0

        daily_signals_sent += 1
        last_signal_time = current_time
        last_signal_price = trade_plan.exact_entry_price
        last_signal_action = trade_plan.action

        final_message = f"🚨 **High-Conviction Sniper Signal!** 🚨\n\n" if not is_routine else f"📊 **Routine Market Update (มีสัญญาณเข้าเทรด!)**\n\n"
        final_message += f"**Trade Plan for {SYMBOL}** (Patch 1.7.3)\n"
        final_message += f"**Action:** {trade_plan.action}\n"
        final_message += f"**Quota วันนี้:** [ไม้ที่ {daily_signals_sent}/{MAX_DAILY_SIGNALS}]\n"
        if getattr(trade_plan, 'trade_style', None):
            final_message += f"**รูปแบบแผน:** {trade_plan.trade_style}\n"
        
        final_message += f"**Entry:** ${trade_plan.exact_entry_price:.2f}\n"
        final_message += f"**Stop Loss:** ${trade_plan.stop_loss:.2f} (ห่าง ${risk:.2f})\n"
        final_message += f"**Take Profit 1:** ${trade_plan.take_profit_1:.2f} (เป้า +${reward:.2f})\n"
        if trade_plan.take_profit_2:
            final_message += f"**Take Profit 2:** ${trade_plan.take_profit_2:.2f}\n"
        final_message += f"**Risk/Reward Ratio:** 1 : {rr_ratio:.2f} (เป้าหมาย Win Rate ≥ 70%)\n"
            
        final_message += f"\n**Rationale:**\n{trade_plan.rationale}\n"
        final_message += "\n---\n**โปรดให้คะแนนความแม่นยำและเหตุผลของแผนนี้ (0-10) โดยพิมพ์ตัวเลขลงในช่องแชทได้เลยครับ** 👇"
        
        send_discord_notify(final_message)
        logger.info(f"Trading signal sent successfully ({daily_signals_sent}/{MAX_DAILY_SIGNALS}).")
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
