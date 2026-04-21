from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📅 Добавить день", callback_data="admin:add_day")
    )
    builder.row(
        InlineKeyboardButton(text="🕒 Добавить слоты на дату", callback_data="admin:add_slots")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Закрыть день", callback_data="admin:close_day")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Расписание на дату", callback_data="admin:view_day")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ В меню", callback_data="menu:main")
    )

    return builder.as_markup()


def admin_back_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад в админку", callback_data="admin:menu")
    )
    return builder.as_markup()