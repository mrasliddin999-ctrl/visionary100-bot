import os
import json
import asyncio
import logging
from datetime import datetime, time
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
DATA_FILE = "users.json"

# ===== MA'LUMOTLAR =====
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(chat_id: str):
    data = load_data()
    return data.get(str(chat_id), {})

def save_user(chat_id: str, user_data: dict):
    data = load_data()
    data[str(chat_id)] = user_data
    save_data(data)

# ===== KOMANDALAR =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    
    existing = get_user(chat_id)
    if not existing:
        save_user(chat_id, {
            "name": user.first_name,
            "username": user.username or "",
            "goals": {},
            "remind_time": "09:00",
            "active": True,
            "joined": datetime.now().isoformat()
        })
    
    keyboard = [
        [InlineKeyboardButton("📋 Maqsadlarim", callback_data="my_goals")],
        [InlineKeyboardButton("⏰ Eslatma vaqtini sozlash", callback_data="set_time")],
        [InlineKeyboardButton("📊 Statistika", callback_data="stats")],
        [InlineKeyboardButton("ℹ️ Yordam", callback_data="help")],
    ]
    
    await update.message.reply_text(
        f"🌟 Salom, {user.first_name}!\n\n"
        f"Men <b>Visionary 100</b> botiman — sizning 100 yillik maqsadlaringiz yordamchisi!\n\n"
        f"🎯 Saytda qo'ygan maqsadlaringizni har kuni eslatib turaman.\n"
        f"📱 Telegram ID ingiz: <code>{chat_id}</code>\n\n"
        f"Bu ID ni Visionary 100 saytiga kiriting!",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📚 <b>Buyruqlar:</b>\n\n"
        "/start — Botni ishga tushirish\n"
        "/maqsadlar — Barcha maqsadlarimni ko'rish\n"
        "/bugun — Bugungi eslatma\n"
        "/vaqt — Eslatma vaqtini o'zgartirish\n"
        "/statistika — Maqsadlar statistikasi\n"
        "/id — Telegram ID ni ko'rish\n"
        "/stop — Eslatmalarni to'xtatish\n"
        "/start — Eslatmalarni qayta yoqish\n\n"
        "💡 Saytda maqsad qo'shing → bot avtomatik eslatadi!"
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="HTML")
    else:
        await update.message.reply_text(text, parse_mode="HTML")

async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"🆔 Sizning Telegram ID ingiz:\n\n"
        f"<code>{chat_id}</code>\n\n"
        f"Bu raqamni Visionary 100 saytidagi profilingizga kiriting!",
        parse_mode="HTML"
    )

async def my_goals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = get_user(chat_id)
    goals = user.get("goals", {})
    
    if not goals:
        text = (
            "📋 Hozircha maqsadlaringiz yo'q.\n\n"
            "Visionary 100 saytiga kiring va maqsad qo'shing! 🎯"
        )
    else:
        lines = ["📋 <b>Sizning maqsadlaringiz:</b>\n"]
        
        weekly = {k: v for k, v in goals.items() if k.startswith("w_")}
        monthly = {k: v for k, v in goals.items() if k.startswith("m_")}
        yearly = {k: v for k, v in goals.items() if k.startswith("y_")}
        decade = {k: v for k, v in goals.items() if k.startswith("d_")}
        
        if weekly:
            lines.append("📅 <b>Haftalik:</b>")
            for k, v in list(weekly.items())[:5]:
                lines.append(f"  ✅ {v}")
        if monthly:
            lines.append("\n🗓️ <b>Oylik:</b>")
            for k, v in list(monthly.items())[:5]:
                lines.append(f"  ✅ {v}")
        if yearly:
            lines.append("\n📆 <b>Yillik:</b>")
            for k, v in list(yearly.items())[:3]:
                lines.append(f"  ✅ {v}")
        if decade:
            lines.append("\n🚀 <b>10 yillik:</b>")
            for k, v in list(decade.items())[:2]:
                lines.append(f"  ✅ {v}")
        
        total = len(goals)
        lines.append(f"\n<b>Jami: {total} ta maqsad</b> 🎯")
        text = "\n".join(lines)
    
    keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")]]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(text, parse_mode="HTML")

