import os
import json
import asyncio
import logging
from datetime import datetime
 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
TOKEN = os.environ.get("BOT_TOKEN", "")
DATA_FILE = "users.json"
 
# ===== STORAGE =====
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}
 
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
 
def get_user(chat_id):
    return load_data().get(str(chat_id), {})
 
def save_user(chat_id, user_data):
    data = load_data()
    data[str(chat_id)] = user_data
    save_data(data)
 
# ===== MAIN MENU =====
def main_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Maqsadlarim", callback_data="my_goals")],
        [InlineKeyboardButton("📊 Statistika", callback_data="stats")],
        [InlineKeyboardButton("⏰ Eslatma vaqti", callback_data="set_time")],
        [InlineKeyboardButton("🆔 Mening ID im", callback_data="my_id")],
        [InlineKeyboardButton("ℹ️ Yordam", callback_data="help")],
    ])
 
# ===== /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    
    if not get_user(chat_id):
        save_user(chat_id, {
            "name": user.first_name,
            "username": user.username or "",
            "goals": {},
            "remind_time": "09:00",
            "active": True,
            "joined": datetime.now().isoformat()
        })
    
    await update.message.reply_text(
        f"🌟 Salom, <b>{user.first_name}</b>!\n\n"
        f"Men <b>Visionary 100</b> botiman!\n"
        f"Sizning 100 yillik maqsadlaringizni har kuni eslatib turaman.\n\n"
        f"📱 <b>Sizning Telegram ID:</b>\n<code>{chat_id}</code>\n\n"
        f"⬆️ Bu ID ni Visionary 100 saytidagi profilingizga kiriting!",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )
 
# ===== /id =====
async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = (
        f"🆔 <b>Sizning Telegram ID:</b>\n\n"
        f"<code>{chat_id}</code>\n\n"
        f"Bu ID ni Visionary 100 saytidagi profilingizga kiriting!"
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back")]]))
    else:
        await update.message.reply_text(text, parse_mode="HTML")
 
# ===== /maqsadlar =====
async def my_goals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = get_user(chat_id)
    goals = user.get("goals", {})
    
    if not goals:
        text = "📋 Hozircha maqsadlaringiz yo'q.\n\nVisionary 100 saytiga kiring va maqsad qo'shing! 🎯"
    else:
        lines = ["📋 <b>Sizning maqsadlaringiz:</b>\n"]
        w = [(k,v) for k,v in goals.items() if k.startswith("w_")]
        m = [(k,v) for k,v in goals.items() if k.startswith("m_")]
        y = [(k,v) for k,v in goals.items() if k.startswith("y_")]
        d = [(k,v) for k,v in goals.items() if k.startswith("d_")]
        
        if w:
            lines.append("📅 <b>Haftalik:</b>")
            for _,v in w[:5]: lines.append(f"  • {v}")
        if m:
            lines.append("\n🗓️ <b>Oylik:</b>")
            for _,v in m[:5]: lines.append(f"  • {v}")
        if y:
            lines.append("\n📆 <b>Yillik:</b>")
            for _,v in y[:3]: lines.append(f"  • {v}")
        if d:
            lines.append("\n🚀 <b>10 yillik:</b>")
            for _,v in d[:2]: lines.append(f"  • {v}")
        
        lines.append(f"\n🎯 <b>Jami: {len(goals)} ta maqsad</b>")
        text = "\n".join(lines)
    
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back")]])
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb)
 
# ===== /statistika =====
async def statistika(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = get_user(chat_id)
    goals = user.get("goals", {})
    
    wc = len([k for k in goals if k.startswith("w_")])
    mc = len([k for k in goals if k.startswith("m_")])
    yc = len([k for k in goals if k.startswith("y_")])
    dc = len([k for k in goals if k.startswith("d_")])
    total = wc + mc + yc + dc
    
    def bar(n, mx):
        pct = min(100, int(n/mx*100)) if mx else 0
        f = int(pct/10)
        return f"{'█'*f}{'░'*(10-f)} {pct}%"
    
    text = (
        f"📊 <b>Maqsadlar statistikasi</b>\n\n"
        f"📅 Haftalik: {wc}/52\n{bar(wc,52)}\n\n"
        f"🗓️ Oylik: {mc}/12\n{bar(mc,12)}\n\n"
        f"📆 Yillik: {yc}/100\n{bar(yc,100)}\n\n"
        f"🚀 10 yillik: {dc}/10\n{bar(dc,10)}\n\n"
        f"🎯 <b>Jami: {total} ta maqsad</b>\n💪 Davom eting!"
    )
    
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back")]])
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb)
 
# ===== /bugun =====
async def bugun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    await send_reminder(context.bot, chat_id, update)
 
