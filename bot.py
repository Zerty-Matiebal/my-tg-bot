from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import os
import asyncio
import sys
from aiohttp import web, ClientSession

TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")

# Прямой запрос к ИИ через обычный веб-запрос (без библиотеки groq)
async def ask_ai(user_message: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        # Заменили старую отключенную модель на новую и рабочую
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": "Ты — умный и дружелюбный ИИ-ассистент в чате. Отвечай кратко, емко и по делу."
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    }
    
    try:
        # trust_env=False намертво отключает любые системные прокси Render для этого запроса
        async with ClientSession(trust_env=False) as session:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    print(f"Ошибка сервера Groq (Код {response.status}): {error_text}", flush=True)
                    return "Извини, ИИ временно недоступен."
    except Exception as e:
        print(f"Ошибка сети при запросе к ИИ: {e}", flush=True)
        return "Извини, не смог связаться с мыслительным центром."

# Функция ответа в Telegram
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    user_text = update.message.text
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        ai_response = await ask_ai(user_text)
        await update.message.reply_text(ai_response)
    except Exception as e:
        print(f"Ошибка отправки в TG: {e}", flush=True)

# Веб-сервер для заглушки Render
async def handle(request):
    return web.Response(text="Бот активен!")

async def main():
    print("Проверка ключей...", flush=True)
    if not TOKEN or not GROQ_KEY:
        print("КРИТИЧЕСКАЯ ОШИБКА: Токены не заполнены!", file=sys.stderr, flush=True)
        return

    # Поднимаем веб-сервер
    app_web = web.Application()
    app_web.router.add_get('/', handle)
    runner = web.AppRunner(app_web)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Веб-сервер запущен на порту {port}", flush=True)

    # Запуск Telegram бота
    print("Старт Telegram-бота...", flush=True)
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("БОТ УСПЕШНО ЗАПУЩЕН И ГОТОВ К РАБОТЕ!", flush=True)
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as main_error:
        print(f"Критическая ошибка главного цикла: {main_error}", file=sys.stderr, flush=True)
