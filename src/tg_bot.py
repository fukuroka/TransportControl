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


async def get_stops_keyboard(message_or_callback, state: FSMContext):
    if db.conn is None:
        await db.connect()

    stops = await db.get_all_stops()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=stop_name, callback_data=f"stop_{stop_name}")]
            for stop_name in stops
        ]
    )

    await message_or_callback.answer("Выбери остановку:", reply_markup=keyboard)
    await state.set_state(BusQuery.choosing_stop)


@dp.message(Command("start"))
async def send_welcome(message: Message, state: FSMContext):
    if db.conn is None:
        await db.connect()

    await message.answer("Привет!\nВыбери остановку:")
    await get_stops_keyboard(message, state)


@dp.callback_query(lambda c: c.data.startswith("stop_"))
async def handle_stop_choice(callback: CallbackQuery, state: FSMContext):
    stop_name = callback.data.removeprefix("stop_")
    await state.update_data(stop_name=stop_name)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_stops")],
            [InlineKeyboardButton(text="🔄 Начать сначала", callback_data="restart")],
        ]
    )

    await callback.message.answer("Теперь введи номер маршрута:", reply_markup=keyboard)
    await state.set_state(BusQuery.choosing_route)
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
    if db.conn is None:
        await db.connect()

    data = await state.get_data()
    stop_id = data.get("stop_name")
    route_number = message.text.strip()

    if not route_number.isdigit():
        await message.reply("Неверный формат маршрута. Попробуй снова.")
        return

    url = await db.get_stop_link(stop_id)
    result_text = map_parser.get_bus_arrival_info(route_number, url)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Проверить снова", callback_data=f"stop_{stop_id}")],
            [InlineKeyboardButton(text="🔄 Начать сначала", callback_data="restart")],
        ]
    )

    await message.answer(result_text, reply_markup=keyboard)
    await state.clear()


@dp.message(Command("stop"))
async def stop_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Диалог завершён. Чтобы начать заново, напиши /start.")


async def main():
    try:
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="Начать сначала"),
                BotCommand(command="stop", description="Остановить диалог"),
            ]
        )
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
