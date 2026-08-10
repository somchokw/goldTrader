from crewai import Agent, Crew, Process, Task
from crewai.tools import tool
import json
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GEMINI_API_KEY, LLM_MODEL
from market_data import fetch_gold_news, fetch_macro_data
from indicators import fetch_technical_data
from models import TradePlan

logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model=LLM_MODEL,
    google_api_key=GEMINI_API_KEY,
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

    trade_strategist = Agent(
        role="Chief Gold Trader",
        goal="รวมข้อมูลจากปัจจัยพื้นฐานและเทคนิคอล เพื่อตัดสินใจแผนการเทรดทองคำ",
        backstory="คุณคือ Portfolio Manager ที่ตัดสินใจเด็ดขาด เน้นทำกำไรและคุมความเสี่ยงเข้มงวด",
        verbose=True,
        llm=llm
    )

    task_macro = Task(
        description="รวบรวมข่าวสารล่าสุดของทองคำและข้อมูล Macro Data (DXY, US Yield)",
        expected_output="สรุปทิศทางปัจจัยพื้นฐานว่าเป็นบวก (Bullish) หรือลบ (Bearish) ต่อราคาทอง",
        agent=macro_analyst,
    )

    task_tech = Task(
        description="เรียกใช้ tool ดึงราคาและข้อมูลเทคนิคอลของทองคำล่าสุด (Daily และ 15m) แล้ววิเคราะห์จุดรับจุดต้าน (Swing High/Low, ATR)",
        expected_output="สรุปสัญญาณทางเทคนิคอล สภาพแนวโน้ม และแนวรับ-แนวต้านสำคัญทั้งในระดับวันและระดับนาที",
        agent=technical_analyst,
    )

    task_strategy = Task(
        description="นำข้อมูลพื้นฐานและเทคนิคอลมาประมวลผลรวมกัน เพื่อหาจุดเข้าที่แม่นยำที่สุดแบบ Sniper Entry (ใช้กราฟ 15m เป็นหลัก)",
        expected_output="TradePlan JSON data structure with action, entry, SL, TP, and rationale.",
        agent=trade_strategist,
        output_pydantic=TradePlan
    )

    crew = Crew(
        agents=[macro_analyst, technical_analyst, trade_strategist],
        tasks=[task_macro, task_tech, task_strategy],
        process=Process.sequential,
    )
    return crew
