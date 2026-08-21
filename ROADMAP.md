# 🗺️ Gold Trading AI Crew - Development Roadmap

เพื่อให้ระบบ "Gold Trading Crew" มีความสามารถที่แข็งแกร่งขึ้น และใช้งานได้อัตโนมัติ 100% นี่คือแผนการพัฒนา (Patch Updates) ที่เราวางไว้สำหรับโปรเจกต์นี้ครับ:

---

## ✅ Completed Patches (ดำเนินการแล้ว)

### 🎯 Patch v1.7.0: Strict Real-Time Price Enforcement (Anti-Hallucination)
**สถานะ: ดำเนินการแล้วเสร็จ**
- กำชับคำสั่งและ Backstory ของ Chief Gold Trader ให้ใช้ราคา Spot Gold จาก Data Tool สดๆ (4,500+ USD) ห้ามอิงราคาเก่าในความจำโมเดล (2,000–2,400 USD)
- ป้องกันปัญหาแผนเทรดมีตัวเลขราคาไม่ตรงกับราคาตลาดปัจจุบัน

### 🚀 Patch v1.6.9: Real-Time Spot Gold, Fresh News Feed & Slash Commands
**สถานะ: ดำเนินการแล้วเสร็จ**
- เชื่อมต่อ Live Spot Gold Feed จาก Swissquote และ Yahoo Finance ทำให้ได้ราคาทองคำปัจจุบันสดใหม่อยู่เสมอ
- ปรับปรุงการดึงข่าวสารให้กรองเฉพาะข่าวใน 24 ชั่วโมงล่าสุด (`when:1d`) และ FXStreet RSS
- เพิ่ม Discord Slash Commands `/check` และ `/checkgold` ใช้งานได้ทันทีแบบ Native

### 🛠️ Patch v1.6.8: Gemini Model 404 Resolution & Multi-Model Dynamic Fallbacks
**สถานะ: ดำเนินการแล้วเสร็จ**
- แก้ปัญหา `404 NOT_FOUND` ของ Google Gemini API v1beta ด้วยการตั้งค่า Default เป็น `gemini-2.0-flash`
- เพิ่มระบบ Dynamic Multi-Model Fallback ใน `agents.py`, `scheduler.py`, และ `vision.py` เพื่อลองสลับไปใช้ `gemini-2.5-flash`, `gemini-1.5-flash-latest` อัตโนมัติหากโมเดลหลักไม่พร้อมใช้งาน

### 🛠️ Patch v1.6.7: Gemini Model Identifier & Safe Pytest Discovery
**สถานะ: ดำเนินการแล้วเสร็จ**
- ปรับแก้ชื่อโมเดล LLM และ Vision ให้ถูกต้องเป็น `gemini-1.5-flash` พร้อมเปิดรับค่า override จาก environment variables ป้องกัน ModelNotFound Error ตอน AI ออกแผนและอ่านรูปภาพ
- อัปเดต Unit Test Discovery เพื่อให้ทดสอบระบบผ่าน 100%

### 🚀 Patch v1.6.6: Short-term & Long-term Instant Signals
**สถานะ: ดำเนินการแล้วเสร็จ**
- ปรับเงื่อนไขการออกสัญญาณเทรดของ AI ให้ยืดหยุ่นและตอบสนองไวยิ่งขึ้น: เมื่อพบจังหวะเทรดไม่ว่าจะเป็นไม้สั้น (Scalp/Intraday) หรือไม้ยาว (Swing/Trend) ระบบจะส่งสัญญาณ BUY/SELL ทันที
- ระบุประเภทไม้ (`ไม้สั้น` หรือ `ไม้ยาว`) ลงในข้อความแจ้งเตือนอย่างชัดเจน

