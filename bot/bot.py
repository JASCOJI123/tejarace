"""
TEJA RACE - Telegram Bot
Foydalanuvchini Mini App bilan tanishtiradi.

Ishga tushirish:
  BOT_TOKEN="..." WEBAPP_URL="https://sizning-domeningiz.com" python3 bot.py

BOT_TOKEN - @BotFather'dan olinadi
WEBAPP_URL - Mini App joylashtirilgan HTTPS manzil (masalan, Render'da hosting qilingandan keyin)
"""

import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://example.com")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🏁 TEJA RACE'ni ochish",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                )
            ]
        ]
    )
    await update.message.reply_text(
        "TEJA RACE'ga xush kelibsiz!\n\n"
        "Benzin sarfingizni kiriting, tejamkorlik reytingida raqobatlashing "
        "va hamkor AZS'lardan chegirmalar yutib oling.\n\n"
        "Boshlash uchun pastdagi tugmani bosing 👇",
        reply_markup=keyboard,
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Mini App'ni ochish\n"
        "/reyting - Joriy haftalik reytingni ko'rish"
    )


def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN environment variable o'rnatilmagan")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    # Python 3.14 fix: asyncio.get_event_loop() endi avtomatik loop yaratmaydi.
    # Shu joriy event loop'ni qo'lda o'rnatamiz.
    asyncio.set_event_loop(asyncio.new_event_loop())

    print("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
