import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from bot.config import get_settings
from bot.database.database import close_db, init_db
from bot.handlers.admin import router as admin_router
from bot.handlers.changes import router as changes_router
from bot.handlers.common import router as common_router
from bot.handlers.search import router as search_router
from bot.handlers.start import router as start_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

async def main() -> None:
    settings = get_settings()
    await init_db(settings.database_url)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await bot.set_my_commands([
        BotCommand(command="start", description="Открыть главное меню"),
        BotCommand(command="changes", description="Мои изменения"),
        BotCommand(command="stats", description="Статистика"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="cancel", description="Отменить текущую операцию"),
        BotCommand(command="admin", description="Администрирование"),
        BotCommand(command="all_changes", description="Все изменения (админ)"),
        BotCommand(command="export", description="Экспорт CSV (админ)"),
    ])
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(changes_router)
    dp.include_router(search_router)
    dp.include_router(admin_router)
    dp.include_router(common_router)

    logging.info("Bot started")
    try:
        await dp.start_polling(bot, settings=settings)
    finally:
        await close_db()
        await bot.session.close()
        logging.info("Bot stopped")
