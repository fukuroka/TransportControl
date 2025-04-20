import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config.env import BOT_TOKEN, DB_NAME
from src import map_parser
from src.bus_stop_dao import BusStopDAO
from src.states import BusQuery

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = BusStopDAO(DB_NAME)


async def get_stops_keyboard(target, state: FSMContext):
    if db.conn is None:
        await db.connect()
    stops = await db.get_all_stops()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=stop, callback_data=f"stop_{stop}")] for stop in stops
        ]
    )
    await target.answer("Выбери остановку:", reply_markup=keyboard)
    await state.set_state(BusQuery.choosing_stop)


@dp.message(Command("start"))
async def send_welcome(message: Message, state: FSMContext):
    await message.answer("Привет! Чтобы начать, выбери остановку:")
    await get_stops_keyboard(message, state)


@dp.callback_query(lambda c: c.data.startswith("stop_"))
async def handle_stop_choice(callback: CallbackQuery, state: FSMContext):
    stop = callback.data.removeprefix("stop_")
    await state.update_data(stop_name=stop)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_stops")],
            [InlineKeyboardButton(text="🔄 Начать сначала", callback_data="restart")],
            [
                InlineKeyboardButton(
                    text="🚌 Посмотреть ближайшие автобусы", callback_data="all_buses"
                )
            ],
        ]
    )
    await callback.message.answer(
        f"Остановкa: {stop}\nТеперь введи номер маршрута или нажми кнопку:", reply_markup=keyboard
    )
    await state.set_state(BusQuery.choosing_route)
    await callback.answer()


@dp.callback_query(lambda c: c.data == "all_buses")
async def handle_all_buses(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    stop = data.get("stop_name")
    url = await db.get_stop_link(stop)
    text = map_parser.get_buses_info(url)
    await callback.message.answer(f"Ближайшие автобусы для остановки {stop}:\n{text}")
    await callback.answer()


@dp.callback_query(lambda c: c.data in {"back_to_stops", "restart"})
async def handle_navigation(callback: CallbackQuery, state: FSMContext):
    if callback.data == "restart":
        await state.clear()
        await callback.message.answer("Начнём сначала.")
    else:
        await callback.message.answer("Выбери другую остановку:")
    await get_stops_keyboard(callback.message, state)
    await callback.answer()


@dp.message(BusQuery.choosing_route)
async def handle_route_choice(message: Message, state: FSMContext):
    data = await state.get_data()
    stop = data.get("stop_name")
    route = message.text.strip()
    if not route.isdigit():
        await message.reply("Введите корректный номер маршрута.")
        return
    url = await db.get_stop_link(stop)
    text = map_parser.get_buses_info(url, route)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚌 Показать все автобусы", callback_data="all_buses")],
            [InlineKeyboardButton(text="🔄 Начать сначала", callback_data="restart")],
        ]
    )
    await message.answer(text, reply_markup=keyboard)
    await state.set_state(BusQuery.choosing_route)


@dp.message(Command("stop"))
async def stop_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Диалог завершён. Используй /start для начала.")


async def main():
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Начать"),
            BotCommand(command="stop", description="Остановить диалог"),
        ]
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
