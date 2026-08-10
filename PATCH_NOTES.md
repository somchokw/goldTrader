# 📝 Patch Notes

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
