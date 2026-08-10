# 🤖 Gold Trading AI Crew

โปรเจกต์บอทเทรดทองคำ (Gold Futures / XAUUSD) ที่ขับเคลื่อนด้วยเทคโนโลยี Multi-Agent System จาก **CrewAI** และประมวลผลความคิดด้วย **Google Gemini API** โดยแบ่งหน้าที่การวิเคราะห์ให้กับ AI 3 บทบาท เพื่อความแม่นยำในการวางแผนเทรด:

1. **Macro & Sentiment Analyst:** วิเคราะห์ข่าวสารเศรษฐกิจมหภาค (ดอกเบี้ย FED, ดัชนี DXY, ข่าวภูมิรัฐศาสตร์)
2. **Technical Analyst:** วิเคราะห์กราฟเทคนิคอล (RSI, Moving Average) โดยดึงข้อมูลราคา Real-time ผ่าน `yfinance`
3. **Chief Gold Trader (Portfolio Manager):** นำข้อมูลทั้งหมดมาสรุปเป็นแผนการเทรดที่ชัดเจน (จุดเข้า, Stop Loss, Take Profit)

---

## 📋 สิ่งที่ต้องเตรียม (Prerequisites)
- Python 3.10 หรือใหม่กว่า
- [Google Gemini API Key](https://aistudio.google.com/app/apikey) (แนะนำให้สร้างคีย์จาก Google AI Studio แบบโปรเจกต์ใหม่ เพื่อใช้งาน Free Tier แบบไม่มีเงื่อนไขผูกบัตร)

---

## 🛠️ วิธีติดตั้ง (Installation)

1. **Clone repository นี้ลงเครื่องของคุณ:**
   ```bash
   git clone https://github.com/somchokw/goldTrader.git
   cd goldTrader
   ```

2. **สร้าง Virtual Environment และเปิดใช้งาน:**
   ```bash
   # สำหรับ macOS/Linux
   python3 -m venv venv
   source venv/bin/activate

   # สำหรับ Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **ติดตั้งไลบรารีที่จำเป็นทั้งหมด:**
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ การตั้งค่าระบบ (Configuration)

1. ก๊อปปี้ไฟล์ `.env.example` แล้วเปลี่ยนชื่อเป็น `.env`:
   ```bash
   cp .env.example .env
   ```
2. เปิดไฟล์ `.env` ขึ้นมา แล้วนำ **Gemini API Key** ของคุณไปใส่:
   ```env
   GEMINI_API_KEY=ใส่_API_KEY_ของคุณที่นี่
   ```

---

## 🚀 วิธีใช้งาน (Usage)

เมื่อติดตั้งและตั้งค่าเสร็จแล้ว สามารถสั่งให้บอทเริ่มประชุมและวิเคราะห์แผนการเทรดได้ทันทีด้วยคำสั่ง:

```bash
python main.py
```

รอประมาณ 15-30 วินาที AI จะทำการวิเคราะห์ข้อมูลเรียลไทม์ และพิมพ์ **"แผนการเทรด (Trading Strategy)"** พร้อมจุดเข้าซื้อ-ขาย สรุปออกมาทางหน้าจอ Terminal ครับ!

---

## ⚠️ คำเตือน (Disclaimer)
โปรเจกต์นี้สร้างขึ้นเพื่อการศึกษาและการวิเคราะห์ข้อมูลเบื้องต้นเท่านั้น ตลาดการลงทุนมีความเสี่ยงสูง แผนการเทรดที่ได้จาก AI ควรถูกนำไปวิเคราะห์ร่วมกับการตัดสินใจส่วนบุคคลก่อนนำไปลงทุนจริง 
