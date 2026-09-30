from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot.database.models import ProjectChange
from bot.keyboards.changes import (
    PRIORITY_LABELS,
    STATUS_LABELS,
    list_keyboard,
    search_menu_keyboard,
    choice_keyboard,
)
from bot.services import change_service
from bot.states.change import SearchForm

router = Router()

STATUS_CHOICES = [(k, v) for k, v in STATUS_LABELS.items()]
PRIORITY_CHOICES = [(k, v) for k, v in PRIORITY_LABELS.items()]
AREA_CHOICES = [
    ("documentation", "📄 Проектная документация"),
    ("structures", "🏗 Конструктивные решения"),
    ("architecture", "🏛 Архитектура"),
    ("engineering", "⚙️ Инженерные системы"),
    ("estimate", "💰 Смета"),
    ("schedule", "📅 График"),
    ("construction", "🔨 Строительные работы"),
    ("other", "📌 Другое"),
]

@router.message(F.text == "🔎 Найти изменение")
async def search_start(message: Message):
    await message.answer("Выберите способ поиска:", reply_markup=search_menu_keyboard())

@router.callback_query(F.data == "search:id")
async def search_id(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(SearchForm.id)
    await callback.message.edit_text("🆔 Введите ID изменения числом.\n\nНапример: 15")
    await callback.answer()

@router.message(SearchForm.id)
async def search_id_value(message: Message, state: FSMContext):
    value = (message.text or "").strip()
    if not value.isdigit():
        await message.answer("❗ ID должен содержать только цифры. Например: 15")
        return
    change = await change_service.get_change(int(value))
    await state.clear()
    if not change:
        await message.answer("❌ Изменение с таким ID не найдено.")
        return
    if change.created_by != message.from_user.id:
        await message.answer("⛔ Нет доступа к этому изменению.")
        return
    await message.answer(
        f"Найдено изменение <b>#{change.id}</b> — {change.title}",
        reply_markup=list_keyboard([change]),
    )

@router.message(Command("search_id"))
async def search_id_command(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /search_id 15")
        return
    change = await change_service.get_change(int(parts[1]))
    if not change:
        await message.answer("Изменение не найдено.")
        return
    if change.created_by != message.from_user.id:
        await message.answer("Нет доступа к этому изменению.")
        return
    await message.answer(
        f"Найдено: <b>#{change.id}</b> — {change.title}",
        reply_markup=list_keyboard([change]),
    )

@router.callback_query(F.data == "search:title")
async def search_title(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(SearchForm.title)
    await callback.message.edit_text("🔤 Введите слово или фразу из названия изменения.")
    await callback.answer()

@router.message(SearchForm.title)
async def search_title_value(message: Message, state: FSMContext):
    query = (message.text or "").strip()
    if not query:
        await message.answer("❗ Введите текст для поиска.")
        return
    changes = await change_service.list_changes(
        created_by=message.from_user.id,
        title_query=query,
    )
    await state.clear()
    await _send_results(message, changes)

@router.message(Command("search_title"))
async def search_title_command(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Использование: /search_title фасад")
        return
    changes = await change_service.list_changes(
        created_by=message.from_user.id,
        title_query=parts[1],
    )
    await _send_results(message, changes)

@router.callback_query(F.data == "search:status")
async def search_status(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выберите статус:",
        reply_markup=choice_keyboard("filterstatus", STATUS_CHOICES),
    )
    await callback.answer()

@router.callback_query(F.data.startswith("filterstatus:"))
async def filter_status(callback: CallbackQuery):
    status = callback.data.split(":", 1)[1]
    changes = await change_service.list_changes(
        created_by=callback.from_user.id,
        status=status,
    )
    await _send_results(callback.message, changes)
    await callback.answer()

@router.callback_query(F.data == "search:priority")
async def search_priority(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выберите приоритет:",
        reply_markup=choice_keyboard("filterpriority", PRIORITY_CHOICES),
    )
    await callback.answer()

@router.callback_query(F.data.startswith("filterpriority:"))
async def filter_priority(callback: CallbackQuery):
    priority = callback.data.split(":", 1)[1]
    changes = await change_service.list_changes(
        created_by=callback.from_user.id,
        priority=priority,
    )
    await _send_results(callback.message, changes)
    await callback.answer()

@router.callback_query(F.data == "search:area")
async def search_area(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выберите область:",
        reply_markup=choice_keyboard("filterarea", AREA_CHOICES),
    )
    await callback.answer()

@router.callback_query(F.data.startswith("filterarea:"))
async def filter_area(callback: CallbackQuery):
    area = callback.data.split(":", 1)[1]
    changes = await change_service.list_changes(
        created_by=callback.from_user.id,
        affected_area=area,
    )
    await _send_results(callback.message, changes)
    await callback.answer()

@router.callback_query(F.data == "search:active")
async def active_changes(callback: CallbackQuery):
    active = ["new", "review", "approved", "in_progress"]
    changes = []
    for status in active:
        changes.extend(await change_service.list_changes(
            created_by=callback.from_user.id,
            status=status,
        ))
    changes.sort(key=lambda c: c.created_at, reverse=True)
    await _send_results(callback.message, changes)
    await callback.answer()

async def _send_results(message: Message, changes: list[ProjectChange]):
    if not changes:
        await message.answer("По заданному фильтру ничего не найдено.")
        return
    await message.answer(
        f"Найдено изменений: <b>{len(changes)}</b>",
        reply_markup=list_keyboard(changes),
    )
