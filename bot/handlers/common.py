import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config import Settings
from bot.keyboards.main import main_menu

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Текущая операция отменена.")

@router.message(Command("help"))
async def help_handler(message: Message, settings: Settings) -> None:
    text = (
        "<b>📚 Помощь</b>\n\n"
        "Бот регистрирует проектные изменения и хранит историю их статусов.\n\n"
        "Основные команды:\n"
        "/start — главное меню\n"
        "/changes — мои изменения\n"
        "/stats — статистика\n"
        "/cancel — отменить текущий ввод"
    )
    if message.from_user.id == settings.admin_id:
        text += "\n/admin — административный режим\n/all_changes — все изменения\n/export — CSV-экспорт"
    await message.answer(text, reply_markup=main_menu(message.from_user.id == settings.admin_id))
