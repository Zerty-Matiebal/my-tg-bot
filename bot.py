from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import os
import asyncio
from aiohttp import web

TOKEN = os.getenv("BOT_TOKEN")

# Функция ответа в Telegram
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Никита, иди нахуй")

# Крошечный веб-сервер для обмана Render
async def handle(request):
    return web.Response(text="Бот активен!")

async def start_web_server():
    app_web = web.Application()
    app_web.router.add_get('/', handle)
    runner = web.AppRunner(app_web)
    await runner.setup()
    # Render автоматически передает порт в переменную окружения PORT, по умолчанию берем 10000
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(# В кавычках простая строка, без LaTeX
"Веб-сервер успешно запущен на порту " + str(port))

async def main():
    # 1. Запускаем веб-сервер для Render
    await start_web_server()

    # 2. Настраиваем и запускаем Telegram-бота
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    
    async with app:
        await app.initialize()
        await app.start()
        print("Бот успешно запущен и слушает сообщения...")
        await app.updater.start_polling()
        
        # Держим всё запущенным
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
