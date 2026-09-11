import os
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
    MAX_DAILY_SIGNALS, SIGNAL_COOLDOWN_MINUTES, DIRECTIONAL_COOLDOWN_MINUTES,
    MIN_PRICE_CHANGE_FOR_NEW_SIGNAL, is_news_guard_active
)
from indicators import fetch_technical_data, evaluate_market_readiness

logger = logging.getLogger(__name__)

# Daily Quota & Anti-Spam Tracking State (Patch 1.7.3 & 1.8.0)
daily_signals_sent = 0
last_signal_date = None
last_signal_time = None
last_signal_price = None
last_signal_action = None
credit_exhaustion_notified = False

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
    global daily_signals_sent, last_signal_date, last_signal_time, last_signal_price, last_signal_action, credit_exhaustion_notified

    current_time = datetime.now(timezone.utc)
    current_date = current_time.date()
    if last_signal_date != current_date:
        daily_signals_sent = 0
        last_signal_date = current_date
        logger.info(f"New trading day ({current_date}). Reset daily quota to 0/{MAX_DAILY_SIGNALS}.")

    # 0. US High-Impact News & NY Open Volatility Guard (20:15 - 21:45 Thai time)
    if is_news_guard_active(current_time):
        logger.info(
            "US High-Impact News & Market Open Volatility Guard is ACTIVE (13:15-14:45 UTC / 20:15-21:45 TH). "
            "Suppressing new signal entries to protect capital against stop hunts and liquidity spikes."
        )
        return None

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

    # 4. Quantitative Pre-Filter (Zero-Cost LLM Saver & Quality Enforcer)
    if not snapshot:
        logger.warning("No technical snapshot available. Skipping trading cycle.")
        return None

    is_ready, bias, readiness_reason = evaluate_market_readiness(snapshot)
    if not is_ready:
        logger.info(f"Market pre-filter: NOT READY ({readiness_reason}). Staying silent.")
        return None

    # 5. Anti-Revenge Directional Cooldown: Do not issue same-direction trade within 90 minutes
    if last_signal_action and last_signal_action == bias and last_signal_time is not None:
        dir_elapsed = (current_time - last_signal_time).total_seconds() / 60.0
        if dir_elapsed < DIRECTIONAL_COOLDOWN_MINUTES:
            logger.info(
                f"Directional Cooldown active for {bias} ({dir_elapsed:.1f}m < {DIRECTIONAL_COOLDOWN_MINUTES}m). "
                f"Suppressing duplicate {bias} trade to prevent doubling down on a losing trend."
            )
            return None

    logger.info(f"Pre-filter PASSED: Suggested bias = {bias} ({readiness_reason}). Invoking CrewAI...")
    
    candidate_models = [
        LLM_MODEL,
        "gemini/gemini-3.6-flash",
        "gemini/gemini-3.5-flash",
        "gemini/gemini-flash-latest",
        "gemini/gemini-3.1-pro-preview"
    ]
    if os.environ.get("DEEPSEEK_API_KEY"):
        candidate_models.append("deepseek/deepseek-chat")
    if os.environ.get("OPENAI_API_KEY"):
        candidate_models.append("openai/gpt-4o-mini")

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
                credit_exhaustion_notified = False
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
            err_str = str(last_error or '')
            logger.error(f"Failed to parse TradePlan from Agent output (all candidate models tried). Last error: {last_error}")
            
            # Graceful Credit Depletion / Quota Exhaustion Alert
            if "prepayment credits are depleted" in err_str or "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                if not credit_exhaustion_notified:
                    credit_exhaustion_notified = True
                    notice = (
                        "⚠️ **Gemini API Credit Alert** ⚠️\n\n"
                        "ยอดเครดิตใน Google AI Studio / Gemini API ของโปรเจกต์หมดลงแล้วครับ (`Prepayment credits are depleted`)\n\n"
                        "**วิธีแก้ไข (เลือกอย่างใดอย่างหนึ่ง):**\n"
                        "1. **เติมเครดิต:** เข้าไปเติมเงินที่ https://aistudio.google.com/ หรือ Google Cloud Billing\n"
                        "2. **เปลี่ยน API Key ฟรี:** สร้าง Key ใหม่จาก Google Account อื่น (Free Tier) แล้วนำมาอัปเดตใน Environment Variable `GEMINI_API_KEY` บน Render\n"
                        "3. **ใช้โมเดลอื่น:** ใส่ `DEEPSEEK_API_KEY` หรือ `OPENAI_API_KEY` ใน Render เพื่อให้ระบบสลับไปใช้ DeepSeek/OpenAI โดยอัตโนมัติ\n\n"
                        "*หมายเหตุ: ระบบจะพักการแจ้งเตือน Error นี้ไว้ ไม่ส่งซ้ำจนกว่าจะมีการเปลี่ยน Key หรือเติมเครดิตครับ*"
                    )
                    send_discord_notify(notice)
                else:
                    logger.warning("Gemini credit depleted. Suppressing repetitive Discord error spam.")
            else:
                logger.warning(f"Failed to parse TradePlan: {last_error}")
            return None
             
        # Validate logic (Enforces MIN_RR_RATIO >= 1.5, SL >= $5.0, and strict trend alignment)
        is_valid = validate_trade_plan(trade_plan, snapshot=snapshot)
        if not is_valid:
            logger.warning("Trade plan validation failed (e.g. counter-trend, tight SL, or low RR). Changing Action to WAIT.")
            trade_plan.action = "WAIT"
            
        # SILENCE ENFORCEMENT: If Action is WAIT, NEVER notify Discord!
        if trade_plan.action == "WAIT":
            logger.info("Trade plan is WAIT. Staying completely silent as requested by user.")
            return trade_plan

        # ONLY notify when there is a real, high-conviction BUY or SELL signal!
        risk = abs(trade_plan.exact_entry_price - trade_plan.stop_loss)
        reward = abs(trade_plan.take_profit_1 - trade_plan.exact_entry_price)
        rr_ratio = reward / risk if risk > 0 else 0.0

        daily_signals_sent += 1
        last_signal_time = current_time
        last_signal_price = trade_plan.exact_entry_price
        last_signal_action = trade_plan.action

        final_message = f"🚨 **High-Conviction Sniper Signal!** 🚨\n\n"
        final_message += f"**Trade Plan for {SYMBOL}** (Patch 1.8.0 - Quant Multi-Timeframe)\n"
        final_message += f"**Action:** {trade_plan.action}\n"
        final_message += f"**Quota วันนี้:** [ไม้ที่ {daily_signals_sent}/{MAX_DAILY_SIGNALS}]\n"
        if getattr(trade_plan, 'trade_style', None):
            final_message += f"**รูปแบบแผน:** {trade_plan.trade_style}\n"
        
        # Confluence snapshot
        confluences = []
        if getattr(snapshot, 'htf_trend_1h', None):
            confluences.append(f"1H Trend: `{snapshot.htf_trend_1h}`")
        if getattr(snapshot, 'adx', None) is not None:
            confluences.append(f"ADX: `{snapshot.adx:.1f}`")
        if getattr(snapshot, 'candlestick_pattern', None):
            confluences.append(f"Candle: `{snapshot.candlestick_pattern}`")
        if getattr(snapshot, 'rsi_divergence', None):
            confluences.append(f"Divergence: `{snapshot.rsi_divergence}`")
        if confluences:
            final_message += f"**Confluence:** {' | '.join(confluences)}\n"

        final_message += f"**Entry:** ${trade_plan.exact_entry_price:.2f}\n"
        final_message += f"**Stop Loss:** ${trade_plan.stop_loss:.2f} (ห่าง ${risk:.2f})\n"
        final_message += f"**Take Profit 1:** ${trade_plan.take_profit_1:.2f} (เป้า +${reward:.2f})\n"
        if trade_plan.take_profit_2:
            final_message += f"**Take Profit 2:** ${trade_plan.take_profit_2:.2f}\n"
        final_message += f"**Risk/Reward Ratio:** 1 : {rr_ratio:.2f} (เป้าหมาย Win Rate ≥ 75-80%)\n"
            
        final_message += f"\n**Rationale:**\n{trade_plan.rationale}\n"
        final_message += "\n---\n**โปรดให้คะแนนความแม่นยำและเหตุผลของแผนนี้ (0-10) โดยพิมพ์ตัวเลขลงในช่องแชทได้เลยครับ** 👇"
        
        send_discord_notify(final_message)
        logger.info(f"Sniper signal sent successfully ({daily_signals_sent}/{MAX_DAILY_SIGNALS}).")
        return trade_plan
        
    except Exception as e:
        logger.error(f"Error during trading cycle: {e}", exc_info=True)
        return None

def start_scheduler():
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is missing! Fail fast.")
        exit(1)
        
    logger.info("=== Gold Trading Bot Started (Sniper Mode Only - Silent on WAIT) ===")
    
    # Schedule Sniper Scanner every 15 minutes (Completely silent unless high-conviction signal is found)
    schedule.every(15).minutes.do(run_trading_cycle)
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Graceful shutdown requested. Exiting.")

