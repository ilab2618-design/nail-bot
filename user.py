from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import config
from database.db import Database
from keyboards.calendar import calendar_kb
from keyboards.common import (
    main_menu_kb,
    back_to_menu_kb,
    portfolio_kb,
    confirm_booking_kb,
    cancel_appointment_kb,
)
from keyboards.admin import admin_menu_kb
from states import BookingStates

router = Router()


def format_date_ru(date_str: str) -> str:
    return f"{date_str[8:10]}.{date_str[5:7]}.{date_str[:4]}"


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "<b>Добро пожаловать 💅</b>\n\nВыберите действие:",
        reply_markup=main_menu_kb(is_admin=message.from_user.id == config.admin_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "menu:main")
async def menu_main(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        "<b>Главное меню</b>\n\nВыберите действие:",
        reply_markup=main_menu_kb(is_admin=callback.from_user.id == config.admin_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "menu:admin")
async def open_admin_from_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()

    if callback.from_user.id != config.admin_id:
        await callback.answer("Нет доступа", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text(
        "<b>Админ-панель</b>",
        reply_markup=admin_menu_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "menu:prices")
async def show_prices(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(
        "<b>💅 Прайсы</b>\n\n"
        "Френч — <b>1000₽</b>\n"
        "Квадрат — <b>500₽</b>",
        reply_markup=back_to_menu_kb(is_admin=callback.from_user.id == config.admin_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "menu:portfolio")
async def show_portfolio(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(
        "<b>Портфолио</b>\n\nНажмите кнопку ниже:",
        reply_markup=portfolio_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "menu:book")
async def booking_start(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    await callback.answer()

    try:
        existing = await db.get_active_appointment_by_user(callback.from_user.id)

        if existing:
            appointment_id = existing["id"] if isinstance(existing, dict) else existing[0]
            work_date = existing["work_date"] if isinstance(existing, dict) else existing[1]
            slot_time = existing["slot_time"] if isinstance(existing, dict) else existing[2]

            await callback.message.edit_text(
                "<b>У вас уже есть активная запись</b>\n\n"
                f"📅 Дата: <b>{format_date_ru(work_date)}</b>\n"
                f"⏰ Время: <b>{slot_time}</b>\n\n"
                "Сначала отмените её.",
                reply_markup=cancel_appointment_kb(appointment_id),
                parse_mode="HTML",
            )
            return

        await state.set_state(BookingStates.choosing_date)
        await callback.message.edit_text(
            "<b>Выберите дату 📅</b>\n\nНажмите на свободный день:",
            reply_markup=await calendar_kb(db),
            parse_mode="HTML",
        )

    except Exception as e:
        print("BOOKING ERROR:", e)
        await callback.message.answer(
            f"Ошибка:\n<code>{str(e)}</code>",
            parse_mode="HTML"
        )


@router.callback_query(F.data == "calendar:ignore")
async def calendar_ignore(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data.startswith("calendar:month:"))
async def change_month(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    await callback.answer()
    _, _, year, month = callback.data.split(":")
    await state.set_state(BookingStates.choosing_date)
    await callback.message.edit_text(
        "<b>Выберите дату 📅</b>\n\nНажмите на свободный день:",
        reply_markup=await calendar_kb(db, int(year), int(month)),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("date:choose:"))
async def select_date(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    await callback.answer()

    work_date = callback.data.split(":")[-1]
    slots = await db.get_available_slots_by_date(work_date)

    if not slots:
        await callback.message.edit_text(
            "❌ На этот день нет свободного времени",
            reply_markup=main_menu_kb(is_admin=callback.from_user.id == config.admin_id),
        )
        return

    builder = InlineKeyboardBuilder()

    for slot in slots:
        slot_id = slot["id"] if isinstance(slot, dict) else slot[0]
        slot_time = slot["slot_time"] if isinstance(slot, dict) else slot[1]

        builder.button(
            text=slot_time,
            callback_data=f"slot:choose:{slot_id}"
        )

    builder.adjust(3)
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:book")
    )

    await state.update_data(work_date=work_date)
    await state.set_state(BookingStates.choosing_time)

    await callback.message.edit_text(
        f"<b>📅 Дата:</b> {format_date_ru(work_date)}\n\n<b>Выберите время:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("slot:choose:"))
async def choose_time(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    await callback.answer()
    slot_id = int(callback.data.split(":")[-1])

    slot = await db.fetchone(
        """
        SELECT ts.id, ts.slot_time, wd.work_date
        FROM time_slots ts
        JOIN work_days wd ON wd.id = ts.work_day_id
        WHERE ts.id = ? AND ts.is_booked = 0 AND wd.is_closed = 0
        """,
        (slot_id,)
    )

    if not slot:
        await callback.message.edit_text(
            "❌ Это время уже занято",
            reply_markup=back_to_menu_kb(is_admin=callback.from_user.id == config.admin_id)
        )
        return

    slot_time = slot["slot_time"] if isinstance(slot, dict) else slot[1]
    work_date = slot["work_date"] if isinstance(slot, dict) else slot[2]

    await state.update_data(slot_id=slot_id, slot_time=slot_time, work_date=work_date)
    await state.set_state(BookingStates.waiting_for_name)

    await callback.message.edit_text(
        f"<b>Дата:</b> {format_date_ru(work_date)}\n"
        f"<b>Время:</b> {slot_time}\n\n"
        "<b>Введите ваше имя:</b>",
        parse_mode="HTML"
    )


@router.message(BookingStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()

    if len(name) < 2:
        await message.answer("Введите корректное имя")
        return

    await state.update_data(client_name=name)
    await state.set_state(BookingStates.waiting_for_phone)

    await message.answer(
        "<b>Введите номер телефона:</b>\n\nПример: <code>+79991234567</code>",
        parse_mode="HTML"
    )


@router.message(BookingStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()

    if len(phone) < 6:
        await message.answer("Введите корректный номер телефона")
        return

    await state.update_data(client_phone=phone)
    data = await state.get_data()
    await state.set_state(BookingStates.confirming)

    await message.answer(
        "<b>Подтвердите запись</b>\n\n"
        f"👤 Имя: <b>{data['client_name']}</b>\n"
        f"📞 Телефон: <b>{data['client_phone']}</b>\n"
        f"📅 Дата: <b>{format_date_ru(data['work_date'])}</b>\n"
        f"⏰ Время: <b>{data['slot_time']}</b>",
        reply_markup=confirm_booking_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "booking:restart")
async def booking_restart(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    await callback.answer()
    await state.clear()
    await state.set_state(BookingStates.choosing_date)

    await callback.message.edit_text(
        "<b>Выберите дату 📅</b>\n\nНажмите на свободный день:",
        reply_markup=await calendar_kb(db),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "booking:confirm")
async def booking_confirm(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    await callback.answer()

    data = await state.get_data()
    slot_id = data["slot_id"]

    slot = await db.fetchone(
        """
        SELECT ts.id, ts.is_booked
        FROM time_slots ts
        WHERE ts.id = ?
        """,
        (slot_id,)
    )

    if not slot:
        await callback.message.edit_text(
            "Слот не найден",
            reply_markup=back_to_menu_kb(is_admin=callback.from_user.id == config.admin_id)
        )
        await state.clear()
        return

    is_booked = slot["is_booked"] if isinstance(slot, dict) else slot[1]
    if is_booked:
        await callback.message.edit_text(
            "Это время уже занято",
            reply_markup=back_to_menu_kb(is_admin=callback.from_user.id == config.admin_id)
        )
        await state.clear()
        return

    await db.execute(
        """
        INSERT INTO appointments (user_id, client_name, phone, slot_id, status)
        VALUES (?, ?, ?, ?, 'booked')
        """,
        (
            callback.from_user.id,
            data["client_name"],
            data["client_phone"],
            slot_id,
        )
    )

    await db.execute(
        "UPDATE time_slots SET is_booked = 1 WHERE id = ?",
        (slot_id,)
    )

    await db.commit()
    await state.clear()

    await callback.message.edit_text(
        "<b>✅ Запись успешно создана</b>\n\n"
        f"👤 Имя: <b>{data['client_name']}</b>\n"
        f"📞 Телефон: <b>{data['client_phone']}</b>\n"
        f"📅 Дата: <b>{format_date_ru(data['work_date'])}</b>\n"
        f"⏰ Время: <b>{data['slot_time']}</b>",
        reply_markup=back_to_menu_kb(is_admin=callback.from_user.id == config.admin_id),
        parse_mode="HTML"
    )

    try:
        await callback.bot.send_message(
            config.admin_id,
            "<b>Новая запись 💅</b>\n\n"
            f"👤 Имя: <b>{data['client_name']}</b>\n"
            f"📞 Телефон: <b>{data['client_phone']}</b>\n"
            f"📅 Дата: <b>{format_date_ru(data['work_date'])}</b>\n"
            f"⏰ Время: <b>{data['slot_time']}</b>\n"
            f"🆔 User ID: <code>{callback.from_user.id}</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        print("ADMIN NOTIFY ERROR:", e)


@router.callback_query(F.data == "menu:my_appointments")
async def my_appointments(callback: CallbackQuery, db: Database) -> None:
    await callback.answer()

    appointment = await db.get_active_appointment_by_user(callback.from_user.id)

    if not appointment:
        await callback.message.edit_text(
            "<b>У вас нет активной записи</b>",
            reply_markup=back_to_menu_kb(is_admin=callback.from_user.id == config.admin_id),
            parse_mode="HTML",
        )
        return

    appointment_id = appointment["id"] if isinstance(appointment, dict) else appointment[0]
    work_date = appointment["work_date"] if isinstance(appointment, dict) else appointment[1]
    slot_time = appointment["slot_time"] if isinstance(appointment, dict) else appointment[2]

    await callback.message.edit_text(
        "<b>Ваша запись</b>\n\n"
        f"📅 Дата: <b>{format_date_ru(work_date)}</b>\n"
        f"⏰ Время: <b>{slot_time}</b>",
        reply_markup=cancel_appointment_kb(appointment_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("appointment:cancel:"))
async def cancel_appointment(callback: CallbackQuery, db: Database) -> None:
    await callback.answer()
    appointment_id = int(callback.data.split(":")[-1])

    appointment = await db.fetchone(
        "SELECT id, slot_id, user_id FROM appointments WHERE id = ? AND status = 'booked'",
        (appointment_id,)
    )

    if not appointment:
        await callback.message.edit_text(
            "Запись не найдена или уже отменена",
            reply_markup=back_to_menu_kb(is_admin=callback.from_user.id == config.admin_id)
        )
        return

    slot_id = appointment["slot_id"] if isinstance(appointment, dict) else appointment[1]
    user_id = appointment["user_id"] if isinstance(appointment, dict) else appointment[2]

    if user_id != callback.from_user.id:
        await callback.answer("Нельзя отменить чужую запись", show_alert=True)
        return

    await db.execute(
        "UPDATE appointments SET status = 'cancelled' WHERE id = ?",
        (appointment_id,)
    )

    await db.execute(
        "UPDATE time_slots SET is_booked = 0 WHERE id = ?",
        (slot_id,)
    )

    await db.commit()

    await callback.message.edit_text(
        "<b>Запись отменена</b>\n\nСлот снова доступен для бронирования.",
        reply_markup=back_to_menu_kb(is_admin=callback.from_user.id == config.admin_id),
        parse_mode="HTML"
    )