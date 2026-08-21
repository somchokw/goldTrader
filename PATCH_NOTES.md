# 📝 Patch Notes

## v1.7.1 - 2026-08-21
### 🚀 Upgraded Models & 503 High Demand Resilience
- **Upgrade to Gemini 2.5 Flash / 2.5 Pro:** อัปเกรดโมเดลหลักเป็นโมเดลรุ่นใหม่ล่าสุด `gemini-2.5-flash` และ `gemini-2.5-pro` ซึ่งมีความแม่นยำและการคำนวณเชิง Quant สูงกว่าโมเดล 1.5 อย่างก้าวกระโดด
- **Multi-Provider Support:** รองรับการเชื่อมต่อ OpenAI (`gpt-4o`, `gpt-4o-mini`), Anthropic (`claude-3-5-sonnet`), DeepSeek (`deepseek-chat`) เพียงเพิ่ม API Key ใน Environment Variables
- **503 High Demand Auto-Recovery:** เพิ่มระบบจัดการ Error `503 UNAVAILABLE (High demand)` พร้อม Exponential Backoff และสลับไปยังโมเดลสำรองใน Candidate Pool โดยอัตโนมัติ ทำให้บอททำงานต่อเนื่องได้ไม่สะดุด

## v1.7.0 - 2026-08-21
### 🎯 Price Accuracy & Anti-Hallucination
- **Strict Real-Time Price Enforcement (4,500+ USD):** ล็อกกฎเหล็กใน Agent Backstory และ Trader Task ให้ใช้ตัวเลข `close_price` ปัจจุบันจากกราฟ 15m (ระดับ 4,500+ USD) เท่านั้น ห้าม AI หลอนหรือนำตัวเลขเก่าในหน่วยความจำ (2,000–2,400 USD) มาใช้ออกแผนเทรดเด็ดขาด
- **Live Spot Gold Validation:** กำหนดให้จุด Entry, SL, TP สัมพันธ์กับราคา Spot Gold ณ ปัจจุบัน 100%

## v1.6.9 - 2026-08-21
### 🚀 Enhanced & Fixed
- **Real-Time Institutional Spot Gold Feed:** ย้ายระบบดึงราคาทองคำ Spot Gold มาใช้ Swissquote Institutional Live Feed + Yahoo Finance GC=F ทำให้ได้ราคา Spot Gold ปัจจุบันที่แม่นยำและสดใหม่อยู่เสมอ
- **Real-Time Gold News Filtering:** ปรับจูน Google News RSS ดึงเฉพาะข่าวสารทองคำและ XAUUSD ภายใน 24 ชม. ล่าสุด (`when:1d`) พร้อมเสริม FXStreet News RSS
- **Discord Native Slash Commands (`/check` & `/checkgold`):** เพิ่ม Discord Slash Commands เต็มรูปแบบ ซิงค์คำสั่งอัตโนมัติเมื่อบอทออนไลน์ ทำให้พิมพ์ `/check` และ `/checkgold` ได้โดยตรง และทำงานได้แม้เซิร์ฟเวอร์ไม่ได้เปิด Message Content Intent
- **Forgiving Text Command Matching:** ปรับปรุง `on_message` ให้รองรับคำสั่ง `#check`, `!check`, `check`, `checkgold`, `@bot check` ทุกรูปแบบ

## v1.6.8 - 2026-08-21
### 🛠️ Fixed
- **Gemini Model 404 Resolution & Multi-Model Dynamic Fallbacks:** แก้ปัญหา `404 NOT_FOUND` จาก Google Gemini v1beta โดยเปลี่ยนโมเดลหลักเป็น `gemini-2.0-flash` และเพิ่มระบบ Auto-Fallback อัตโนมัติ (`gemini-2.0-flash` -> `gemini-2.5-flash` -> `gemini-1.5-flash-latest` -> `gemini-1.5-flash-002`) ทั้งใน CrewAI trading cycle และ Vision OCR ทำให้ AI สามารถสลับโมเดลที่เปิดให้บริการใน API Key นั้นๆ ได้ทันทีโดยไม่พัง

## v1.6.7 - 2026-08-21
### 🛠️ Fixed
- **Gemini Model Identifier & Env Override:** เปลี่ยนชื่อโมเดลจาก `gemini-3.5-flash` ที่ไม่มีอยู่จริง กลับมาใช้โมเดลมาตรฐานที่เสถียร `gemini-1.5-flash` พร้อมเปิดรับค่าผ่าน `LLM_MODEL` และ `VISION_MODEL` environment variable ป้องกัน AI Crew และ Vision API ล่มตอนรันวิเคราะห์
- **Test Suite Discovery Guard:** ปรับปรุง `test_models.py` ให้ทำงานแบบ Safe Discovery เพื่อให้ Pytest รันผ่านทุก Test Case

