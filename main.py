import os
import sqlite3
import logging
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= BASIC CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_FILE = "focus_bot.db"


# ================= DATABASE =================

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS targets (
            user_id INTEGER PRIMARY KEY,
            target TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mood_logs (
            user_id INTEGER,
            mood TEXT,
            date TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_target(user_id: int, target: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO targets (user_id, target)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET target=excluded.target
    """, (user_id, target))
    conn.commit()
    conn.close()


def get_target(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT target FROM targets WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def save_mood(user_id: int, mood: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO mood_logs (user_id, mood, date) VALUES (?, ?, ?)",
                   (user_id, mood, date))
    conn.commit()
    conn.close()


# ================= MENU =================

def main_menu():
    keyboard = [
        [InlineKeyboardButton("📅 Fokus Hari Ini", callback_data="focus")],
        [InlineKeyboardButton("🎯 Target Pribadi", callback_data="target")],
        [InlineKeyboardButton("⏳ Timer Fokus 25 Menit", callback_data="timer")],
        [InlineKeyboardButton("😊 Catatan Mood", callback_data="mood")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Selamat datang di Daily Focus Assistant.\n\n"
        "Bot ini membantu kamu mengatur fokus dan produktivitas harian.\n"
        "Pilih fitur di bawah."
    )
    await update.message.reply_text(text, reply_markup=main_menu())


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Daily Focus Assistant adalah bot produktivitas sederhana.\n\n"
        "Bot ini tidak menyediakan:\n"
        "- Hadiah\n"
        "- Sistem poin\n"
        "- Uang\n"
        "- Investasi\n"
        "- Permainan\n\n"
        "Hanya alat bantu fokus dan pengembangan diri."
    )
    await update.message.reply_text(text)


async def privacy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Kebijakan Privasi:\n\n"
        "Bot ini tidak menyimpan data pribadi di luar Telegram.\n"
        "Data hanya digunakan untuk fungsi internal bot.\n"
        "Tidak dibagikan ke pihak ketiga."
    )
    await update.message.reply_text(text)


# ================= BUTTON HANDLER =================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "focus":
        today = datetime.now().strftime("%d %B %Y")
        text = (
            f"📅 Fokus Hari Ini ({today})\n\n"
            "Tuliskan satu prioritas utama kamu hari ini."
        )
        context.user_data["awaiting_focus"] = True
        await query.edit_message_text(text, reply_markup=main_menu())

    elif query.data == "target":
        text = (
            "🎯 Target Pribadi\n\n"
            "Ketik target kamu sekarang.\n"
            "Target sebelumnya akan diperbarui."
        )
        context.user_data["awaiting_target"] = True
        await query.edit_message_text(text, reply_markup=main_menu())

    elif query.data == "timer":
        context.user_data["timer_start"] = datetime.now()
        text = (
            "⏳ Timer Fokus dimulai.\n"
            "Silakan fokus selama 25 menit.\n"
            "Gunakan /stoptimer untuk menghentikan timer."
        )
        await query.edit_message_text(text, reply_markup=main_menu())

    elif query.data == "mood":
        text = (
            "😊 Catatan Mood\n\n"
            "Ketik suasana hati kamu hari ini:\n"
            "Contoh: Bahagia, Netral, Lelah, Termotivasi"
        )
        context.user_data["awaiting_mood"] = True
        await query.edit_message_text(text, reply_markup=main_menu())


# ================= MESSAGE HANDLER =================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if context.user_data.get("awaiting_target"):
        save_target(user_id, text)
        context.user_data["awaiting_target"] = False
        await update.message.reply_text("🎯 Target berhasil disimpan.")
        return

    if context.user_data.get("awaiting_mood"):
        save_mood(user_id, text)
        context.user_data["awaiting_mood"] = False
        await update.message.reply_text("😊 Catatan mood disimpan.")
        return

    if context.user_data.get("awaiting_focus"):
        context.user_data["awaiting_focus"] = False
        await update.message.reply_text("📅 Prioritas hari ini dicatat.")
        return


# ================= TIMER =================

async def stop_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = context.user_data.get("timer_start")

    if not start:
        await update.message.reply_text("Timer belum dimulai.")
        return

    duration = (datetime.now() - start).seconds // 60
    await update.message.reply_text(
        f"⏱ Kamu fokus selama {duration} menit.\nKerja bagus."
    )


# ================= MAIN =================

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN belum diatur!")

    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("privacy", privacy))
    app.add_handler(CommandHandler("stoptimer", stop_timer))

    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Daily Focus Assistant berjalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