async def send_reminder(bot, chat_id, update=None):
    user = get_user(chat_id)
    if not user:
        return
    goals = user.get("goals", {})
    name = user.get("name", "Do'stim")
    now = datetime.now()
    days = ["Dushanba","Seshanba","Chorshanba","Payshanba","Juma","Shanba","Yakshanba"]
    day = days[now.weekday()]
    
    if not goals:
        text = (
            f"🌅 Xayrli tong, <b>{name}</b>!\n"
            f"📅 {day}, {now.strftime('%d.%m.%Y')}\n\n"
            f"💡 Hali maqsad qo'ymagan ekansiz!\n"
            f"Visionary 100 saytiga kiring! 🎯"
        )
    else:
        import random
        all_goals = list(goals.values())
        goal = random.choice(all_goals)
        text = (
            f"🌅 Xayrli tong, <b>{name}</b>!\n"
            f"📅 {day}, {now.strftime('%d.%m.%Y')}\n\n"
            f"🎯 <b>Bugungi eslatma:</b>\n"
            f"<i>«{goal}»</i>\n\n"
            f"💪 Bugun ham bir qadam oldinga!\n"
            f"✨ Muvaffaqiyat!"
        )
    
    if update:
        await update.message.reply_text(text, parse_mode="HTML")
    else:
        try:
            await bot.send_message(chat_id=int(chat_id), text=text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Error sending to {chat_id}: {e}")
 
# ===== /vaqt =====
async def vaqt_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "⏰ <b>Eslatma vaqtini o'zgartirish</b>\n\n"
        "Vaqtni <b>HH:MM</b> formatda yuboring:\n"
        "Masalan: <code>08:00</code> yoki <code>21:30</code>"
    )
    context.user_data["waiting_time"] = True
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="HTML")
    else:
        await update.message.reply_text(text, parse_mode="HTML")
 
# ===== /stop =====
async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    user = get_user(chat_id)
    user["active"] = False
    save_user(chat_id, user)
    await update.message.reply_text("⏸ Eslatmalar to'xtatildi.\n/start — qayta yoqish.")
 
# ===== CALLBACK =====
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = q.data
    if d == "my_goals": await my_goals(update, context)
    elif d == "stats": await statistika(update, context)
    elif d == "set_time": await vaqt_cmd(update, context)
    elif d == "my_id": await my_id(update, context)
    elif d == "help": await help_cmd(update, context)
    elif d == "back":
        await q.edit_message_text(
            "🌟 <b>Visionary 100 Bot</b>\n\nNimani xohlaysiz?",
            parse_mode="HTML", reply_markup=main_menu_kb()
        )
 
# ===== HELP =====
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📚 <b>Buyruqlar:</b>\n\n"
        "/start — Botni ishga tushirish\n"
        "/id — Telegram ID ni ko'rish\n"
        "/maqsadlar — Barcha maqsadlar\n"
        "/bugun — Bugungi eslatma\n"
        "/statistika — Progress\n"
        "/vaqt — Eslatma vaqtini o'zgartirish\n"
        "/stop — Eslatmalarni to'xtatish"
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back")]]))
    else:
        await update.message.reply_text(text, parse_mode="HTML")
 
# ===== MESSAGE =====
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    text = update.message.text.strip()
    
    if context.user_data.get("waiting_time"):
        try:
            h, m = map(int, text.split(":"))
            if 0 <= h <= 23 and 0 <= m <= 59:
                user = get_user(chat_id)
                user["remind_time"] = f"{h:02d}:{m:02d}"
                save_user(chat_id, user)
                context.user_data["waiting_time"] = False
                await update.message.reply_text(
                    f"✅ Eslatma vaqti <b>{h:02d}:{m:02d}</b> ga o'rnatildi! 🔔",
                    parse_mode="HTML", reply_markup=main_menu_kb()
                )
            else:
                await update.message.reply_text("❌ Noto'g'ri vaqt! Masalan: <code>09:00</code>", parse_mode="HTML")
        except:
            await update.message.reply_text("❌ Noto'g'ri format! Masalan: <code>09:00</code>", parse_mode="HTML")
        return
    
    await update.message.reply_text(
        "💡 /help — buyruqlar ro'yxati",
        reply_markup=main_menu_kb()
    )
 
# ===== KUNLIK ESLATMA (alohida task) =====
async def reminder_loop(app):
    while True:
        await asyncio.sleep(60)
        try:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            data = load_data()
            for chat_id, user in data.items():
                if not user.get("active", True):
                    continue
                if user.get("remind_time", "09:00") == current_time:
                    await send_reminder(app.bot, chat_id)
        except Exception as e:
            logger.error(f"Reminder loop error: {e}")
 
# ===== MAIN =====
async def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("id", my_id))
    app.add_handler(CommandHandler("maqsadlar", my_goals))
    app.add_handler(CommandHandler("bugun", bugun))
    app.add_handler(CommandHandler("statistika", statistika))
    app.add_handler(CommandHandler("vaqt", vaqt_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    await app.initialize()
    await app.start()
    
    # Eslatma loop ni parallel ishlatish
    asyncio.create_task(reminder_loop(app))
    
    logger.info("✅ Bot ishga tushdi!")
    await app.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()
 
if __name__ == "__main__":
    asyncio.run(main())
