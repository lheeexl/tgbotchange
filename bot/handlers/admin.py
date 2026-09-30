import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.config import Settings
from bot.keyboards.admin import admin_keyboard
from bot.keyboards.changes import list_keyboard
from bot.services import change_service
from bot.services.export_service import export_changes, export_history

router = Router()
logger = logging.getLogger(__name__)

async def is_admin(user_id: int, settings: Settings) -> bool:
    return user_id == settings.admin_id

@router.message(Command("admin"))
async def admin_command(message: Message, settings: Settings):
    if not await is_admin(message.from_user.id, settings):
        await message.answer("⛔ Доступ запрещён.")
        return
    logger.info("Admin panel opened by %s", message.from_user.id)
    await message.answer("⚙️ <b>Администрирование</b>", reply_markup=admin_keyboard())

@router.message(Command("all_changes"))
async def all_changes(message: Message, settings: Settings):
    if not await is_admin(message.from_user.id, settings):
        await message.answer("⛔ Доступ запрещён.")
        return
    changes = await change_service.list_changes()
    if not changes:
        await message.answer("Изменений пока нет.")
        return
    await message.answer("📋 <b>Все изменения</b>", reply_markup=list_keyboard(changes))

@router.message(Command("export"))
async def export_command(message: Message, settings: Settings):
    if not await is_admin(message.from_user.id, settings):
        await message.answer("⛔ Доступ запрещён.")
        return
    await _do_export(message)

@router.message(F.text == "⚙️ Администрирование")
async def admin_button(message: Message, settings: Settings):
    if not await is_admin(message.from_user.id, settings):
        await message.answer("⛔ Доступ запрещён.")
        return
    await message.answer("⚙️ <b>Администрирование</b>", reply_markup=admin_keyboard())

@router.callback_query(F.data == "admin:all")
async def admin_all(callback: CallbackQuery, settings: Settings):
    if not await is_admin(callback.from_user.id, settings):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    changes = await change_service.list_changes()
    await callback.message.edit_text(
        "📋 <b>Все изменения</b>",
        reply_markup=list_keyboard(changes),
    )
    await callback.answer()

@router.callback_query(F.data == "admin:search")
async def admin_search(callback: CallbackQuery, settings: Settings):
    if not await is_admin(callback.from_user.id, settings):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await callback.message.answer(
        "Для поиска администратора используйте:\n"
        "/admin_search_title слово"
    )
    await callback.answer()

@router.message(Command("admin_search_title"))
async def admin_search_title(message: Message, settings: Settings):
    if not await is_admin(message.from_user.id, settings):
        await message.answer("⛔ Доступ запрещён.")
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Использование: /admin_search_title фасад")
        return
    changes = await change_service.list_changes(title_query=parts[1])
    if not changes:
        await message.answer("Ничего не найдено.")
        return
    await message.answer(
        f"Найдено: <b>{len(changes)}</b>",
        reply_markup=list_keyboard(changes),
    )

@router.callback_query(F.data == "admin:stats")
async def admin_stats(callback: CallbackQuery, settings: Settings):
    if not await is_admin(callback.from_user.id, settings):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    data = await change_service.stats()
    await callback.message.edit_text(_stats_text(data))
    await callback.answer()

@router.callback_query(F.data == "admin:export")
async def admin_export(callback: CallbackQuery, settings: Settings):
    if not await is_admin(callback.from_user.id, settings):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    await _do_export(callback.message)
    await callback.answer("Экспорт готов")

async def _do_export(message: Message):
    try:
        changes_path = await export_changes()
        history_path = await export_history()
        await message.answer_document(
            FSInputFile(changes_path),
            caption="📤 Экспорт проектных изменений",
        )
        await message.answer_document(
            FSInputFile(history_path),
            caption="📜 Экспорт истории изменений",
        )
        logger.info("Export completed for chat %s", message.chat.id)
    except Exception:
        logger.exception("Export failed")
        await message.answer("❌ Ошибка при формировании экспорта.")

def _stats_text(data: dict) -> str:
    s = data["statuses"]
    p = data["priorities"]
    return (
        "📊 <b>Статистика</b>\n\n"
        f"Общее количество изменений: <b>{data['total']}</b>\n\n"
        f"🆕 Новые: {s['new']}\n"
        f"🔎 На рассмотрении: {s['review']}\n"
        f"✅ Согласованные: {s['approved']}\n"
        f"🔄 В работе: {s['in_progress']}\n"
        f"🏁 Выполненные: {s['completed']}\n"
        f"❌ Отклонённые: {s['rejected']}\n"
        f"🚫 Отменённые: {s['cancelled']}\n\n"
        f"🔴 Высокий приоритет: {p['high']}\n"
        f"🟡 Средний приоритет: {p['medium']}\n"
        f"🟢 Низкий приоритет: {p['low']}"
    )

@router.message(F.text == "📊 Статистика")
async def stats_button(message: Message):
    data = await change_service.stats()
    await message.answer(_stats_text(data))

@router.message(Command("stats"))
async def stats_command(message: Message):
    data = await change_service.stats()
    await message.answer(_stats_text(data))
