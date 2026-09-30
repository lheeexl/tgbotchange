from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

STATUS_LABELS = {
    "new": "🆕 Новое",
    "review": "🔎 На рассмотрении",
    "approved": "✅ Согласовано",
    "rejected": "❌ Отклонено",
    "in_progress": "🔄 В работе",
    "completed": "🏁 Выполнено",
    "cancelled": "🚫 Отменено",
}
PRIORITY_LABELS = {
    "high": "🔴 Высокий",
    "medium": "🟡 Средний",
    "low": "🟢 Низкий",
}

def priority_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 Высокий", callback_data="priority:high")],
        [InlineKeyboardButton(text="🟡 Средний", callback_data="priority:medium")],
        [InlineKeyboardButton(text="🟢 Низкий", callback_data="priority:low")],
    ])

def choice_keyboard(prefix: str, values: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"{prefix}:{value}")]
            for value, label in values
        ]
    )

def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="change:confirm"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="change:cancel"),
    ]])

def change_card_keyboard(change_id: int, can_edit: bool = True) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🔄 Изменить статус", callback_data=f"change:status:{change_id}")],
        [InlineKeyboardButton(text="📜 История", callback_data=f"change:history:{change_id}")],
    ]
    if can_edit:
        rows.append([InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"change:edit:{change_id}")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="change:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def status_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"status:{status}")]
            for status, label in STATUS_LABELS.items()
        ]
    )

def list_keyboard(changes: list, prefix: str = "open") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            text=f"#{c.id} — {c.title[:35]}",
            callback_data=f"{prefix}:{c.id}",
        )]
        for c in changes
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def search_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆔 По ID", callback_data="search:id")],
        [InlineKeyboardButton(text="🔤 По названию", callback_data="search:title")],
        [InlineKeyboardButton(text="📌 По статусу", callback_data="search:status")],
        [InlineKeyboardButton(text="🎯 По приоритету", callback_data="search:priority")],
        [InlineKeyboardButton(text="🏗 По области", callback_data="search:area")],
        [InlineKeyboardButton(text="🔥 Активные", callback_data="search:active")],
    ])
