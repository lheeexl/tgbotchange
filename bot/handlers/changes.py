import logging
import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.config import Settings
from bot.keyboards.changes import (
    PRIORITY_LABELS,
    STATUS_LABELS,
    change_card_keyboard,
    choice_keyboard,
    confirm_keyboard,
    list_keyboard,
    priority_keyboard,
    status_keyboard,
)
from bot.keyboards.main import main_menu
from bot.services import change_service
from bot.services.history_service import format_dt, format_history
from bot.states.change import ChangeForm, EditChangeForm, StatusForm

router = Router()
logger = logging.getLogger(__name__)

AREAS = [
    ("documentation", "📄 Проектная документация"),
    ("structures", "🏗 Конструктивные решения"),
    ("architecture", "🏛 Архитектура"),
    ("engineering", "⚙️ Инженерные системы"),
    ("estimate", "💰 Смета"),
    ("schedule", "📅 График"),
    ("construction", "🔨 Строительные работы"),
    ("other", "📌 Другое"),
]
SCHEDULE_IMPACTS = [
    ("none", "Без влияния"),
    ("minor", "Незначительное"),
    ("medium", "Среднее"),
    ("major", "Значительное"),
]
COST_IMPACTS = [
    ("none", "Без влияния"),
    ("decrease", "Уменьшение стоимости"),
    ("unchanged", "Без изменений"),
    ("increase", "Увеличение стоимости"),
]
MAX_TEXT = 4000

def _label(values, value):
    return dict(values).get(value, value)

def _responsible_id(text: str) -> int | None:
    if re.fullmatch(r"\d{5,20}", text.strip()):
        return int(text.strip())
    return None

def _card(change) -> str:
    return (
        "━━━━━━━━━━━━━━━━\n"
        f"📋 <b>ИЗМЕНЕНИЕ #{change.id}</b>\n\n"
        f"<b>Название:</b> {change.title}\n"
        f"<b>Описание:</b> {change.description}\n"
        f"<b>Причина:</b> {change.reason}\n"
        f"<b>Область:</b> {_label(AREAS, change.affected_area)}\n"
        f"<b>Приоритет:</b> {PRIORITY_LABELS.get(change.priority, change.priority)}\n"
        f"<b>Влияние на сроки:</b> {_label(SCHEDULE_IMPACTS, change.schedule_impact)}\n"
        f"<b>Влияние на стоимость:</b> {_label(COST_IMPACTS, change.cost_impact)}\n"
        f"<b>Ответственный:</b> {change.responsible_person}\n"
        f"<b>Автор:</b> {change.creator_full_name or change.creator_username or change.created_by}\n"
        f"<b>Дата:</b> {format_dt(change.created_at)}\n"
        f"<b>Изменено:</b> {format_dt(change.updated_at)}\n"
        f"<b>Статус:</b> {STATUS_LABELS.get(change.status, change.status)}\n"
        f"<b>Комментарий:</b> {change.comment or '—'}\n"
        "━━━━━━━━━━━━━━━━"
    )

async def _show_change(target, change, can_edit=True):
    text = _card(change)
    if isinstance(target, Message):
        await target.answer(text, reply_markup=change_card_keyboard(change.id, can_edit))
    else:
        await target.message.edit_text(text, reply_markup=change_card_keyboard(change.id, can_edit))
        await target.answer()

