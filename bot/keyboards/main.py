from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

def main_menu(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="➕ Зарегистрировать изменение")],
        [KeyboardButton(text="📋 Мои изменения"), KeyboardButton(text="🔎 Найти изменение")],
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="❓ Помощь")],
    ]
    if is_admin:
        rows.append([KeyboardButton(text="⚙️ Администрирование")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
