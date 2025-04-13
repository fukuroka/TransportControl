from aiogram.fsm.state import State, StatesGroup


class BusQuery(StatesGroup):
    choosing_stop = State()
    choosing_route = State()