@router.message(F.text == "➕ Зарегистрировать изменение")
async def start_change(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(ChangeForm.title)
    await message.answer("Введите название изменения.")

@router.message(ChangeForm.title)
async def form_title(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if not text or len(text) > 200:
        await message.answer("Название не должно быть пустым и должно содержать не более 200 символов.")
        return
    await state.update_data(title=text)
    await state.set_state(ChangeForm.description)
    await message.answer("Подробно опишите, что необходимо изменить.")

@router.message(ChangeForm.description)
async def form_description(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if not text or len(text) > MAX_TEXT:
        await message.answer(f"Описание должно быть непустым и не длиннее {MAX_TEXT} символов.")
        return
    await state.update_data(description=text)
    await state.set_state(ChangeForm.reason)
    await message.answer("Укажите причину изменения.")

@router.message(ChangeForm.reason)
async def form_reason(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if not text or len(text) > MAX_TEXT:
        await message.answer(f"Причина должна быть непустой и не длиннее {MAX_TEXT} символов.")
        return
    await state.update_data(reason=text)
    await state.set_state(ChangeForm.affected_area)
    await message.answer(
        "Какой объект/раздел проекта затрагивает изменение?",
        reply_markup=choice_keyboard("area", AREAS),
    )

@router.callback_query(ChangeForm.affected_area, F.data.startswith("area:"))
async def form_area(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":", 1)[1]
    if value not in dict(AREAS):
        await callback.answer("Некорректное значение", show_alert=True)
        return
    await state.update_data(affected_area=value)
    await state.set_state(ChangeForm.priority)
    await callback.message.edit_text("Выберите приоритет изменения.", reply_markup=priority_keyboard())
    await callback.answer()

@router.message(ChangeForm.affected_area)
async def area_wrong(message: Message):
    await message.answer("Выберите область кнопкой ниже.", reply_markup=choice_keyboard("area", AREAS))

@router.callback_query(ChangeForm.priority, F.data.startswith("priority:"))
async def form_priority(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":", 1)[1]
    if value not in PRIORITY_LABELS:
        await callback.answer("Некорректное значение", show_alert=True)
        return
    await state.update_data(priority=value)
    await state.set_state(ChangeForm.schedule_impact)
    await callback.message.edit_text(
        "Укажите предполагаемое влияние изменения на сроки проекта.",
        reply_markup=choice_keyboard("schedule", SCHEDULE_IMPACTS),
    )
    await callback.answer()

@router.callback_query(ChangeForm.schedule_impact, F.data.startswith("schedule:"))
async def form_schedule(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":", 1)[1]
    if value not in dict(SCHEDULE_IMPACTS):
        await callback.answer("Некорректное значение", show_alert=True)
        return
    await state.update_data(schedule_impact=value)
    await state.set_state(ChangeForm.cost_impact)
    await callback.message.edit_text(
        "Укажите предполагаемое влияние на стоимость проекта.",
        reply_markup=choice_keyboard("cost", COST_IMPACTS),
    )
    await callback.answer()

@router.callback_query(ChangeForm.cost_impact, F.data.startswith("cost:"))
async def form_cost(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":", 1)[1]
    if value not in dict(COST_IMPACTS):
        await callback.answer("Некорректное значение", show_alert=True)
        return
    await state.update_data(cost_impact=value)
    await state.set_state(ChangeForm.responsible_person)
    await callback.message.edit_text(
        "Укажите ответственного за обработку изменения.\n"
        "Можно указать ФИО или Telegram ID числом.",
    )
    await callback.answer()

@router.message(ChangeForm.responsible_person)
async def form_responsible(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if not text or len(text) > 200:
        await message.answer("Ответственный должен быть указан и не длиннее 200 символов.")
        return
    await state.update_data(
        responsible_person=text,
        responsible_telegram_id=_responsible_id(text),
    )
    await state.set_state(ChangeForm.comment)
    await message.answer("Добавьте дополнительный комментарий или примечание. Если не нужен — напишите «нет».")

@router.message(ChangeForm.comment)
async def form_comment(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if len(text) > MAX_TEXT:
        await message.answer(f"Комментарий не длиннее {MAX_TEXT} символов.")
        return
    if text.lower() == "нет":
        text = ""
    await state.update_data(comment=text)
    await state.set_state(ChangeForm.confirmation)
    data = await state.get_data()
    preview = (
        "━━━━━━━━━━━━━━━━\n"
        "📋 <b>НОВОЕ ИЗМЕНЕНИЕ</b>\n\n"
        f"<b>Название:</b> {data['title']}\n"
        f"<b>Описание:</b> {data['description']}\n"
        f"<b>Причина:</b> {data['reason']}\n"
        f"<b>Область:</b> {_label(AREAS, data['affected_area'])}\n"
        f"<b>Приоритет:</b> {PRIORITY_LABELS[data['priority']]}\n"
        f"<b>Влияние на сроки:</b> {_label(SCHEDULE_IMPACTS, data['schedule_impact'])}\n"
        f"<b>Влияние на стоимость:</b> {_label(COST_IMPACTS, data['cost_impact'])}\n"
        f"<b>Ответственный:</b> {data['responsible_person']}\n"
        f"<b>Комментарий:</b> {data['comment'] or '—'}\n"
        "<b>Статус:</b> 🆕 Новое\n"
        f"<b>Автор:</b> {message.from_user.full_name}\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "Подтвердить регистрацию изменения?"
    )
    await message.answer(preview, reply_markup=confirm_keyboard())

@router.callback_query(ChangeForm.confirmation, F.data == "change:cancel")
async def cancel_change(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Регистрация изменения отменена.")
    await callback.answer()

@router.callback_query(ChangeForm.confirmation, F.data == "change:confirm")
async def confirm_change(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    change = await change_service.create_change(
        data=data,
        user_id=callback.from_user.id,
        username=callback.from_user.username or "",
        full_name=callback.from_user.full_name,
    )
    await state.clear()
    logger.info("Change #%s registered by %s", change.id, callback.from_user.id)
    await callback.message.edit_text(
        f"✅ Изменение <b>#{change.id}</b> зарегистрировано.\n\n{_card(change)}"
    )
    await callback.answer("Сохранено")

@router.message(Command("changes"))
async def my_changes_command(message: Message):
    changes = await change_service.list_changes(created_by=message.from_user.id)
    if not changes:
        await message.answer("📋 У вас пока нет зарегистрированных изменений.")
        return
    await message.answer("📋 <b>Мои изменения</b>:", reply_markup=list_keyboard(changes))

@router.message(F.text == "📋 Мои изменения")
async def my_changes_button(message: Message):
    changes = await change_service.list_changes(created_by=message.from_user.id)
    if not changes:
        await message.answer("У вас пока нет зарегистрированных изменений.")
        return
    await message.answer("📋 <b>Мои изменения</b>:", reply_markup=list_keyboard(changes))

@router.callback_query(F.data.startswith("open:"))
async def open_change(callback: CallbackQuery, settings: Settings):
    change_id = int(callback.data.split(":")[1])
    change = await change_service.get_change(change_id)
    if not change:
        await callback.answer("Изменение не найдено", show_alert=True)
        return
    can_edit = change.created_by == callback.from_user.id or callback.from_user.id == settings.admin_id
    if change.created_by != callback.from_user.id and callback.from_user.id != settings.admin_id:
        await callback.answer("Нет доступа к этому изменению.", show_alert=True)
        return
    await _show_change(callback, change, can_edit)

@router.callback_query(F.data == "change:back")
async def back_change(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()

@router.callback_query(F.data.startswith("change:history:"))
async def show_history(callback: CallbackQuery, settings: Settings):
    change_id = int(callback.data.split(":")[2])
    change = await change_service.get_change(change_id)
    if not change or (
        change.created_by != callback.from_user.id
        and callback.from_user.id != settings.admin_id
    ):
        await callback.answer("Нет доступа.", show_alert=True)
        return
    history = await change_service.history(change_id)
    await callback.message.edit_text(
        f"📜 <b>История изменения #{change_id}</b>\n\n{format_history(history)}",
        reply_markup=change_card_keyboard(change_id),
    )
    await callback.answer()

@router.callback_query(F.data.startswith("change:status:"))
async def start_status(callback: CallbackQuery, state: FSMContext, settings: Settings):
    change_id = int(callback.data.split(":")[2])
    change = await change_service.get_change(change_id)
    if not change or (change.created_by != callback.from_user.id and callback.from_user.id != settings.admin_id):
        await callback.answer("Нет доступа.", show_alert=True)
        return
    await state.clear()
    await state.update_data(change_id=change_id)
    await state.set_state(StatusForm.status)
    await callback.message.edit_text("Выберите новый статус.", reply_markup=status_keyboard())
    await callback.answer()

@router.callback_query(StatusForm.status, F.data.startswith("status:"))
async def select_status(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":", 1)[1]
    if value not in STATUS_LABELS:
        await callback.answer("Некорректный статус", show_alert=True)
        return
    data = await state.get_data()
    change = await change_service.get_change(data["change_id"])
    if not change:
        await state.clear()
        await callback.answer("Изменение не найдено", show_alert=True)
        return
    if value == change.status:
        await callback.answer("Это уже текущий статус", show_alert=True)
        return
    await state.update_data(new_status=value)
    await state.set_state(StatusForm.comment)
    await callback.message.edit_text("Укажите причину изменения статуса или дополнительный комментарий.")
    await callback.answer()

@router.message(StatusForm.comment)
async def finish_status(message: Message, state: FSMContext, bot):
    comment = message.text.strip() if message.text else ""
    if not comment:
        await message.answer("Комментарий не должен быть пустым.")
        return
    if len(comment) > MAX_TEXT:
        await message.answer(f"Комментарий не длиннее {MAX_TEXT} символов.")
        return

    data = await state.get_data()
    change, history = await change_service.set_status(
        data["change_id"],
        data["new_status"],
        message.from_user.id,
        message.from_user.full_name,
        comment,
    )
    await state.clear()
    if not change:
        await message.answer("Изменение не найдено.")
        return

    old_label = STATUS_LABELS.get(history.old_status, history.old_status)
    new_label = STATUS_LABELS.get(history.new_status, history.new_status)
    notification = (
        f"🔔 <b>Изменение #{change.id}</b>\n\n"
        f"Статус изменён:\n{old_label} → {new_label}\n\n"
        f"<b>Изменение:</b> {change.title}\n"
        f"<b>Комментарий:</b> {comment}"
    )
    await message.answer(notification)

    recipient_ids = {change.created_by}
    if change.responsible_telegram_id:
        recipient_ids.add(change.responsible_telegram_id)
    # Administrator notification is sent together with author/responsible notifications.
    from bot.config import get_settings
    admin_id = get_settings().admin_id
    recipient_ids.add(admin_id)
    for recipient in recipient_ids:
        if recipient == message.from_user.id:
            continue
        try:
            await bot.send_message(recipient, notification)
        except Exception as exc:
            logger.warning("Notification to %s failed: %s", recipient, exc)

@router.callback_query(F.data.startswith("change:edit:"))
async def start_edit(callback: CallbackQuery, state: FSMContext, settings: Settings):
    change_id = int(callback.data.split(":")[2])
    change = await change_service.get_change(change_id)
    if not change or (change.created_by != callback.from_user.id and callback.from_user.id != settings.admin_id):
        await callback.answer("Нет доступа.", show_alert=True)
        return
    await state.clear()
    await state.update_data(change_id=change_id)
    await state.set_state(EditChangeForm.title)
    await callback.message.edit_text(
        f"✏️ Редактирование #{change_id}\n\n"
        f"Текущее название: <b>{change.title}</b>\n"
        "Введите новое название или отправьте `-`, чтобы оставить без изменений."
    )
    await callback.answer()

async def _edit_text_field(message: Message, state: FSMContext, state_next, key: str, limit: int, prompt: str):
    text = message.text.strip() if message.text else ""
    await state.update_data(**{key: None if text == "-" else text})
    await state.set_state(state_next)
    await message.answer(prompt)

@router.message(EditChangeForm.title)
async def edit_title(message: Message, state: FSMContext):
    await _edit_text_field(message, state, EditChangeForm.description, "title", 200,
                           "Введите новое описание или `-`.")

@router.message(EditChangeForm.description)
async def edit_description(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if text != "-" and (not text or len(text) > MAX_TEXT):
        await message.answer(f"Описание должно быть непустым и не длиннее {MAX_TEXT}.")
        return
    await state.update_data(description=None if text == "-" else text)
    await state.set_state(EditChangeForm.reason)
    await message.answer("Введите новую причину или `-`.")

@router.message(EditChangeForm.reason)
async def edit_reason(message: Message, state: FSMContext):
    text = message.text.strip() if message.text else ""
    if text != "-" and (not text or len(text) > MAX_TEXT):
        await message.answer(f"Причина должна быть непустой и не длиннее {MAX_TEXT}.")
        return
    await state.update_data(reason=None if text == "-" else text)
    await state.set_state(EditChangeForm.affected_area)
    await message.answer("Выберите новую область или `-`.", reply_markup=choice_keyboard("editarea", AREAS))

@router.callback_query(EditChangeForm.affected_area, F.data.startswith("editarea:"))
async def edit_area(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":", 1)[1]
    await state.update_data(affected_area=value)
    await state.set_state(EditChangeForm.priority)
    await callback.message.edit_text("Выберите новый приоритет.", reply_markup=priority_keyboard())
    await callback.answer()

@router.message(EditChangeForm.affected_area)
async def edit_area_text(message: Message, state: FSMContext):
    if message.text.strip() == "-":
        await state.update_data(affected_area=None)
        await state.set_state(EditChangeForm.priority)
        await message.answer("Выберите новый приоритет.", reply_markup=priority_keyboard())
    else:
        await message.answer("Выберите область кнопкой или отправьте `-`.")

@router.callback_query(EditChangeForm.priority, F.data.startswith("priority:"))
async def edit_priority(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":", 1)[1]
    await state.update_data(priority=value)
    await state.set_state(EditChangeForm.schedule_impact)
    await callback.message.edit_text("Выберите влияние на сроки.",
                                     reply_markup=choice_keyboard("editschedule", SCHEDULE_IMPACTS))
    await callback.answer()

@router.message(EditChangeForm.priority)
async def edit_priority_text(message: Message):
    await message.answer("Выберите приоритет кнопкой.")

@router.callback_query(EditChangeForm.schedule_impact, F.data.startswith("editschedule:"))
async def edit_schedule(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":", 1)[1]
    await state.update_data(schedule_impact=value)
    await state.set_state(EditChangeForm.cost_impact)
    await callback.message.edit_text("Выберите влияние на стоимость.",
                                     reply_markup=choice_keyboard("editcost", COST_IMPACTS))
    await callback.answer()

@router.message(EditChangeForm.schedule_impact)
async def edit_schedule_text(message: Message):
    await message.answer("Выберите влияние на сроки кнопкой.")

@router.callback_query(EditChangeForm.cost_impact, F.data.startswith("editcost:"))
async def edit_cost(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":", 1)[1]
    await state.update_data(cost_impact=value)
    await state.set_state(EditChangeForm.responsible_person)
    await callback.message.edit_text("Введите нового ответственного или `-`.")
    await callback.answer()

@router.message(EditChangeForm.cost_impact)
async def edit_cost_text(message: Message):
    await message.answer("Выберите влияние на стоимость кнопкой.")

@router.message(EditChangeForm.responsible_person)
async def edit_responsible(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(
        responsible_person=None if text == "-" else text,
        responsible_telegram_id=None if text == "-" else _responsible_id(text),
    )
    await state.set_state(EditChangeForm.comment)
    await message.answer("Введите новый комментарий или `-`.")

@router.message(EditChangeForm.comment)
async def finish_edit(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    fields = {}
    for key in (
        "title", "description", "reason", "affected_area", "priority",
        "schedule_impact", "cost_impact", "responsible_person", "responsible_telegram_id",
    ):
        if data.get(key) is not None:
            fields[key] = data[key]
    if text != "-":
        if len(text) > MAX_TEXT:
            await message.answer(f"Комментарий не длиннее {MAX_TEXT}.")
            return
        fields["comment"] = text

    if "title" in fields and (not fields["title"] or len(fields["title"]) > 200):
        await message.answer("Некорректное название.")
        return
    change = await change_service.edit_change(data["change_id"], fields)
    await state.clear()
    if change:
        await message.answer("✅ Изменение обновлено.")
        await _show_change(message, change)
    else:
        await message.answer("Изменение не найдено.")
