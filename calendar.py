from calendar import monthrange
from datetime import date, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
MONTHS_RU = {
    1: "Январь",
    2: "Февраль",
    3: "Март",
    4: "Апрель",
    5: "Май",
    6: "Июнь",
    7: "Июль",
    8: "Август",
    9: "Сентябрь",
    10: "Октябрь",
    11: "Ноябрь",
    12: "Декабрь",
}


async def calendar_kb(db, year: int | None = None, month: int | None = None) -> InlineKeyboardMarkup:
    today = date.today()

    if year is None:
        year = today.year
    if month is None:
        month = today.month

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=f"{MONTHS_RU[month]} {year}",
            callback_data="calendar:ignore"
        )
    )

    builder.row(*[
        InlineKeyboardButton(text=day, callback_data="calendar:ignore")
        for day in WEEKDAYS
    ])

    first_weekday, days_in_month = monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, days_in_month)

    available_dates = await db.get_available_dates_in_range(
        start_date.isoformat(),
        end_date.isoformat()
    )
    available_dates = set(available_dates)

    cells = []

    for _ in range(first_weekday):
        cells.append(InlineKeyboardButton(text=" ", callback_data="calendar:ignore"))

    for day_num in range(1, days_in_month + 1):
        current = date(year, month, day_num)
        current_str = current.isoformat()

        if current < today:
            text = "·"
            callback = "calendar:ignore"
        elif current_str in available_dates:
            text = str(day_num)
            callback = f"date:choose:{current_str}"
        else:
            text = f"•{day_num}"
            callback = "calendar:ignore"

        cells.append(InlineKeyboardButton(text=text, callback_data=callback))

    while len(cells) % 7 != 0:
        cells.append(InlineKeyboardButton(text=" ", callback_data="calendar:ignore"))

    for i in range(0, len(cells), 7):
        builder.row(*cells[i:i + 7])

    prev_year, prev_month = year, month - 1
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1

    next_year, next_month = year, month + 1
    if next_month > 12:
        next_month = 1
        next_year += 1

    limit_date = today + timedelta(days=31)
    can_go_prev = (year, month) > (today.year, today.month)
    can_go_next = date(next_year, next_month, 1) <= date(limit_date.year, limit_date.month, 1)

    builder.row(
        InlineKeyboardButton(
            text="⬅️" if can_go_prev else " ",
            callback_data=f"calendar:month:{prev_year}:{prev_month}" if can_go_prev else "calendar:ignore"
        ),
        InlineKeyboardButton(
            text="⬅️ В меню",
            callback_data="menu:main"
        ),
        InlineKeyboardButton(
            text="➡️" if can_go_next else " ",
            callback_data=f"calendar:month:{next_year}:{next_month}" if can_go_next else "calendar:ignore"
        ),
    )

    return builder.as_markup()