### 🛠️ Patch v1.6.5: Keep-Alive Multi-Method & Discord Gateway Concurrency Lock
**สถานะ: ดำเนินการแล้วเสร็จ**
- ปรับ `keep_alive.py` ให้รองรับ HTTP Methods ทุกแบบ (`GET`, `HEAD`, `POST`, `OPTIONS`) และรองรับ JSON headers เพื่อให้ cron-job.org / ping monitoring ตอบสนอง 200 OK ได้แน่นอน
- เพิ่ม `asyncio.Lock()` ใน `bot.py` ป้องกัน `routine_loop` และ `scanner_loop` รันซ้อนกันตอนเริ่มระบบ ลดภาระ RAM/CPU ไม่ให้ Discord Gateway หลุด
- เพิ่มความยืดหยุ่นของคำสั่ง `#check`, `#checkgold`, `!check`, `/check` พร้อมตัด Mention Prefix ออกอัตโนมัติ

### 🛠️ Patch v1.6.4: Fix Render Cold-Start & Keep-Alive 502/503
**สถานะ: ดำเนินการแล้วเสร็จ**
- ปรับจังหวะการเปิด Flask server (`keep_alive()`) ให้รันทันทีที่เริ่มโปรแกรม ก่อนโหลดโมดูลหนัก (CrewAI, LangChain, Discord)
- เพิ่ม endpoint `/health`, `/ping`, `/healthz` เพื่อให้ cron-job.org หรือ Render health check ตอบสนอง 200 OK ได้ทันที ป้องกัน 502/503 Service Unavailable

### 🛠️ Patch v1.6.3: Fix Render Deployment Missing Dependencies
**สถานะ: ดำเนินการแล้วเสร็จ**
- เพิ่ม dependency ที่จำเป็นใน `requirements.txt` (`schedule`, `python-dotenv`, `requests`, `pillow`, `google-genai`)
- แก้ไขปัญหา Render startup crash จาก `ModuleNotFoundError: No module named 'schedule'`

### 🛠️ Patch v1.6.2: Resilient Gold Price & Multi-Source News Feed
**สถานะ: ดำเนินการแล้วเสร็จ**
- แก้ปัญหา `ModuleNotFoundError` จากการลบ dependency yfinance ค้างใน indicators.py และ main.py
- เสริมระบบดึงราคาทองคำ Spot Gold และ Binance OHLCV ให้มี Multi-Endpoint Fallbacks
- เสริมระบบดึงข่าวสารทองคำด้วย Google News RSS + Investing.com RSS ป้องกันปัญหาข่าวไม่โหลด
- แก้ไข Pydantic `TradePlan` model ให้ `take_profit_2` เป็น optional พร้อมอัปเดต Unit Tests ทั้งหมด

### 🛠️ Patch v1.1: The Indicator Expansion
**สถานะ: ดำเนินการแล้วเสร็จ**
- เพิ่ม `pandas-ta` สำหรับการคำนวณ Indicator ระดับสูง (MACD, Bollinger Bands, RSI)
- ดึงข่าวสดจาก `yfinance` มาช่วยประเมิน Sentiment รายวัน

### 🎯 Patch v1.1.1: Precision Sniper
**สถานะ: ดำเนินการแล้วเสร็จ**
- เพิ่ม Tool ดึงกราฟ Intraday (15 นาที) มาประมวลผลคู่กับกราฟรายวัน
- ปรับ Prompt ของ Chief Trader ให้เลิกบอกจุดเข้าเป็น "โซนกว้างๆ" แต่ให้ฟันธง "ตัวเลขจุดเข้าแบบเป๊ะๆ" โดยอิงจากแนวรับ/ต้านในกราฟ 15 นาที

---

### 📱 Patch v1.2: The Notification System (ระบบรายงานตัว)
**สถานะ: ดำเนินการแล้วเสร็จ**
- **Discord Webhook Integration:** เมื่อ `Chief Gold Trader` สรุปแผนเสร็จ จะส่งข้อความแจ้งเตือน (Alert) แบบ Optional เข้าสู่สมาร์ทโฟนหรือคอมพิวเตอร์ผ่าน Discord ทันที (ทดแทนระบบเก่า)
- **Scheduler (ตั้งเวลารันอัตโนมัติ):** ใช้ไลบรารี `schedule` ให้บอทตื่นขึ้นมาทำงานเองลูปอัตโนมัติ (ปัจจุบันตั้งค่า Default ไว้ที่ทุกๆ 4 ชั่วโมง)

