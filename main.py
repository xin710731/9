import os
import time
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
    ContextTypes,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ================= MENU =================

def main_menu():
    keyboard = [
        [InlineKeyboardButton("📅 Fokus Hari Ini", callback_data="focus")],
        [InlineKeyboardButton("🎯 Target Pribadi", callback_data="target")],
        [InlineKeyboardButton("😊 Catatan Mood", callback_data="mood")],
        [InlineKeyboardButton("⏳ Timer Fokus 25 Menit", callback_data="timer")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ================= START =================

START_TEXT = (
    "👋 Selamat datang di *Daily Focus Assistant*.\n\n"
    "Bot ini membantu kamu:\n"
    "• Mengatur fokus harian\n"
    "• Menetapkan target pribadi\n"
    "• Mencatat suasana hati\n"
    "• Menggunakan timer fokus\n\n"
    "Bot ini hanya menyediakan fitur produktivitas dan pengembangan diri.\n"
    "Tidak ada hadiah, uang, atau sistem permainan.\n\n"
    "Silakan pilih menu di bawah."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        START_TEXT,
        reply_markup=main_menu(),
        parse_mode="Markdown",
    )


# ================= BUTTON HANDLER =================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "focus":
        today = datetime.now().strftime("%d %B %Y")
        text = (
            f"📅 Fokus Hari Ini ({today})\n\n"
            "Tulis 1 hal paling penting yang ingin kamu selesaikan hari ini.\n"
            "Fokus pada satu prioritas saja."
        )
        await query.edit_message_text(text, reply_markup=main_menu())
        return

    if data == "target":
        context.user_data["target"] = "Belum ditentukan"
        text = (
            "🎯 Target Pribadi\n\n"
            "Gunakan /settarget untuk menetapkan target.\n"
            "Gunakan /mytarget untuk melihat target kamu."
        )
        await query.edit_message_text(text, reply_markup=main_menu())
        return

    if data == "mood":
        text = (
            "😊 Catatan Mood\n\n"
            "Bagaimana perasaan kamu hari ini?\n"
            "Ketik salah satu:\n"
            "• Bahagia\n"
            "• Netral\n"
            "• Lelah\n"
            "• Termotivasi"
        )
        await query.edit_message_text(text, reply_markup=main_menu())
        return

    if data == "timer":
        context.user_data["timer_start"] = time.time()
        text = (
            "⏳ Timer Fokus dimulai selama 25 menit.\n\n"
            "Tetap fokus pada satu tugas.\n"
            "Ketik /stoptimer untuk menghentikan timer."
        )
        await query.edit_message_text(text, reply_markup=main_menu())
        return


# ================= TARGET COMMANDS =================

async def set_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan: /settarget tujuan_kamu")
        return

    target = " ".join(context.args)
    context.user_data["target"] = target
    await update.message.reply_text(f"🎯 Target disimpan:\n{target}")


async def my_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = context.user_data.get("target", "Belum ada target.")
    await update.message.reply_text(f"🎯 Target kamu:\n{target}")


# ================= TIMER =================

async def stop_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = context.user_data.get("timer_start")

    if not start:
        await update.message.reply_text("Timer belum dimulai.")
        return

    duration = int((time.time() - start) / 60)
    await update.message.reply_text(
        f"⏱ Kamu fokus selama {duration} menit.\nKerja bagus!"
    )


# ================= MAIN =================

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN belum diatur!")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("settarget", set_target))
    app.add_handler(CommandHandler("mytarget", my_target))
    app.add_handler(CommandHandler("stoptimer", stop_timer))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Bot berjalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
