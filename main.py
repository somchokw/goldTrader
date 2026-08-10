import yfinance as yf
from crewai import Agent, Crew, Process, Task, LLM
from crewai.tools import tool
import os
import time
import datetime
import requests
import schedule
from dotenv import load_dotenv
import pandas_ta as ta

load_dotenv()

@tool("Fetch Latest Gold News")
def get_latest_gold_news():
    """ดึงข่าวสารล่าสุดที่เกี่ยวกับทองคำเพื่อวิเคราะห์ Sentiment"""
    gold = yf.Ticker("GC=F")
    news_items = gold.news
    if not news_items:
        return "ไม่มีข่าวสารล่าสุดในระบบ yfinance"
    
    # รวบรวมหัวข้อข่าว 5 อันดับแรก
    news_summary = ""
    for idx, item in enumerate(news_items[:5], 1):
        news_summary += f"{idx}. {item.get('title', 'No Title')} (Publisher: {item.get('publisher', 'Unknown')})\n"
    return f"ข่าวล่าสุดเกี่ยวกับทองคำ:\n{news_summary}"

# Tool สำหรับดึงข้อมูลกราฟเทคนิคอลทองคำ (XAU/USD)
@tool("Fetch Gold Market Data")
def get_gold_technical_data():
    """ดึงข้อมูลราคา และคำนวณ Indicator เชิงลึก (MACD, RSI, Bollinger Bands) ของทองคำ"""
    gold = yf.Ticker("GC=F")  # Gold Futures
    # ดึงข้อมูลมา 3 เดือนเพื่อให้มีข้อมูลพอสำหรับการคำนวณ Indicator
    hist = gold.history(period="3mo", interval="1d")

    # คำนวณ Indicators ด้วย pandas-ta
    hist.ta.macd(append=True)
    hist.ta.rsi(length=14, append=True)
    hist.ta.bbands(length=20, std=2, append=True)
    hist["SMA_20"] = hist.ta.sma(length=20)
    
    latest = hist.iloc[-1]

    # กำหนดตัวแปรสำหรับคอลัมน์ที่ถูกสร้างโดย pandas-ta (อาจมีการปรับเปลี่ยนชื่อเล็กน้อยตามเวอร์ชัน)
    # MACD ธรรมดาจะสร้างคอลัมน์ MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
    macd_val = latest.get("MACD_12_26_9", 0)
    macd_signal = latest.get("MACDs_12_26_9", 0)
    rsi_val = latest.get("RSI_14", 50)
    bb_lower = latest.get("BBL_20_2.0", 0)
    bb_upper = latest.get("BBU_20_2.0", 0)

    return f"""
    --- Daily Timeframe Data ---
    ราคาปัจจุบัน (Close): {latest['Close']:.2f}
    High: {latest['High']:.2f}, Low: {latest['Low']:.2f}
    SMA 20 วัน: {latest.get('SMA_20', 0):.2f}
    RSI (14): {rsi_val:.2f}
    MACD: {macd_val:.2f} (Signal: {macd_signal:.2f})
    Bollinger Bands: Lower={bb_lower:.2f}, Upper={bb_upper:.2f}
    """

# Tool สำหรับดึงข้อมูลกราฟ 15 นาที
@tool("Fetch Intraday Gold Data")
def get_intraday_technical_data():
    """ดึงข้อมูลราคา และคำนวณ Indicator ของทองคำในระดับ 15 นาที (15m) สำหรับหาจุดเข้าที่แม่นยำ"""
    gold = yf.Ticker("GC=F")
    hist = gold.history(period="5d", interval="15m")
    
    if hist.empty:
        return "ไม่มีข้อมูล Intraday 15m"

    hist.ta.rsi(length=14, append=True)
    hist.ta.bbands(length=20, std=2, append=True)
    
    latest = hist.iloc[-1]
    
    rsi_val = latest.get("RSI_14", 50)
    bb_lower = latest.get("BBL_20_2.0", 0)
    bb_upper = latest.get("BBU_20_2.0", 0)
    
    return f"""
    --- 15-Minute (Intraday) Timeframe Data ---
    ราคาล่าสุด (15m Close): {latest['Close']:.2f}
    RSI 15m (14): {rsi_val:.2f}
    Bollinger Bands 15m: Lower={bb_lower:.2f}, Upper={bb_upper:.2f}
    """

llm_model = "gemini/gemini-flash-latest"

# Agent 1: สายข่าวและมหภาค
macro_analyst = Agent(
    role="Gold Macro & Sentiment Analyst",
    goal="วิเคราะห์ภาพรวมเศรษฐกิจโลก ดอกเบี้ย FED ค่าเงิน DXY และสงครามที่มีผลต่อราคาทองคำ",
    backstory="คุณคือผู้เชี่ยวชาญด้านเศรษฐศาสตร์ มุ่งเน้นการวิเคราะห์สินทรัพย์ปลอดภัยอย่างทองคำ",
    tools=[get_latest_gold_news],
    verbose=True,
    llm=llm_model
)