### 🧠 Patch v1.3: Risk Management Module (เพิ่มบอทคุมความเสี่ยง)
**สถานะ: ดำเนินการแล้วเสร็จ (Major Refactor v1.3.1 - v1.3.5)**
- **Deterministic Risk Engine:** ย้ายการคำนวณออกจากการกะประมาณของ LLM มาใช้สมการคณิตศาสตร์ที่แม่นยำ (Python) 
- **Strict Data Validation:** ตรวจสอบโครงสร้างกราฟและข่าวแบบเข้มงวด
- **Pydantic Structured Output:** บังคับ Agent คืนค่าผลลัพธ์การวิเคราะห์เป็น JSON schema
- **Refactor Project Structure:** แยกโค้ดออกจาก `main.py` เป็นโมดูลที่แยกอิสระ (SOLID Principle) พร้อมชุดทดสอบ `pytest`

---

### 🤖 Patch v1.4: Trade Management AI (ผู้ช่วยจัดการไม้เทรด)
**สถานะ: ดำเนินการแล้วเสร็จ**
- **Discord Bot + Vision AI:** เปลี่ยนจาก Webhook ทางเดียว เป็นบอทโต้ตอบได้
- **Image Parsing:** สามารถอัปโหลดรูปหน้าจอ MT4/MT5 เข้าแชทเพื่อให้ Gemini AI อ่านค่าราคาเข้า, SL, TP ได้
- **Trade Management Agent:** เพิ่มระบบให้คำปรึกษาเกี่ยวกับไม้ที่ถืออยู่ (HOLD, CLOSE, RAISE_SL, ADD_POSITION) พร้อมเหตุผลรองรับ

### ☁️ Patch v1.4.1: Cloud Deployment Support
**สถานะ: ดำเนินการแล้วเสร็จ**
- **Keep-Alive Server:** เพิ่ม `keep_alive.py` จำลองเว็บเซิร์ฟเวอร์ด้วย Flask
- ปรับแต่งให้รันบน Free Tier ของ Render.com, Koyeb, และ Railway.app ได้โดยไม่โดนบังคับ Sleep

### 🛠️ Patch v1.4.2: Smart Feedback & Dynamic Signals
**สถานะ: ดำเนินการแล้วเสร็จ**
- **Recovery Agent:** เพิ่มกลไกวิเคราะห์เมื่อไม้เทรดโดน SL เพื่อหาจุดแก้เกม
- **Feedback Loop:** เพิ่มระบบให้คะแนนความแม่นยำ (0-10) จากผู้ใช้งานเพื่อปรับจูน Prompt อัตโนมัติ
- **Smart Notification:** ปรับ Scheduler ให้แจ้งเตือนเฉพาะเมื่อเจอสัญญาณ High-Probability Setup เท่านั้น

### 🛠️ Patch v1.4.3: Price Accuracy & Global Feedback
**สถานะ: ดำเนินการแล้วเสร็จ**
- **Data Source Migration:** เปลี่ยนสัญลักษณ์จาก `GC=F` (Gold Futures) เป็น `XAUUSD=X` (Spot Gold) เพื่อให้ราคาซิงก์กับพอร์ต MT4/MT5 ของผู้ใช้มากที่สุด
- **Global Feedback:** ขยายระบบเก็บคะแนน 0-10 ให้ครอบคลุมไปถึงระบบสแกนอัตโนมัติรายชั่วโมง (Auto Signals) ด้วย

