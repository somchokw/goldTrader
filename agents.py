from crewai import Agent, Crew, Process, Task, LLM
from crewai.tools import tool
import json
import logging
import os
from config import GEMINI_API_KEY, OPENAI_API_KEY, DEEPSEEK_API_KEY, ANTHROPIC_API_KEY, LLM_MODEL
from market_data import fetch_gold_news, fetch_macro_data
from indicators import fetch_technical_data
from models import TradePlan

logger = logging.getLogger(__name__)

# Initialize LLM helper using CrewAI's wrapper
def get_llm(model_name: str = None):
    chosen_model = model_name or LLM_MODEL
    
    if chosen_model.startswith("openai/") or chosen_model.startswith("gpt-"):
        api_key = OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
    elif chosen_model.startswith("anthropic/") or chosen_model.startswith("claude-"):
        api_key = ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY")
    elif chosen_model.startswith("deepseek/"):
        api_key = DEEPSEEK_API_KEY or os.environ.get("DEEPSEEK_API_KEY")
    else:
        api_key = GEMINI_API_KEY
        
    return LLM(
        model=chosen_model,
        api_key=api_key,
        temperature=0.2
    )

llm = get_llm()

@tool("Fetch Latest Gold News")
def tool_get_latest_gold_news() -> str:
    """ดึงข่าวสารล่าสุดที่เกี่ยวกับทองคำและข้อมูลมหภาค (DXY, Yield)"""
    news = fetch_gold_news()
    macro = fetch_macro_data()
    return f"Macro Data:\n{json.dumps(macro, indent=2)}\n\nNews:\n{news}"

@tool("Fetch Technical Data")
def tool_get_technical_data() -> str:
    """ดึงข้อมูลราคา และคำนวณ Indicator ของทองคำ (Daily และ 15m)"""
    daily = fetch_technical_data(interval="1d", period="3mo")
    intraday = fetch_technical_data(interval="15m", period="5d")
    
    if not daily or not intraday:
        return "INSUFFICIENT_DATA: ไม่สามารถดึงข้อมูลกราฟที่สมบูรณ์ได้"
        
    return f"Daily Data:\n{daily.model_dump_json(indent=2)}\n\n15m Data:\n{intraday.model_dump_json(indent=2)}"