# Agent 2: สายเทคนิคอล
technical_analyst = Agent(
    role="Gold Technical Analyst",
    goal="อ่านกราฟเทคนิคอล คำนวณจุดรับ-จุดต้าน และโมเมนตัมของราคาทองคำ",
    backstory="คุณคือ Trader สาย Quant ที่วิเคราะห์อินดิเคเตอร์และโครงสร้างราคาได้อย่างแม่นยำ",
    tools=[get_gold_technical_data, get_intraday_technical_data],
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

# Agent 4: บริหารความเสี่ยง (Risk Manager)
risk_manager = Agent(
    role="Risk Management Specialist",
    goal="ประเมินความเสี่ยงและคำนวณ Lot Size ที่เหมาะสมจากแผนของ Chief Gold Trader",
    backstory="คุณคือผู้เชี่ยวชาญด้านการบริหารความเสี่ยง (Risk Management) ที่ช่วยปกป้องเงินทุนของเทรดเดอร์ไม่ให้ล้างพอร์ต",
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
    description="เรียกใช้ tool ดึงราคาและข้อมูลเทคนิคอลของทองคำล่าสุด (ทั้ง Daily และ Intraday 15m) แล้ววิเคราะห์จุดรับจุดต้าน",
    expected_output="สรุปสัญญาณทางเทคนิคอล สภาพแนวโน้ม และแนวรับ-แนวต้านสำคัญทั้งในระดับวันและระดับนาที",
    agent=technical_analyst,
)

# Task 3: ออกแผนการเทรด
task_strategy = Task(
    description="นำข้อมูลพื้นฐานและเทคนิคอลมาประมวลผลรวมกัน โดยบังคับให้ใช้กราฟ 15 นาที เพื่อหาจุดเข้าที่แม่นยำที่สุดแบบ Sniper Entry (ห้ามให้ช่วงราคากว้างเกิน 2 เหรียญ)",
    expected_output='''
    จัดทำรายงานการเทรดทองคำแบบ Sniper Execution:
    1. Action: (BUY / SELL / WAIT)
    2. Exact Entry Price (ตัวเลขจุดเข้าที่แม่นยำเป๊ะๆ อิงจาก 15m):
    3. Stop Loss (จุดตัดขาดทุน):
    4. Take Profit (จุดทำกำไร):
    5. เหตุผลสนับสนุน (อธิบายถึงความสอดคล้องระหว่าง Daily Trend และ 15m Reversal):
    ''',
    agent=trade_strategist,
)

# Task 4: คำนวณ Lot Size
task_risk = Task(
    description="นำแผนการเทรด (Action, Entry, Stop Loss) มาคำนวณระยะห่างความเสี่ยงเป็นดอลลาร์ และสร้างตารางแนะนำ Lot Size โดยใช้ข้อมูลว่า ทองคำ 1 Standard Lot = 100 ออนซ์",
    expected_output='''
    เพิ่มส่วน 🛡️ Risk Management (คำแนะนำการออกหลอด) ต่อท้ายรายงานแผนการเทรด โดยจัดรูปแบบตาราง Lot Size Guide ดังนี้:
    (ระบุระยะ Stop Loss สำหรับไม้นี้เป็นดอลลาร์ต่อออนซ์)
    
    แบบที่ 1: สายปลอดภัย (Risk 1-2%) - สำหรับคนตามซิกแนลทั่วไป
    - ทุน $1,000 -> เปิดออเดอร์ ... Lots
    - ทุน $3,000 -> เปิดออเดอร์ ... Lots
    - ทุน $5,000 -> เปิดออเดอร์ ... Lots
    
    แบบที่ 2: สายสไนเปอร์ (High Risk 50%) - พอร์ตปั้น/พอร์ตซิ่ง
    - ทุน $30 -> เปิดออเดอร์ ... Lots
    - ทุน $50 -> เปิดออเดอร์ ... Lots
    - ทุน $100 -> เปิดออเดอร์ ... Lots
    ''',
    agent=risk_manager,
)

# รวมทีมและรันระบบ
gold_crew = Crew(
    agents=[macro_analyst, technical_analyst, trade_strategist, risk_manager],
    tasks=[task_macro, task_tech, task_strategy, task_risk],
    process=Process.sequential,  # ทำงานตามลำดับ 1 -> 2 -> 3 -> 4
)

def send_discord_notify(message):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url or webhook_url == "your_discord_webhook_url_here_optional":
        return
    
    data = {
        "content": f"🤖 **Gold Trading AI Update** 📈\n```text\n{message}\n```"
    }
    try:
        requests.post(webhook_url, json=data)
    except Exception as e:
        print(f"Error sending Discord Notify: {e}")

def run_trading_bot():
    print(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Gold Trading Crew...")
    try:
        result = gold_crew.kickoff()
        output_msg = f"\n\n=======================================\nFinal Trading Strategy Result:\n=======================================\n{result}"
        print(output_msg)
        send_discord_notify(output_msg)
    except Exception as e:
        error_msg = f"Error running Gold Trading Crew: {e}"
        print(error_msg)
        send_discord_notify(error_msg)
    print("Waiting for next scheduled run...")

if __name__ == "__main__":
    if "GEMINI_API_KEY" not in os.environ:
        print("Warning: GEMINI_API_KEY environment variable is not set.")
        
    print("=== Gold Trading Bot Scheduler Started ===")
    print("The bot will run immediately, and then every 4 hours.")
    
    # รันรอบแรกทันที
    run_trading_bot()
    
    # ตั้งเวลารันทุกๆ 4 ชั่วโมง
    schedule.every(4).hours.do(run_trading_bot)
    
    # วนลูปเพื่อเช็คและรันตามเวลาที่กำหนด
    while True:
        schedule.run_pending()
        time.sleep(60)  # เช็คทุก 1 นาที