## v1.6.6 - 2026-08-19
### 🚀 Enhanced
- **Short-term (Scalp) & Long-term (Swing) Instant Signal Trigger:** ปรับจูน Prompt ของ Chief Gold Trader ให้สแกนและส่งสัญญาณเทรดทันทีเมื่อพบโอกาส ทั้งไม้สั้น (15m Scalp/Intraday ดักการกลับตัวตาม Stochastic/RSI/BB) และไม้ยาว (Daily/Swing รันเทรนด์ตามโครงสร้างใหญ่) โดยไม่ต้องรอให้เงื่อนไขสุดโต่ง (Extreme) ครบทุกข้อ
- **Trade Style Tagging:** เพิ่มฟิลด์ `trade_style` ใน `TradePlan` และแสดงผลในข้อความแจ้งเตือน Discord ว่าเป็นไม้สั้นหรือไม้ยาวอย่างชัดเจน

## v1.6.5 - 2026-08-19
### 🛠️ Fixed
- **Keep-Alive Multi-Method & Response Headers:** Added support for `HEAD`, `POST`, `OPTIONS` along with `GET` on `/`, `/health`, `/ping`, `/healthz`, with JSON content-negotiation and explicit threaded execution to ensure external pingers (cron-job.org, UptimeRobot) receive reliable 200 OK responses.
- **Discord Bot Concurrency & Startup Lock:** Added `asyncio.Lock()` around CrewAI kickoff loops to prevent `routine_loop` and `scanner_loop` from running heavy AI crews simultaneously on startup, eliminating CPU/RAM throttling and gateway heartbeat disconnects.
- **Flexible Command & Mention Handling:** Added flexible command aliases (`#check`, `!check`, `/check`, `$check`, `check`, `#checkgold`, `!checkgold`, etc.) and cleaned mention tag stripping in `on_message` so the bot responds reliably even when mentioned.

## v1.6.4 - 2026-08-18
### 🛠️ Fixed
- **Instant Web Health Check & Keep-Alive:** Moved `keep_alive()` to run immediately at entry point in `main.py` before importing heavy modules (CrewAI, LangChain, Discord) so that Render and cron-job.org health checks receive an instant 200 OK without timing out (preventing 502/503 Service Unavailable).
- **Added Health Endpoints:** Added `/health`, `/ping`, `/healthz` endpoints to `keep_alive.py` with default port 10000.

## v1.6.3 - 2026-08-18
### 🛠️ Fixed
- **Render Deployment Dependencies:** Added missing dependencies (`schedule`, `python-dotenv`, `requests`, `pillow`, `google-genai`) to `requirements.txt` to fix `ModuleNotFoundError: No module named 'schedule'` on Render startup.

## v1.6.2 - 2026-08-18
### 🛠️ Fixed
- **Gold Price & Indicator Fetching:** Fixed `ModuleNotFoundError` by removing remaining `yfinance` import in `indicators.py` and `main.py`.
- **Multi-Endpoint Binance Fallbacks:** Added fallbacks (`api.binance.com`, `data-api.binance.vision`, `api.binance.us`) for robust PAXGUSDT OHLCV and Spot Gold spread calculation across all hosting providers.
- **Resilient Gold News Feed:** Implemented multi-source RSS fallback (Google News RSS & Investing.com RSS) to ensure gold news is always reliably retrieved.
- **Model Validation:** Fixed missing default for `take_profit_2` in `TradePlan` model and updated test suites.
### Added
- **Pending Order Support:** AI now extracts `order_status` (ACTIVE or PENDING) from images.
- **Thai Translations:** Action outputs (HOLD, CLOSE, RAISE_SL) are now translated to Thai for clarity.

### Changed
- Trade Management Specialist prompt updated to evaluate Pending orders appropriately.

## v1.4.6 - 2026-08-11
### 🛠️ Fixed
- **Dual-Scheduler Integration:** ย้ายระบบตั้งเวลา (`schedule` library) จาก `scheduler.py` มาใช้ `discord.ext.tasks` ใน `bot.py` เพื่อให้ลูปการทำงาน 15 นาที และ 4 ชั่วโมง สามารถรันคู่กับตัว Discord Bot ได้โดยไม่ถูกบล็อก
- **Image Processing Debugging:** เพิ่มระบบ Debug Log เข้าไปใน `on_message` เพื่อตรวจสอบว่าบอทมองเห็นรูปภาพและอ่านนามสกุลไฟล์ได้ถูกต้องหรือไม่ (แก้ไขปัญหาส่งรูปแล้วบอทไม่ตอบ)

## v1.4.5 - Dual-Scheduler Logic
**Date:** 2026-08-11

