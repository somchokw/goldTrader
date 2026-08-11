from crewai import Agent, Crew, Process, Task, LLM
from crewai.tools import tool
import json
import logging
from config import GEMINI_API_KEY, LLM_MODEL
from market_data import fetch_gold_news, fetch_macro_data
from indicators import fetch_technical_data
from models import TradePlan

logger = logging.getLogger(__name__)

# Initialize LLM using CrewAI's wrapper
llm = LLM(
    model=LLM_MODEL,
    api_key=GEMINI_API_KEY,
    temperature=0.2
)

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

def create_gold_crew():
    macro_analyst = Agent(
        role="Gold Macro & Sentiment Analyst",
        goal="วิเคราะห์ภาพรวมเศรษฐกิจโลก ดอกเบี้ย FED ค่าเงิน DXY และสงครามที่มีผลต่อราคาทองคำ",
        backstory="คุณคือผู้เชี่ยวชาญด้านเศรษฐศาสตร์ มุ่งเน้นการวิเคราะห์สินทรัพย์ปลอดภัยอย่างทองคำ ห้ามอ้างอิงความรู้เก่า ให้วิเคราะห์จากข้อมูลที่ Tool ดึงมาเท่านั้น",
        tools=[tool_get_latest_gold_news],
        verbose=True,
        llm=llm
    )

    technical_analyst = Agent(
        role="Gold Technical Analyst",
        goal="อ่านกราฟเทคนิคอล คำนวณจุดรับ-จุดต้าน และโมเมนตัมของราคาทองคำ",
        backstory="คุณคือ Trader สาย Quant ที่วิเคราะห์อินดิเคเตอร์และโครงสร้างราคาได้อย่างแม่นยำ วิเคราะห์จาก Data Snapshot ที่ได้มาเท่านั้น",
        tools=[tool_get_technical_data],
        verbose=True,
        llm=llm
    )

    chief_trader = Agent(
        role="Chief Gold Trader",
        goal="นำข้อมูลทั้งหมดจาก Macro และ Technical Analyst มาประมวลผล เพื่อตัดสินใจและออกแผนการเทรดขั้นสุดท้าย โดยต้องคุม Risk/Reward ให้คุ้มค่า",
        backstory="คุณคือหัวหน้าทีมเทรดผู้จัดการพอร์ตลงทุน คุณเป็นสาย Sniper Execution ที่เน้นจุดเข้าแม่นยำเป๊ะๆ คุณเป็นผู้ตัดสินใจขั้นเด็ดขาดว่าควรเทรดหรือไม่",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    trade_manager = Agent(
        role="Trade Management Specialist",
        goal="ประเมินออเดอร์ที่ถืออยู่จากสถานการณ์ตลาดปัจจุบัน และตัดสินใจอย่างเด็ดขาดว่าจะ HOLD, CLOSE, RAISE_SL หรือ ADD_POSITION",
        backstory="คุณคือผู้เชี่ยวชาญการบริหารจัดการหน้าตัก (Trade Management) คุณเก่งในการเอาตัวรอดในตลาดผันผวน รู้ว่าเมื่อไหร่ควรหนี (Close) เมื่อไหร่ควรเลื่อน Stop Loss บังหน้าทุน (Raise SL) และเมื่อไหร่ควรปล่อยให้กำไรรันต่อไป (Hold)",
        verbose=True,
        allow_delegation=False,
        tools=[tool_get_latest_gold_news, tool_get_technical_data],
        llm=llm
    )

    # 2. Define Tasks
    macro_task = Task(
        description="Fetch latest gold news and macro data, then summarize the market sentiment.",
        expected_output="A structured JSON detailing the macro factors, DXY, US10Y, and overall sentiment.",
        agent=macro_analyst
    )

    technical_task = Task(
        description="Fetch gold market data (1d and 15m). Compute technical indicators (RSI, MACD, BB) and support/resistance levels.",
        expected_output="A JSON object containing current market price, RSI, trend, support and resistance levels.",
        agent=technical_analyst
    )

    trader_task = Task(
        description=(
            "Based on the macro sentiment and technical analysis, decide the final trade action for Spot Gold (XAUUSD).\n"
            "You MUST output the result matching the Pydantic TradePlan schema EXACTLY.\n"
            "CRITICAL: Ensure Risk/Reward Ratio is >= 1.0 (Reward distance MUST be greater than or equal to Risk distance). If RR is < 1.0 or market is uncertain, output 'WAIT'."
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

def create_trade_management_crew(order_details: dict):
    from models import TradeManagementPlan
    
    trade_manager = Agent(
        role="Trade Management Specialist",
        goal="ประเมินออเดอร์ที่ถืออยู่หรือตั้งล่วงหน้า จากสถานการณ์ตลาดปัจจุบัน และตัดสินใจอย่างเด็ดขาดว่าจะ HOLD, CLOSE, RAISE_SL, ADD_POSITION, WAIT_PENDING หรือ CANCEL_PENDING",
        backstory="คุณคือผู้เชี่ยวชาญการบริหารจัดการหน้าตัก (Trade Management) คุณเก่งในการเอาตัวรอดในตลาดผันผวน คุณต้องแยกแยะให้ออกว่าออเดอร์นั้นถูกเปิดแล้ว (ACTIVE) หรือเป็นเพียงออเดอร์ล่วงหน้า (PENDING) ถ้าราคาไปไกลจากจุด PENDING มากแล้วควรสั่งยกเลิก (CANCEL_PENDING)",
        verbose=True,
        allow_delegation=False,
        tools=[tool_get_latest_gold_news, tool_get_technical_data],
        llm=llm
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

def create_recovery_crew(order_details: dict):
    from models import RecoveryPlan
    
    recovery_specialist = Agent(
        role="Recovery & Psychology Specialist",
        goal="วิเคราะห์สาเหตุที่ออเดอร์เดิมชน Stop Loss หรือล้างพอร์ต และตัดสินใจว่าจะแนะนำให้พัก (REST) หรือหาจุดเข้าใหม่เพื่อแก้เกม (RECOVERY)",
        backstory="คุณคือผู้เชี่ยวชาญด้านการฟื้นฟูพอร์ตและจิตวิทยาการเทรด คุณรู้ว่าเมื่อไหร่ตลาดไม่เป็นใจและควรพักผ่อน และเมื่อไหร่เป็นเพียงการสะบัดกิน SL (Stop Hunt) ซึ่งสามารถเข้าแก้เกมได้ทันที คุณตัดสินใจเด็ดขาดและรอบคอบ",
        verbose=True,
        allow_delegation=False,
        tools=[tool_get_latest_gold_news, tool_get_technical_data],
        llm=llm
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
