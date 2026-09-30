from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import Settings
from bot.keyboards.main import main_menu

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message, settings: Settings) -> None:
    is_admin = message.from_user.id == settings.admin_id
    first_name = message.from_user.first_name or message.from_user.full_name or "пользователь"
    await message.answer(
        f"👋 <b>Привет, {first_name}!</b>\n\n"
        "Добро пожаловать в систему управления проектными изменениями.\n\n"
        "Здесь можно регистрировать изменения проекта, назначать ответственных, "
        "отслеживать статусы, просматривать историю и получать статистику.\n\n"
        "Выберите действие в меню ниже 👇",
        reply_markup=main_menu(is_admin),
    )