### 🚀 Feature Enhancements
- **Dual-Scheduler (2-Tier Scanning):** ปรับระบบตั้งเวลาให้แบ่งเป็น 2 รอบคือ
  - `Routine Update`: รายงานสถานการณ์ตลาดทุกๆ 4 ชั่วโมง เพื่อให้ผู้ใช้ทราบว่าบอทยังทำงานอยู่ (ถึงแม้จะไม่มีสัญญาณเข้าก็จะมีรายงานส่งมาบอกว่าทำไมถึงให้ WAIT)
  - `Sniper Scanner`: สแกนกราฟเบื้องหลังทุกๆ 15 นาที หากไม่มีสัญญาณจะอยู่เงียบๆ แต่ถ้าพบสัญญาณ (BUY/SELL) ที่คุ้มค่า จะเด้งแจ้งเตือนแทรกขึ้นมาทันที
## v1.4.4 - TradingView Data Integration
**Date:** 2026-08-10

### 🚀 Technical Engine Overhaul
- **TradingView TA:** เปลี่ยนระบบดึงข้อมูลกราฟและคำนวณอินดิเคเตอร์ทั้งหมดจาก `yfinance` + `pandas-ta` ไปใช้ `tradingview-ta` 
- **OANDA XAUUSD:** ดึงข้อมูล Spot Gold (XAUUSD) จากโบรกเกอร์ OANDA บนแพลตฟอร์ม TradingView โดยตรง ทำให้ได้ราคาปัจจุบัน (Current Price) และค่าต่างๆ (RSI, MACD, SMA) ตรงกับกราฟในจอผู้ใช้ 100% 
- **Bug Fix:** แก้ปัญหา Yahoo Finance บล็อก API (Error 403) จนทำให้ AI ขาดข้อมูลราคาปัจจุบันและหลอนเดาไปที่ราคา 1955.0
## v1.4.3 - Price Accuracy & Global Feedback
**Date:** 2026-08-10

### 🎯 Data Source Migration
- **Spot Gold Integration:** เปลี่ยนระบบดึงราคากลางจาก `GC=F` (Gold Futures) เป็น `XAUUSD=X` (Spot Gold) เพื่อให้ราคาที่ AI ใช้วิเคราะห์ ตรงกับพอร์ต MT4/MT5 ของผู้ใช้แบบ 100% แก้ปัญหาราคาแนะนำคลาดเคลื่อนจากความจริง

### 🧠 Global Feedback Loop
- **Auto Signal Feedback:** ระบบจะขอคะแนนความพึงพอใจ 0-10 ทุกครั้งที่ส่งสัญญาณเทรดอัตโนมัติ (Auto Signals) โดยผู้ใช้สามารถพิมพ์ตัวเลขตอบกลับในช่องแชทได้ทันที และระบบจะทำการบันทึกเพื่อใช้ในการเรียนรู้ต่อไป
## v1.4.2 - Smart Feedback & Dynamic Signals
**Date:** 2026-08-10

### 🛡️ Recovery Plan (แผนแก้เกมเมื่อโดน SL)
- **SL Detection:** บอทสามารถตรวจจับได้แล้วว่าราคาปัจจุบันทะลุจุด Stop Loss ไปแล้วหรือยัง
- **Recovery Agent:** เพิ่ม AI ผู้เชี่ยวชาญด้านการแก้มือ หากพอร์ตแตกหรือโดน SL บอทจะตัดสินใจว่าควรแนะนำให้พักผ่อน (REST) หรือแนะนำจุดเข้าใหม่ (RECOVERY) ทันที

### 🧠 Smart Features (ฟีเจอร์อัจฉริยะ)
- **User Feedback Loop:** บอทจะถามความพึงพอใจ 0-10 หลังจากตอบทุกครั้ง และเก็บข้อมูลลงไฟล์ `feedback.csv` เพื่อนำไปพัฒนา AI ให้เก่งขึ้นในอนาคต
- **Dynamic Scheduler:** ปรับรอบการสแกนตลาดจากทุก 4 ชั่วโมง เป็นทุก 1 ชั่วโมง และปรับเปลี่ยนให้แจ้งเตือนเข้า Discord **เฉพาะเมื่อบอทแนะนำให้ BUY หรือ SELL เท่านั้น** (หากเป็น WAIT บอทจะไม่ส่งข้อความกวนใจ)
## v1.4.1 - Cloud Deployment Support
**Date:** 2026-08-10

