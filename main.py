import yfinance as yf
from crewai import Agent, Crew, Process, Task, LLM
from crewai.tools import tool
import os
from dotenv import load_dotenv

load_dotenv()

# Tool สำหรับดึงข้อมูลกราฟเทคนิคอลทองคำ (XAU/USD)
@tool("Fetch Gold Market Data")
def get_gold_technical_data():
    """ดึงข้อมูลราคา และคำนวณ Indicator ของทองคำ (GC=F หรือ XAUUSD)"""
    gold = yf.Ticker("GC=F")  # Gold Futures
    hist = gold.history(period="1mo", interval="1d")

    # คำนวณ Moving Average หรือ RSI แบบง่าย
    hist["SMA_20"] = hist["Close"].rolling(window=20).mean()
    latest = hist.iloc[-1]

    return f"""
    ราคาปัจจุบัน (Close): {latest['Close']:.2f}
    High: {latest['High']:.2f}, Low: {latest['Low']:.2f}
    SMA 20 วัน: {latest['SMA_20']:.2f}
    เทรนด์คร่าวๆ: {'BULLISH' if latest['Close'] > latest['SMA_20'] else 'BEARISH'}
    """

llm_model = "gemini/gemini-flash-latest"

# Agent 1: สายข่าวและมหภาค
macro_analyst = Agent(
    role="Gold Macro & Sentiment Analyst",
    goal="วิเคราะห์ภาพรวมเศรษฐกิจโลก ดอกเบี้ย FED ค่าเงิน DXY และสงครามที่มีผลต่อราคาทองคำ",
    backstory="คุณคือผู้เชี่ยวชาญด้านเศรษฐศาสตร์ มุ่งเน้นการวิเคราะห์สินทรัพย์ปลอดภัยอย่างทองคำ",
    verbose=True,
    llm=llm_model
)

# Agent 2: สายเทคนิคอล
technical_analyst = Agent(
    role="Gold Technical Analyst",
    goal="อ่านกราฟเทคนิคอล คำนวณจุดรับ-จุดต้าน และโมเมนตัมของราคาทองคำ",
    backstory="คุณคือ Trader สาย Quant ที่วิเคราะห์อินดิเคเตอร์และโครงสร้างราคาได้อย่างแม่นยำ",
    tools=[get_gold_technical_data],
    verbose=True,
    llm=llm_model
)

# Agent 3: สรุปแผนการเทรด
trade_strategist = Agent(
    role="Chief Gold Trader",
    goal="รวมข้อมูลจากปัจจัยพื้นฐานและเทคนิคอล เพื่อตัดสินใจแผนการเทรดทองคำ",
    backstory="คุณคือ Portfolio Manager ที่ตัดสินใจเด็ดขาด เน้นทำกำไรและคุมความเสี่ยงเข้มงวด",
    verbose=True,
    llm=llm_model
)

# Task 1: วิเคราะห์ปัจจัยพื้นฐาน
task_macro = Task(
    description="รวบรวมข่าวสารล่าสุดของทองคำ ดอกเบี้ยสหรัฐฯ และดัชนี DXY ในวันนี้",
    expected_output="สรุปทิศทางปัจจัยพื้นฐานว่าเป็นบวก (Bullish) หรือลบ (Bearish) ต่อราคาทอง",
    agent=macro_analyst,
)

# Task 2: วิเคราะห์เทคนิคอล
task_tech = Task(
    description="เรียกใช้ tool ดึงราคาและข้อมูลเทคนิคอลของทองคำล่าสุด แล้ววิเคราะห์จุดรับจุดต้าน",
    expected_output="สรุปสัญญาณทางเทคนิคอล สภาพแนวโน้ม และแนวรับ-แนวต้านสำคัญ",
    agent=technical_analyst,
)

# Task 3: ออกแผนการเทรด
task_strategy = Task(
    description="นำข้อมูลพื้นฐานจาก task_macro และเทคนิคอลจาก task_tech มาประมวลผลรวมกันเพื่อวางแผนเทรด",
    expected_output='''
    จัดทำรายงานการเทรดทองคำ:
    1. Action: (BUY / SELL / WAIT)
    2. Entry Zone (ราคาเข้า):
    3. Stop Loss (จุดตัดขาดทุน):
    4. Take Profit (จุดทำกำไร):
    5. เหตุผลสนับสนุน:
    ''',
    agent=trade_strategist,
)

# รวมทีมและรันระบบ
gold_crew = Crew(
    agents=[macro_analyst, technical_analyst, trade_strategist],
    tasks=[task_macro, task_tech, task_strategy],
    process=Process.sequential,  # ทำงานตามลำดับ 1 -> 2 -> 3
)

if __name__ == "__main__":
    if "GEMINI_API_KEY" not in os.environ:
        print("Warning: GEMINI_API_KEY environment variable is not set.")
        
    print("Starting Gold Trading Crew...")
    result = gold_crew.kickoff()
    print("=======================================")
    print("Final Trading Strategy Result:")
    print("=======================================")
    print(result)
