import asyncio
from aiogram import Bot, Dispatcher
import logging
from run import register_handlers
from dotenv import load_dotenv
import os
from aiohttp import web

# Загрузка переменных среды
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(TOKEN)
logger = logging.getLogger(__name__)

# Веб-сервер для пинга
async def handle_ping(request):
    return web.Response(text="pong")

async def start_web_server():
    """Запуск веб-сервера"""
    app = web.Application()
    app.router.add_get('/', handle_ping)
    app.router.add_get('/health', lambda r: web.json_response({"status": "ok"}))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("Web server started on port 8080")
    return runner

async def main():
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    logger.info("Starting bot")

    # Запускаем веб-сервер
    web_runner = await start_web_server()

    # Инициализация диспетчера и обработчиков
    dp = Dispatcher()
    register_handlers(dp)
    
    logger.info('Bot is started')
    
    try:
        await dp.start_polling(bot)
    finally:
        # Корректное завершение
        await web_runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())
