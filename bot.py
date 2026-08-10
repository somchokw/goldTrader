import discord
from discord.ext import tasks
import asyncio
import logging
from config import DISCORD_BOT_TOKEN, GEMINI_API_KEY
from scheduler import run_trading_cycle
from vision import extract_order_from_image
from agents import create_trade_management_crew
import os

logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@tasks.loop(hours=4)
async def scheduled_trading_cycle():
    logger.info("Running scheduled trading cycle via Discord loop.")
    await asyncio.to_thread(run_trading_cycle)

@scheduled_trading_cycle.before_loop
async def before_scheduled_cycle():
    await client.wait_until_ready()

@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user}')
    if not scheduled_trading_cycle.is_running():
        scheduled_trading_cycle.start()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Check for image attachments
    if message.attachments:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg']):
                await message.channel.send("📸 กำลังวิเคราะห์รูปภาพพอร์ตของคุณ โปรดรอสักครู่...")
                
                try:
                    # Download image bytes
                    image_bytes = await attachment.read()
                    
                    # 1. OCR Extract values
                    await message.channel.send("🔍 กำลังดึงตัวเลขจากรูปภาพ (Entry, TP, SL)...")
                    order_details = await asyncio.to_thread(extract_order_from_image, image_bytes)
                    
                    # Check for missing fields
                    missing_fields = []
                    if order_details.action is None: missing_fields.append("ฝั่งที่เปิด (BUY หรือ SELL)")
                    if order_details.entry_price is None: missing_fields.append("ราคาเข้า (Entry Price)")
                    if order_details.current_price is None: missing_fields.append("ราคาปัจจุบัน (Current Price)")
                    
                    if missing_fields:
                        missing_str = ", ".join(missing_fields)
                        await message.reply(f"⚠️ รูปภาพที่คุณส่งมาเห็นข้อมูลไม่ครบถ้วนครับ\nบอทมองไม่เห็นข้อมูลดังต่อไปนี้: **{missing_str}**\n\nรบกวนพิมพ์บอกข้อมูลที่ขาดหายไป หรือแคปรูปที่เห็นชัดเจนกว่านี้มาใหม่อีกครั้งนะครับ!")
                        return
                        
                    # Handle SL/TP if missing (warn but proceed)
                    sl_val = order_details.stop_loss if order_details.stop_loss is not None else 0.0
                    tp_val = order_details.take_profit if order_details.take_profit is not None else 0.0
                    
                    # 2. Run Trade Management Agent
                    await message.channel.send(f"✅ อ่านค่าได้แล้ว:\n`Action: {order_details.action} | Entry: {order_details.entry_price} | Current: {order_details.current_price} | SL: {sl_val} | TP: {tp_val}`\n\nกำลังประเมินหน้าตักและเทรนด์ปัจจุบัน...")
                    
                    # Prepare dict for CrewAI
                    order_dict = {
                        "action": order_details.action,
                        "entry_price": order_details.entry_price,
                        "current_price": order_details.current_price,
                        "stop_loss": sl_val,
                        "take_profit": tp_val
                    }
                    crew = create_trade_management_crew(order_dict)
                    result = await asyncio.to_thread(crew.kickoff)
                    
                    plan = getattr(result, 'pydantic', None)
                    if not plan:
                        await message.channel.send("❌ Error: Agent ไม่สามารถคืนค่า TradeManagementPlan ได้")
                        return
                    
                    # 3. Format Reply
                    reply = f"**Trade Management AI (Patch 1.4)**\n\n"
                    reply += f"**Action:** `{plan.action}`\n"
                    if plan.action in ["RAISE_SL", "HOLD", "ADD_POSITION"]:
                        reply += f"**Suggested SL:** {plan.suggested_sl}\n"
                        reply += f"**Suggested TP:** {plan.suggested_tp}\n"
                    
                    reply += f"\n**Rationale:**\n{plan.rationale}"
                    
                    await message.reply(reply)
                    
                except Exception as e:
                    logger.error(f"Error processing image: {e}", exc_info=True)
                    await message.channel.send(f"❌ เกิดข้อผิดพลาดในการวิเคราะห์รูป: {str(e)}")

def run_bot():
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is missing! Fail fast.")
        exit(1)
    if not DISCORD_BOT_TOKEN:
        logger.error("DISCORD_BOT_TOKEN is missing! Fail fast.")
        exit(1)
        
    client.run(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    run_bot()
