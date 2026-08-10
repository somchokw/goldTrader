# 📝 Patch Notes

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
