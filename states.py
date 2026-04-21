from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    choosing_date = State()
    choosing_time = State()
    waiting_for_name = State()
    waiting_for_phone = State()
    confirming = State()


class AdminStates(StatesGroup):
    waiting_for_day = State()
    waiting_for_slots_date = State()
    waiting_for_slots_list = State()
    waiting_for_close_day = State()
    waiting_for_view_day = State()