def create_gold_crew(model_name: str = None):
    current_llm = get_llm(model_name)
    macro_analyst = Agent(
        role="Gold Macro & Sentiment Analyst",
        goal="วิเคราะห์ภาพรวมเศรษฐกิจโลก ดอกเบี้ย FED ค่าเงิน DXY และสงครามที่มีผลต่อราคาทองคำ",
        backstory="คุณคือผู้เชี่ยวชาญด้านเศรษฐศาสตร์ มุ่งเน้นการวิเคราะห์สินทรัพย์ปลอดภัยอย่างทองคำ ห้ามอ้างอิงความรู้เก่า ให้วิเคราะห์จากข้อมูลที่ Tool ดึงมาเท่านั้น",
        tools=[tool_get_latest_gold_news],
        verbose=True,
        llm=current_llm
    )

    technical_analyst = Agent(
        role="Gold Technical Analyst",
        goal="อ่านกราฟเทคนิคอล คำนวณจุดรับ-จุดต้านจาก Swing High / Swing Low และโมเมนตัมของราคาทองคำ",
        backstory="คุณคือ Trader สาย Quant ที่วิเคราะห์โครงสร้างราคา (Market Structure) จาก Swing High/Low ในอดีตได้อย่างแม่นยำ วิเคราะห์จาก Data Snapshot ที่ได้มาเท่านั้น",
        tools=[tool_get_technical_data],
        verbose=True,
        llm=current_llm
    )

    chief_trader = Agent(
        role="Chief Gold Trader",
        goal="นำข้อมูล Macro และ Technical Analyst มาประมวลผล เพื่อตัดสินใจและออกแผนการเทรดที่มี Win Rate สูงระดับมืออาชีพ (Win Rate >= 75-80% / อย่างน้อย 8 ใน 10 ไม้ต้องชนะ) โดยคุม Risk/Reward >= 1.5",
        backstory=(
            "คุณคือหัวหน้าทีมเทรดผู้จัดการพอร์ตลงทุนระดับมืออาชีพที่ยึดหลัก Institutional Quant & Sniper Execution\n"
            "เป้าหมายสูงสุดคือ Win Rate >= 75-80% เทรดเฉพาะจังหวะที่มีแต้มต่อสูงและมีสัญญาณคอนเฟิร์มหลายชั้น (Multi-Timeframe Alignment + Confluence) เท่านั้น ไม่เทรดพร่ำเพรื่อ ไม่ไล่ราคาที่ก้นเหวหรือยอดดอย\n"
            "กฎเหล็กเรื่องราคา: ใช้ราคาตลาดสดปัจจุบัน (close_price) จาก Tool 'Fetch Technical Data' เท่านั้น\n"
            "ห้ามจำหรือเดาราคาเก่าในอดีต (เช่น 1,900 - 2,400 USD) ทุกจุดเข้า Entry, SL, TP ต้องอ้างอิงจากราคาปัจจุบันในกราฟ 15m ล่าสุดเท่านั้น"
        ),
        verbose=True,
        allow_delegation=False,
        llm=current_llm
    )

    trade_manager = Agent(
        role="Trade Management Specialist",
        goal="ประเมินออเดอร์ที่ถืออยู่จากสถานการณ์ตลาดปัจจุบัน และตัดสินใจอย่างเด็ดขาดว่าจะ HOLD, CLOSE, RAISE_SL หรือ ADD_POSITION",
        backstory="คุณคือผู้เชี่ยวชาญการบริหารจัดการหน้าตัก (Trade Management) คุณเก่งในการเอาตัวรอดในตลาดผันผวน รู้ว่าเมื่อไหร่ควรหนี (Close) เมื่อไหร่ควรเลื่อน Stop Loss บังหน้าทุน (Raise SL) และเมื่อไหร่ควรปล่อยให้กำไรรันต่อไป (Hold)",
        verbose=True,
        allow_delegation=False,
        tools=[tool_get_latest_gold_news, tool_get_technical_data],
        llm=current_llm
    )

    # 2. Define Tasks
    macro_task = Task(
        description="Fetch latest gold news and macro data, then summarize the market sentiment.",
        expected_output="A structured JSON detailing the macro factors, DXY, US10Y, and overall sentiment.",
        agent=macro_analyst
    )

    technical_task = Task(
        description="Fetch gold market data (1d and 15m). Compute technical indicators (EMA Ribbon, ADX, RSI, MACD, BB, Stochastic, Divergence, Rejection Candlesticks) and support/resistance levels from swing_high/swing_low.",
        expected_output="A JSON object containing current market price, indicators, trend, support and resistance levels.",
        agent=technical_analyst
    )

    trader_task = Task(
        description=(
            "Based on the macro sentiment and technical analysis, decide the final trade action for Spot Gold (XAUUSD).\n"
            "You MUST output the result matching the Pydantic TradePlan schema EXACTLY.\n"
            "CRITICAL REAL-TIME PRICE REQUIREMENT:\n"
            "- Check the exact 'close_price' in the 15m Data from 'Fetch Technical Data' (reflecting the live market price).\n"
            "- All trade prices ('exact_entry_price', 'stop_loss', 'take_profit_1', 'take_profit_2') MUST be located directly around the current 15m close price.\n"
            "- NEVER use or hallucinate outdated historical gold prices (e.g. 1900-2400 USD). Base all calculations strictly on the live snapshot.\n\n"
            "INSTITUTIONAL QUANT SNIPER RULES (TARGET WIN RATE >= 75-80%):\n"
            "0. MULTI-TIMEFRAME (MTF) & TREND ALIGNMENT (ABSOLUTELY NO COUNTER-TREND):\n"
            "   - HIGHER TIMEFRAME (1H): If 'htf_trend_1h' is 'Bullish', SELL is strictly forbidden! If 'htf_trend_1h' is 'Bearish', BUY is strictly forbidden!\n"
            "   - 15M TREND: IF 15M is Bearish (Price < SMA20): BUY is strictly forbidden! Only consider SELL on pullbacks, or WAIT.\n"
            "   - 15M TREND: IF 15M is Bullish (Price > SMA20): SELL is strictly forbidden! Only consider BUY on dips, or WAIT.\n"
            "   - Align 15m entry with the 1H macro trend. Both timeframes MUST point in the same direction or 1H must be neutral.\n"
            "1. ADX TREND STRENGTH FILTER:\n"
            "   - Check 'adx' value. If ADX < 20, the market is choppy sideways without directional edge. Output 'WAIT'.\n"
            "2. STRICT PULLBACK TRADING ONLY - ABSOLUTELY NO CHASING:\n"
            "   - FOR SELL: NEVER sell when Stochastic %K < 35 or when price is already at the bottom near Lower Bollinger Band! Only SELL when price has pulled back UP into resistance (SMA20, EMA 21/50, Upper BB, or Swing High) and Stochastic %K is >= 60.\n"
            "   - FOR BUY: NEVER buy when Stochastic %K > 65 or when price is already at the peak near Upper Bollinger Band! Only BUY when price has dipped DOWN into support (SMA20, EMA 21/50, Lower BB, or Swing Low) and Stochastic %K is <= 40.\n"
            "3. CANDLESTICK REJECTION & DIVERGENCE CONFLUENCE:\n"
            "   - Confirm entry using 'candlestick_pattern' (e.g. Rejection Pin Bar, Engulfing) or 'rsi_divergence'. Never enter against an active strong momentum candle.\n"
            "4. STOP LOSS DISCIPLINE (PREVENT STOP HUNTS):\n"
            "   - Stop Loss MUST be placed beyond recent market structure (Swing High for SELL, Swing Low for BUY) with a safety buffer of at least $5 to $10 USD (or 1x ATR).\n"
            "   - NEVER set ultra-tight Stop Losses (< $5.00) that get stopped out by normal market noise.\n"
            "5. RISK / REWARD RATIO >= 1.5:\n"
            "   - Reward distance (|TP1 - Entry|) MUST be at least 1.5x of Risk distance (|Entry - SL|).\n"
            "6. HIGH CONVICTION THRESHOLD:\n"
            "   - If the setup does not have at least 75% confidence, output 'WAIT'. Maximum 10 high-quality trades per day."
        ),
        expected_output="A JSON object conforming strictly to the TradePlan schema.",
        agent=chief_trader,
        output_pydantic=TradePlan
    )

    crew = Crew(
        agents=[macro_analyst, technical_analyst, chief_trader],
        tasks=[macro_task, technical_task, trader_task],
        process=Process.sequential,
        verbose=True
    )
    
    return crew

