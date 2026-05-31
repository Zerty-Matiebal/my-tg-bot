from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import os
import asyncio
from aiohttp import web
from groq import Groq

TOKEN = os.getenv("BOT_TOKEN")
# Подключаем ИИ-клиент
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Функция запроса к искусственному интеллекту
async def ask_ai(user_message: str) -> str:
    try:
        # Используем быструю и умную модель Llama 3
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Ты — умный, веселый и дружелюбный ИИ-ассистент в чате. Отвечай кратко, емко и по делу."
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
        print(f"Ошибка ИИ: {e}")
        return "Извини, у меня перегружен мыслительный процессор. Попробуй позже!"

# Функция ответа в Telegram
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # Отправляем эффект "бот печатает..."
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Получаем ответ от ИИ
    ai_response = await ask_ai(user_text)
    
    # Отвечаем пользователю
    await update.message.reply_text(ai_response)

# Крошечный веб-сервер для обмана Render
async def handle(request):
    return web.Response(text="Бот активен!")

async def start_web_server():
    app_web = web.Application()
    app_web.router.add_get('/', handle)
    runner = web.AppRunner(app_web)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print("Веб-сервер запущен.")

async def main():
    await start_web_server()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    
    async with app:
        await app.initialize()
        await app.start()
        print("Бот с ИИ успешно запущен!")
        await app.updater.start_polling()
        
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