### ☁️ New Infrastructure (โครงสร้างพื้นฐานใหม่)
- **Keep-Alive Server (`keep_alive.py`):** เพิ่มเว็บเซิร์ฟเวอร์จำลองขนาดเล็กด้วย Flask เพื่อรันเป็น Background Thread คู่กับตัวบอท
- **Procfile:** เพิ่มไฟล์ Procfile `web: python main.py`
- **Render / Koyeb Ready:** โค้ดชุดนี้สามารถ Deploy ขึ้นผู้ให้บริการ Cloud แบบ Free Tier ได้ทันที โดยสามารถใช้ควบคู่กับ cron-job.org เพื่อป้องกันไม่ให้แอปพลิเคชันหลับ (Sleep) ได้ 100%

---

## v1.4 - Trade Management AI (Discord Bot + Vision)
**Date:** 2026-08-10

### 🤖 New Interactive Features (ฟีเจอร์ใหม่)
- **Discord Bot Migration:** อัปเกรดจาก Webhook ส่งข้อความทางเดียว เป็น Discord Bot เต็มรูปแบบ (`bot.py`) ที่โต้ตอบกับผู้ใช้ได้ในห้องแชท
- **Vision AI Parsing:** เพิ่มความสามารถให้ AI อ่านตัวเลข Entry, Current Price, TP, และ SL จากรูปภาพ (Screenshot หน้าจอ MT4/MT5) ที่ผู้ใช้ส่งเข้ามา
- **Trade Management Agent:** เพิ่ม Agent ใหม่ที่ทำหน้าที่ "วิเคราะห์ออเดอร์ที่ถืออยู่" แล้วให้คำแนะนำว่าจะ HOLD, CLOSE, RAISE_SL, หรือ ADD_POSITION เพื่อดูแลความปลอดภัยให้พอร์ตแบบเรียลไทม์

---

## v1.3 - Risk Management Module
**Date:** 2026-08-10

### 🧠 New AI Agent (บอทใหม่)
- **Risk Manager Agent:** เพิ่มตัวแทน AI ตัวที่ 4 เพื่อทำหน้าที่คำนวณหลอด (Lot Size) จากระยะ Stop Loss แบบอัตโนมัติ โดยสร้าง Risk Matrix ออกมา 2 รูปแบบ
  - **Safe Mode:** สายเทรดปลอดภัย (ทุน $1k, $3k, $5k)
  - **Sniper Mode:** สายปั้นพอร์ตความเสี่ยงสูง (ทุน $30, $50, $100)

---

## v1.2 - The Notification System
**Date:** 2026-08-10

### 📱 New Features (ฟีเจอร์ใหม่)
- **Auto Scheduler:** เพิ่มระบบตั้งเวลาอัตโนมัติ (Scheduler) โดยใช้ไลบรารี `schedule` ทำให้บอทสามารถทำงานเองแบบลูปได้ (ค่าเริ่มต้นคือทุกๆ 4 ชั่วโมง)
- **Discord Webhook Integration:** เพิ่มฟังก์ชันส่งรายงานการเทรดตรงเข้ามือถือผ่านระบบ Discord Webhook แบบ Optional (ทดแทน LINE Notify ที่กำลังจะปิดตัวลง)

---

## v1.1.1 - Precision Sniper
**Date:** 2026-08-10

### 🎯 New Features (ฟีเจอร์ใหม่)
- **Intraday Data Integration:** เพิ่มฟังก์ชันการวิเคราะห์กราฟระดับ 15 นาที (15m) เข้าสู่ระบบ
- **Sniper Entry:** อัปเกรดให้ `Chief Gold Trader` สรุปจุดเข้าเทรดแบบตัวเลขที่เจาะจง (Exact Price) มากยิ่งขึ้น

---

## v1.1 - The Indicator Expansion
**Date:** 2026-08-10

### 🚀 New Features (ฟีเจอร์ใหม่)
- **Advanced Technical Analysis:** `Technical Analyst Agent` ได้รับการอัปเกรดให้สามารถดึงข้อมูลอินดิเคเตอร์เชิงลึกได้แล้ว:
  - `MACD` สำหรับวิเคราะห์ทิศทางและโมเมนตัม
  - `Bollinger Bands` สำหรับวิเคราะห์ความผันผวนและกรอบราคา
  - `RSI` การคำนวณที่แม่นยำขึ้น
- **Live News Feed:** `Macro Analyst Agent` ได้รับ Tool ใหม่ `get_latest_gold_news` สำหรับดึงข่าวสารล่าสุดเกี่ยวกับทองคำ (GC=F) จากระบบของ yfinance เพื่อวิเคราะห์ Sentiment ของตลาด

### 🔧 Improvements (การปรับปรุง)
- เพิ่มไลบรารี `pandas-ta` เข้าสู่ `requirements.txt` สำหรับประมวลผล Technical Indicators ที่รวดเร็วและเป็นมาตรฐานยิ่งขึ้น
