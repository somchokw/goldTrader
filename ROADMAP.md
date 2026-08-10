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
**สถานะ: ดำเนินการแล้วเสร็จ**
- **Risk Manager Agent:** วิเคราะห์ระยะห่าง Stop Loss จากจุดเข้าเพื่อคำนวณความเสี่ยงเป็นดอลลาร์
- **Dual Risk Matrix:** คำนวณตารางขนาดหลอด (Lot Size) ให้ 2 รูปแบบ ทั้งสายปลอดภัย (Safe Mode) สำหรับคนตามซิกแนล และสายปั้นพอร์ต (Sniper Mode) สำหรับรันทุนน้อย 

---

## 🚀 Upcoming Patches (แผนพัฒนาในอนาคต)

### 🤖 Patch v1.4: Auto-Trading Execution (เทรดอัตโนมัติบน MT4/MT5)
- **Position Sizing Calculator:** รับค่าเงินทุนในพอร์ต (Account Balance) แล้วให้ AI คำนวณ Lot Size ที่ควรเปิด โดยให้ความเสี่ยงไม่เกิน 1-2% ของพอร์ต
- **Win-Rate Tracker:** เก็บประวัติการเทรดลงไฟล์ `.csv` อัตโนมัติ เพื่อนำมาประเมินผลความแม่นยำย้อนหลัง (Backtesting)

### 📈 Patch v1.5: Machine Learning Forecasting
**เป้าหมาย:** นำข้อมูลสถิติมาพยากรณ์ล่วงหน้า
- **AI Price Prediction:** ใช้โมเดล Machine Learning (เช่น LSTM หรือ XGBoost) วิเคราะห์ราคาย้อนหลังเพื่อทำนายทิศทางราคาล่วงหน้า 24 ชม.
- **Sentiment Analysis Pipeline:** พัฒนาตัวจับความรู้สึกจาก Twitter/Reddit แบบ Real-time เพื่อประเมินความตื่นตระหนกของตลาด (Fear & Greed Index)

### 🤖 Patch v2.0: Full Auto-Execution (เทรดอัตโนมัติ 100%)
**เป้าหมาย:** ให้บอทส่งคำสั่งซื้อขายจริงเข้าพอร์ตทันทีที่มั่นใจ
- **เชื่อมต่อ Broker API:** เชื่อมต่อกับแพลตฟอร์มเทรด เช่น `MetaTrader 5 (MT5)`, `cTrader` หรือโบรกเกอร์ที่มี API รองรับ
- **One-Click Approval:** (ระบบความปลอดภัยทางเลือก) ให้บอทส่งแผนมาในมือถือพร้อมปุ่ม [Approve] ถ้าเจ้านายกดปุ่ม บอทถึงจะยิงออเดอร์เข้าพอร์ตจริง
- **Trailing Stop Automation:** ให้บอทขยับจุดตัดขาดทุนตามกำไร (กันทุน) เมื่อราคาเริ่มวิ่งไปในทิศทางที่คาดการณ์ไว้
