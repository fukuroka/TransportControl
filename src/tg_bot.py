import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config.env import BOT_TOKEN, DB_NAME
from src import map_parser
from src.bus_stop_dao import BusStopDAO
from src.states import BusQuery

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = BusStopDAO(DB_NAME)

# --- Модуль Telegram-бота (aiogram) ---


@dp.message(Command("start"))
async def send_welcome(message: Message, state: FSMContext):
    await message.answer("Привет!\nВыбери остановку:")
    stops = [stop[0] for stop in db.get_all_stops()]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=stop_name, callback_data=f"stop_{stop_name}")]
            for stop_name in stops
        ]
    )
    await message.answer("Список остановок:", reply_markup=keyboard)
    await state.set_state(BusQuery.choosing_stop)


@dp.callback_query(lambda c: c.data.startswith("stop_"))
async def handle_stop_choice(callback: CallbackQuery, state: FSMContext):
    stop_name = callback.data.split("_")[1]
    await state.update_data(stop_name=stop_name)
    await callback.message.answer("Теперь введи номер маршрута:")
    await state.set_state(BusQuery.choosing_route)
    await callback.answer()


@dp.message(BusQuery.choosing_route)
async def handle_route_choice(message: Message, state: FSMContext):
    data = await state.get_data()
    stop_id = data.get("stop_name")
    route_number = message.text.strip()
    if not route_number.isdigit():
        await message.reply("Неверный формат маршрута. Попробуй снова.")
        return

    url = db.get_stop_link(stop_id)
    result_text = map_parser.get_bus_arrival_info(route_number, url)
    await message.answer(result_text)
    await state.clear()


async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
