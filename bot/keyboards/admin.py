from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Все изменения", callback_data="admin:all")],
        [InlineKeyboardButton(text="🔎 Поиск", callback_data="admin:search")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats")],
        [InlineKeyboardButton(text="📤 Экспорт", callback_data="admin:export")],
    ])