### 🛠️ Patch v1.4.4: TradingView Data Integration
**สถานะ: ดำเนินการแล้วเสร็จ**
- **TradingView Engine:** เปลี่ยนระบบดึงข้อมูลจาก `yfinance` เป็น `tradingview-ta` แก้ปัญหา API โดนบล็อก และได้ราคากับอินดิเคเตอร์ตรงกับกราฟ TradingView จริงแบบ 100% (อ้างอิง OANDA:XAUUSD)

### Completed (Patch 1.4.7) 🧠
- Added `order_status` detection (ACTIVE vs PENDING) to `vision.py`.
- Updated Trade Management Agent to handle Pending Orders (WAIT_PENDING, CANCEL_PENDING).
- Translated Action outputs into Thai for better user experience.

### Completed (Patch 1.4.6) 🐞
**สถานะ: ดำเนินการแล้วเสร็จ**
- Fixed Dual-Scheduler not running (Migrated schedule loop to `bot.py` via `discord.ext.tasks`).
- Added debug logging for `on_message` image attachments.
- Verified Discord Developer Intent (`Message Content`).

### 🛠️ Patch v1.4.5: Dual-Scheduler Logic
**สถานะ: ดำเนินการแล้วเสร็จ**
- **Routine Update (ทุก 4 ชม.):** รายงานสถานการณ์ตลาดและพฤติกรรมกราฟเสมอ แม้ว่าจะยังไม่มีสัญญาณเข้าเทรด
- **Sniper Scanner (ทุก 15 นาที):** สแกนตลาดเบื้องหลังเงียบๆ และแจ้งเตือนทันทีที่พบสัญญาณ (BUY/SELL) โดยข้ามการแจ้งเตือนแบบ WAIT เพื่อลดการสแปม

---

## 🚀 Upcoming Patches (แผนพัฒนาในอนาคต)

### ⚙️ Patch v1.5: Trading Journal & Analytics
- **Win-Rate Tracker:** เก็บประวัติการเทรดลงไฟล์ `.csv` อัตโนมัติ เพื่อนำมาประเมินผลความแม่นยำย้อนหลัง (Backtesting)
- **Position Sizing Calculator:** รับค่าเงินทุนในพอร์ต (Account Balance) แล้วให้ AI คำนวณ Lot Size ที่ควรเปิด โดยให้ความเสี่ยงไม่เกิน 1-2% ของพอร์ต

### 📈 Patch v1.5: Machine Learning Forecasting
**เป้าหมาย:** นำข้อมูลสถิติมาพยากรณ์ล่วงหน้า
- **AI Price Prediction:** ใช้โมเดล Machine Learning (เช่น LSTM หรือ XGBoost) วิเคราะห์ราคาย้อนหลังเพื่อทำนายทิศทางราคาล่วงหน้า 24 ชม.
- **Sentiment Analysis Pipeline:** พัฒนาตัวจับความรู้สึกจาก Twitter/Reddit แบบ Real-time เพื่อประเมินความตื่นตระหนกของตลาด (Fear & Greed Index)

### 🤖 Patch v2.0: Full Auto-Execution (เทรดอัตโนมัติ 100%)
**เป้าหมาย:** ให้บอทส่งคำสั่งซื้อขายจริงเข้าพอร์ตทันทีที่มั่นใจ
- **เชื่อมต่อ Broker API:** เชื่อมต่อกับแพลตฟอร์มเทรด เช่น `MetaTrader 5 (MT5)`, `cTrader` หรือโบรกเกอร์ที่มี API รองรับ
- **One-Click Approval:** (ระบบความปลอดภัยทางเลือก) ให้บอทส่งแผนมาในมือถือพร้อมปุ่ม [Approve] ถ้าเจ้านายกดปุ่ม บอทถึงจะยิงออเดอร์เข้าพอร์ตจริง
- **Trailing Stop Automation:** ให้บอทขยับจุดตัดขาดทุนตามกำไร (กันทุน) เมื่อราคาเริ่มวิ่งไปในทิศทางที่คาดการณ์ไว้