def create_trade_management_crew(order_details: dict, model_name: str = None):
    from models import TradeManagementPlan
    
    current_llm = get_llm(model_name)
    trade_manager = Agent(
        role="Trade Management Specialist",
        goal="ประเมินออเดอร์ที่ถืออยู่หรือตั้งล่วงหน้า จากสถานการณ์ตลาดปัจจุบัน และตัดสินใจอย่างเด็ดขาดว่าจะ HOLD, CLOSE, RAISE_SL, ADD_POSITION, WAIT_PENDING หรือ CANCEL_PENDING",
        backstory="คุณคือผู้เชี่ยวชาญการบริหารจัดการหน้าตัก (Trade Management) คุณเก่งในการเอาตัวรอดในตลาดผันผวน คุณต้องแยกแยะให้ออกว่าออเดอร์นั้นถูกเปิดแล้ว (ACTIVE) หรือเป็นเพียงออเดอร์ล่วงหน้า (PENDING) ถ้าราคาไปไกลจากจุด PENDING มากแล้วควรสั่งยกเลิก (CANCEL_PENDING)",
        verbose=True,
        allow_delegation=False,
        tools=[tool_get_latest_gold_news, tool_get_technical_data],
        llm=current_llm
    )
    
    manage_task = Task(
        description=(
            f"The user has an order with the following details:\n"
            f"{json.dumps(order_details, indent=2)}\n\n"
            "Use your tools to check the CURRENT market sentiment and technicals (price, trend, support/resistance).\n"
            "CRITICAL RULES:\n"
            "1. If 'order_status' is 'ACTIVE', you MUST ONLY output: 'HOLD', 'CLOSE', 'RAISE_SL', or 'ADD_POSITION'.\n"
            "2. If 'order_status' is 'PENDING', you MUST ONLY output: 'WAIT_PENDING' (if the setup is still valid and price is approaching) or 'CANCEL_PENDING' (if the price has moved far away and the setup is invalidated).\n"
            "Evaluate if the order is still valid and output the result matching the TradeManagementPlan Pydantic schema EXACTLY."
        ),
        expected_output="A JSON object conforming strictly to the TradeManagementPlan schema.",
        agent=trade_manager,
        output_pydantic=TradeManagementPlan
    )
    
    crew = Crew(
        agents=[trade_manager],
        tasks=[manage_task],
        process=Process.sequential,
        verbose=True
    )
    
    return crew

def create_recovery_crew(order_details: dict, model_name: str = None):
    from models import RecoveryPlan
    
    current_llm = get_llm(model_name)
    recovery_specialist = Agent(
        role="Recovery & Psychology Specialist",
        goal="วิเคราะห์สาเหตุที่ออเดอร์เดิมชน Stop Loss หรือล้างพอร์ต และตัดสินใจว่าจะแนะนำให้พัก (REST) หรือหาจุดเข้าใหม่เพื่อแก้เกม (RECOVERY)",
        backstory="คุณคือผู้เชี่ยวชาญด้านการฟื้นฟูพอร์ตและจิตวิทยาการเทรด คุณรู้ว่าเมื่อไหร่ตลาดไม่เป็นใจและควรพักผ่อน และเมื่อไหร่เป็นเพียงการสะบัดกิน SL (Stop Hunt) ซึ่งสามารถเข้าแก้เกมได้ทันที คุณตัดสินใจเด็ดขาดและรอบคอบ",
        verbose=True,
        allow_delegation=False,
        tools=[tool_get_latest_gold_news, tool_get_technical_data],
        llm=current_llm
    )
    
    recovery_task = Task(
        description=(
            f"The user has an order that just hit its STOP LOSS with the following details:\n"
            f"{json.dumps(order_details, indent=2)}\n\n"
            "Use your tools to check the CURRENT market sentiment and technicals (price, trend, support/resistance).\n"
            "Analyze why the trade failed (e.g., trend reversal, stop hunt, major news).\n"
            "Evaluate if they should 'REST' (wait for a better day) or 'RECOVERY' (enter a new trade now).\n"
            "Output the result matching the RecoveryPlan Pydantic schema EXACTLY."
        ),
        expected_output="A JSON object conforming strictly to the RecoveryPlan schema.",
        agent=recovery_specialist,
        output_pydantic=RecoveryPlan
    )
    
    crew = Crew(
        agents=[recovery_specialist],
        tasks=[recovery_task],
        process=Process.sequential,
        verbose=True
    )
    
    return crew
