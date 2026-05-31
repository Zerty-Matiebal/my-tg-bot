from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import os
import asyncio
import sys
from aiohttp import web, ClientSession

TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")

# Прямой запрос к ИИ
async def ask_ai(user_message: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": "Ты — умный, вежливый и краткий ИИ-ассистент. Отвечаешь от имени владельца аккаунта. Пиши емко и по делу."
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    }
    try:
        async with ClientSession(trust_env=False) as session:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    return "Извини, я временно завис."
    except Exception as e:
        print(f"Ошибка ИИ: {e}", flush=True)
        return "Извини, не смог связаться с ИИ."

# Обработчик для ОБЫЧНЫХ сообщений (в чате с ботом)
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    ai_response = await ask_ai(user_text)
    await update.message.reply_text(ai_response)

# ОБРАБОТЧИК ДЛЯ TELEGRAM BUSINESS (Личные переписки)
async def reply_business(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.business_message or not update.business_message.text:
        return
    
    # Проверяем, что сообщение пришло ОТ ДРУГОГО человека, а не от тебя самого
    if update.business_message.from_user.id == update.effective_user.id:
        return

    user_text = update.business_message.text
    
    # Отправляем ИИ-ответ прямо в личную переписку
    ai_response = await ask_ai(user_text)
    await update.business_message.reply_text(ai_response)

# Веб-сервер для заглушки Render
async def handle(request):
    return web.Response(text="Бот активен!")

async def main():
    if not TOKEN or not GROQ_KEY:
        print("КРИТИЧЕСКАЯ ОШИБКА: Токены не заполнены!", file=sys.stderr, flush=True)
        return

    app_web = web.Application()
    app_web.router.add_get('/', handle)
    runner = web.AppRunner(app_web)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, '0.0.0.0', port).start()

    # Старт бота
    application = Application.builder().token(TOKEN).build()
    
    # Слушаем обычные сообщения
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    
    # Слушаем бизнес-сообщения в личке!
    application.add_handler(MessageHandler(filters.UpdateType.BUSINESS_MESSAGES & filters.TEXT, reply_business))
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("Бот успешно запущен с поддержкой Telegram Business!", flush=True)
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as main_error:
        print(f"Ошибка цикла: {main_error}", file=sys.stderr, flush=True)