async def bugun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    await send_daily_reminder(context.bot, chat_id)

async def statistika(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = get_user(chat_id)
    goals = user.get("goals", {})
    
    weekly = len([k for k in goals if k.startswith("w_")])
    monthly = len([k for k in goals if k.startswith("m_")])
    yearly = len([k for k in goals if k.startswith("y_")])
    decade = len([k for k in goals if k.startswith("d_")])
    total = weekly + monthly + yearly + decade
    
    # Progress foizi
    w_pct = min(100, int(weekly / 52 * 100))
    m_pct = min(100, int(monthly / 12 * 100))
    y_pct = min(100, int(yearly / 100 * 100))
    d_pct = min(100, int(decade / 10 * 100))
    
    def bar(pct):
        filled = int(pct / 10)
        return "█" * filled + "░" * (10 - filled)
    
    text = (
        f"📊 <b>Maqsadlar statistikasi</b>\n\n"
        f"📅 Haftalik: {weekly}/52\n"
        f"{bar(w_pct)} {w_pct}%\n\n"
        f"🗓️ Oylik: {monthly}/12\n"
        f"{bar(m_pct)} {m_pct}%\n\n"
        f"📆 Yillik: {yearly}/100\n"
        f"{bar(y_pct)} {y_pct}%\n\n"
        f"🚀 10 yillik: {decade}/10\n"
        f"{bar(d_pct)} {d_pct}%\n\n"
        f"🎯 <b>Jami: {total} ta maqsad</b>\n"
        f"💪 Davom eting!"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")]]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(text, parse_mode="HTML")

async def set_time_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "⏰ <b>Eslatma vaqtini o'zgartirish</b>\n\n"
        "Vaqtni HH:MM formatda yuboring:\n"
        "Masalan: <code>08:00</code> yoki <code>21:30</code>"
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="HTML")
    else:
        await update.message.reply_text(text, parse_mode="HTML")
    
    context.user_data["waiting_time"] = True

async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = get_user(chat_id)
    user["active"] = False
    save_user(chat_id, user)
    await update.message.reply_text(
        "⏸ Eslatmalar to'xtatildi.\n"
        "Qayta yoqish uchun /start bosing."
    )

# ===== CALLBACK HANDLER =====
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "my_goals":
        await my_goals(update, context)
    elif data == "set_time":
        await set_time_cmd(update, context)
    elif data == "stats":
        await statistika(update, context)
    elif data == "help":
        await help_cmd(update, context)
    elif data == "back_main":
        keyboard = [
            [InlineKeyboardButton("📋 Maqsadlarim", callback_data="my_goals")],
            [InlineKeyboardButton("⏰ Eslatma vaqtini sozlash", callback_data="set_time")],
            [InlineKeyboardButton("📊 Statistika", callback_data="stats")],
            [InlineKeyboardButton("ℹ️ Yordam", callback_data="help")],
        ]
        await query.edit_message_text(
            "🌟 <b>Visionary 100 Bot</b>\n\nNimani xohlaysiz?",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ===== MESSAGE HANDLER =====
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    text = update.message.text.strip()
    
    # Vaqt kutilmoqda
    if context.user_data.get("waiting_time"):
        try:
            parts = text.split(":")
            h, m = int(parts[0]), int(parts[1])
            if 0 <= h <= 23 and 0 <= m <= 59:
                user = get_user(chat_id)
                user["remind_time"] = f"{h:02d}:{m:02d}"
                save_user(chat_id, user)
                context.user_data["waiting_time"] = False
                await update.message.reply_text(
                    f"✅ Eslatma vaqti {h:02d}:{m:02d} ga o'rnatildi!\n"
                    f"Har kuni shu vaqtda maqsadlaringizni eslataman. 🔔"
                )
            else:
                await update.message.reply_text("❌ Noto'g'ri vaqt! Masalan: 09:00")
        except:
            await update.message.reply_text("❌ Noto'g'ri format! Masalan: 09:00")
        return
    
    await update.message.reply_text(
        "💡 Buyruqlarni ko'rish uchun /help yozing yoki tugmalardan foydalaning.",
    )

# ===== KUNLIK ESLATMA =====
async def send_daily_reminder(bot, chat_id: str):
    user = get_user(chat_id)
    if not user or not user.get("active", True):
        return
    
    goals = user.get("goals", {})
    name = user.get("name", "Do'stim")
    now = datetime.now()
    
    # Haftaning kuni
    days_uz = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
    day_name = days_uz[now.weekday()]
    
    if not goals:
        text = (
            f"🌅 Xayrli tong, {name}!\n\n"
            f"📅 Bugun {day_name}, {now.strftime('%d.%m.%Y')}\n\n"
            f"💡 Hali maqsad qo'ymagan ekansiz!\n"
            f"Visionary 100 saytiga kiring va maqsadlaringizni belgilang. 🎯"
        )
    else:
        # Mos kelgan maqsadlarni topish
        week_num = now.isocalendar()[1]
        month = now.month
        year = now.year
        
        today_goals = []
        
        # Haftalik (joriy hafta)
        for k, v in goals.items():
            if k.startswith("w_"):
                today_goals.append(("📅 Haftalik", v))
            elif k.startswith(f"m_{year}_{month}_"):
                today_goals.append(("🗓️ Oylik", v))
        
        if today_goals:
            lines = [
                f"🌅 Xayrli tong, {name}!",
                f"📅 Bugun {day_name}, {now.strftime('%d.%m.%Y')}",
                "",
                "🎯 <b>Bugungi maqsadlaringiz:</b>",
                ""
            ]
            for label, goal in today_goals[:5]:
                lines.append(f"{label}: <b>{goal}</b>")
            
            lines.extend([
                "",
                "💪 Bugun ham bir qadam oldinga!",
                "✨ Muvaffaqiyat!"
            ])
            text = "\n".join(lines)
        else:
            # Random maqsad
            import random
            all_goals = list(goals.values())
            random_goal = random.choice(all_goals) if all_goals else None
            
            if random_goal:
                text = (
                    f"🌅 Xayrli tong, {name}!\n"
                    f"📅 Bugun {day_name}, {now.strftime('%d.%m.%Y')}\n\n"
                    f"💡 Eslatma:\n"
                    f"<b>«{random_goal}»</b>\n\n"
                    f"Bu maqsadingiz sari bugun bir qadam qo'ying! 🚀"
                )
            else:
                text = f"🌅 Xayrli tong, {name}! Bugun ham zo'r kun bo'lsin! 💪"
    
    try:
        await bot.send_message(
            chat_id=int(chat_id),
            text=text,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Xabar yuborishda xatolik {chat_id}: {e}")

# ===== KUNLIK SCHEDULER =====
async def daily_job(context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    
    for chat_id, user in data.items():
        if not user.get("active", True):
            continue
        remind_time = user.get("remind_time", "09:00")
        if remind_time == current_time:
            await send_daily_reminder(context.bot, chat_id)

# ===== WEBHOOK (Railway uchun) =====
async def main():
    app = Application.builder().token(TOKEN).build()
    
    # Handlerlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("id", my_id))
    app.add_handler(CommandHandler("maqsadlar", my_goals))
    app.add_handler(CommandHandler("bugun", bugun))
    app.add_handler(CommandHandler("statistika", statistika))
    app.add_handler(CommandHandler("vaqt", set_time_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Har daqiqa scheduler
    app.job_queue.run_repeating(daily_job, interval=60, first=10)
    
    logger.info("Bot ishga tushdi!")
    await app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
