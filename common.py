from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb(is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📅 Записаться", callback_data="menu:book")
    )
    builder.row(
        InlineKeyboardButton(text="📂 Моя запись", callback_data="menu:my_appointments")
    )
    builder.row(
        InlineKeyboardButton(text="💅 Прайсы", callback_data="menu:prices")
    )
    builder.row(
        InlineKeyboardButton(text="🖼 Портфолио", callback_data="menu:portfolio")
    )

    if is_admin:
        builder.row(
            InlineKeyboardButton(text="⚙️ Админ-панель", callback_data="menu:admin")
        )

    return builder.as_markup()


def back_to_menu_kb(is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⬅️ В меню", callback_data="menu:main")
    )

    if is_admin:
        builder.row(
            InlineKeyboardButton(text="⚙️ Админ-панель", callback_data="menu:admin")
        )

    return builder.as_markup()


def portfolio_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Смотреть портфолио",
            url="https://ru.pinterest.com/crystalwithluv/_created/"
        )
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ В меню", callback_data="menu:main")
    )
    return builder.as_markup()


def confirm_booking_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="booking:confirm")
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Изменить", callback_data="booking:restart")
    )
    builder.row(
        InlineKeyboardButton(text="❌ В меню", callback_data="menu:main")
    )
    return builder.as_markup()


def cancel_appointment_kb(appointment_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="❌ Отменить запись",
            callback_data=f"appointment:cancel:{appointment_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ В меню", callback_data="menu:main")
    )
    return builder.as_markup()