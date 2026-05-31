from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import os
import asyncio
import sys
from aiohttp import web
from groq import Groq

TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")

# Функция запроса к ИИ Groq
async def ask_ai(user_message: str) -> str:
    try:
        # Инициализируем клиент напрямую внутри функции, чтобы избежать бага с proxies
        client = Groq(api_key=GROQ_KEY)
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Ты — умный и дружелюбный ИИ-ассистент в чате. Отвечай кратко, емко и по делу."
                },
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            model="llama3-8b-8192",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Ошибка при запросе к ИИ: {e}", flush=True)
        return "Извини, не смог обработать запрос к ИИ."

# Функция ответа на сообщения в Telegram
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    user_text = update.message.text
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        ai_response = await ask_ai(user_text)
        await update.message.reply_text(ai_response)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}", flush=True)

# Веб-сервер для Render
async def handle(request):
    return web.Response(text="Бот активен!")

async def main():
    print("Проверка токенов...", flush=True)
    if not TOKEN or not GROQ_KEY:
        print("ОШИБКА: Токены не заданы в Environment Variables!", file=sys.stderr, flush=True)
        return

    # Запуск фонового веб-сервера
    app_web = web.Application()
    app_web.router.add_get('/', handle)
    runner = web.AppRunner(app_web)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Веб-сервер запущен на порту {port}", flush=True)

    # Настройка бота
    print("Инициализация Telegram-бота...", flush=True)
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("Бот успешно запущен!", flush=True)
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as main_error:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {main_error}", file=sys.stderr, flush=True)
