from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import os
import asyncio

TOKEN = os.getenv("BOT_TOKEN")

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я работаю.")

async def main():
    # Собираем приложение
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    
    # Правильный запуск бота для свежих версий Python
    async with app:
        await app.initialize()
        await app.start()
        print("Бот успешно запущен и слушает сообщения...")
        await app.updater.start_polling()
        # Держим бота запущенным
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    # Запускаем главную асинхронную функцию
    asyncio.run(main())
