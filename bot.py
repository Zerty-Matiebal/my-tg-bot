from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import os
import asyncio
from aiohttp import web

TOKEN = os.getenv("BOT_TOKEN")

# Текст твоего автоответчика
AUTO_REPLY_TEXT = "Я супер умный автоответчик Nikita_Slave♂️, мой великодушный хозяин не в сети, пожалуйста подождите"

# Время ожидания твоего ответа (в секундах). 180 секунд = 3 минуты
WAIT_TIME = 60

# Словарь для отслеживания активных таймеров ожидания по каждому чату
active_tasks = {}

# Обработчик для личных бизнес-переписок
async def reply_business(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.business_message:
        return
    
    chat_id = update.effective_chat.id
    user_id = update.business_message.from_user.id
    my_id = update.effective_user.id  # Твой собственный ID

    # ЕСЛИ НАПИСАЛ ТЫ САМ: значит ты в сети и ответил человеку!
    if user_id == my_id:
        if chat_id in active_tasks:
            # Отменяем автоответ бота, так как ты уже общаешься в этом чате
            active_tasks[chat_id].cancel()
            del active_tasks[chat_id]
            print(f"Ты ответил в чате {chat_id}. Автоответ отменен.", flush=True)
        return

    # ЕСЛИ НАПИСАЛ КТО-ТО ДРУГОЙ (Входящее сообщение):
    # Если для этого чата уже тикает таймер, сбрасываем старый и ставим новый (чтобы отсчет шел от последнего сообщения)
    if chat_id in active_tasks:
        active_tasks[chat_id].cancel()

    # Запускаем фоновую задачу ожидания
    task = asyncio.create_task(wait_and_reply(update, chat_id))
    active_tasks[chat_id] = task

# Функция, которая ждет и проверяет, нужно ли отвечать
async def wait_and_reply(update: Update, chat_id: int):
    try:
        # Ждем 3 минуты
        await asyncio.sleep(WAIT_TIME)
        
        # Если время прошло и задачу никто не отменил — значит ты не ответил. Отправляем текст!
        await update.business_message.reply_text(AUTO_REPLY_TEXT)
        print(f"Отправлен автоответ в чат {chat_id}, так как владелец не в сети.", flush=True)
        
        # Удаляем задачу из активных, так как она выполнена
        if chat_id in active_tasks:
            del active_tasks[chat_id]
            
    except asyncio.CancelledError:
        # Сюда код попадает, если задача была успешно отменена твоим ответом
        pass
    except Exception as e:
        print(f"Ошибка в таймере автоответа: {e}", flush=True)

# Заглушка веб-сервера для Render
async def handle(request):
    return web.Response(text="Умный автоответчик активен!")

async def main():
    if not TOKEN:
        print("ОШИБКА: BOT_TOKEN не задан!", flush=True)
        return

    app_web = web.Application()
    app_web.router.add_get('/', handle)
    runner = web.AppRunner(app_web)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, '0.0.0.0', port).start()

    application = Application.builder().token(TOKEN).build()
    
    # Отслеживаем все текстовые сообщения в бизнес-чатах (и твои, и чужие)
    application.add_handler(MessageHandler(filters.UpdateType.BUSINESS_MESSAGES & filters.TEXT, reply_business))
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("Умный автоответчик успешно запущен!", flush=True)
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
