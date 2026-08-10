# 🗺️ Gold Trading AI Crew - Development Roadmap

เพื่อให้ระบบ "Gold Trading Crew" มีความสามารถที่แข็งแกร่งขึ้น และใช้งานได้อัตโนมัติ 100% นี่คือแผนการพัฒนา (Patch Updates) ที่เราวางไว้สำหรับโปรเจกต์นี้ครับ:

---

## ✅ Completed Patches (ดำเนินการแล้ว)

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
