import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Тут добавляем наш токен от Telegram-бота
API_TOKEN = ''

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Путь к файлу с квартирами
APARTMENTS_FILE = "apartments.json"


# Функции для работы с файлом JSON, загрузка данных оттуда
def load_apartments():
    if not os.path.exists(APARTMENTS_FILE):
        return []
    with open(APARTMENTS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


# Функции для работы с файлом JSON, добавление данных туда
def save_apartments(apartments):
    with open(APARTMENTS_FILE, "w", encoding="utf-8") as file:
        json.dump(apartments, file, ensure_ascii=False, indent=4)


# Загрузка данных при старте
apartments = load_apartments()


# Машина состояний
class RentStates(StatesGroup):
    waiting_for_rooms = State()
    waiting_for_metro = State()
    waiting_for_description = State()
    waiting_for_rent_rooms = State()
    waiting_for_rent_metro = State()


# Начальная клавиатура
start_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔑 Арендовать квартиру")],
        [KeyboardButton(text="💰 Сдать квартиру")],
        [KeyboardButton(text="👁️ Показать все доступные варианты")]
    ],
    resize_keyboard=True
)


# Обрабатываем команду /start
@dp.message(Command("start"))
async def start(message: types.Message):
    print(f'❗️ Пользователь @{message.from_user.username} запустил бота.')
    await message.answer(
        "Добро пожаловать!\nЗдесь Вы можете сдать или арендовать квартиру в Москве.\n\n"
        "Разработчик: Владислав Лахтионов, @vladelo.",
        reply_markup=start_kb
    )


# Обрабатываем команду "💰 Сдать квартиру"
@dp.message(lambda message: message.text == "💰 Сдать квартиру")
async def rent_out(message: types.Message, state: FSMContext):
    await message.answer("💬 Введите количество комнат (например, 3):")
    await state.set_state(RentStates.waiting_for_rooms)


# Обрабатываем команду после "💬 Введите количество комнат (например, 3):"
@dp.message(RentStates.waiting_for_rooms)
async def enter_rooms(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗️ Пожалуйста, введите число.")
        return
    await state.update_data(rooms=int(message.text))
    await message.answer("💬 Введите станцию метро:")
    await state.set_state(RentStates.waiting_for_metro)


# Обрабатываем команду после "💬 Введите станцию метро:"
@dp.message(RentStates.waiting_for_metro)
async def enter_metro(message: types.Message, state: FSMContext):
    await state.update_data(metro=message.text)
    await message.answer("💬 Введите описание квартиры:")
    await state.set_state(RentStates.waiting_for_description)


# Обрабатываем команду после "💬 Введите описание квартиры:"
@dp.message(RentStates.waiting_for_description)
async def enter_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    new_apartment = {
        'rooms': data['rooms'],
        'metro': data['metro'],
        'description': message.text,
        'owner': message.from_user.username,
    }
    apartments.append(new_apartment)
    save_apartments(apartments)
    print(f'✅️ Пользователь @{message.from_user.username} добавил квартиру для сдачи.')
    await message.answer("🎉 Квартира успешно добавлена!")
    await state.clear()


# Обрабатываем команду "🔑 Арендовать квартиру"
@dp.message(lambda message: message.text == "🔑 Арендовать квартиру")
async def rent(message: types.Message, state: FSMContext):
    await message.answer("💬 Введите количество комнат:")
    await state.set_state(RentStates.waiting_for_rent_rooms)


# Обрабатываем команду после "💬 Введите количество комнат:"
@dp.message(RentStates.waiting_for_rent_rooms)
async def search_rooms(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗️ Пожалуйста, введите число.")
        return
    await state.update_data(rooms=int(message.text))
    await message.answer("💬 Введите станцию метро:")
    await state.set_state(RentStates.waiting_for_rent_metro)


# Обрабатываем команду после "💬 Введите станцию метро:"
@dp.message(RentStates.waiting_for_rent_metro)
async def search_metro(message: types.Message, state: FSMContext):
    data = await state.get_data()
    rooms = data['rooms']
    metro = message.text.lower()
    apartments = load_apartments()
    found_apartments = [apt for apt in apartments if apt['rooms'] == rooms and metro in apt['metro'].lower()]
    print(f'✅️ Пользователь @{message.from_user.username} ищет квартиру для аренды.')

    if found_apartments:
        result = "🔥 Найдены следующие квартиры:\n\n"
        for apt in found_apartments:
            result += f"🛌 Количество комнат: {apt['rooms']}\n"
            result += f"🚇 Станция метро: {apt['metro']}\n"
            result += f"💬 Описание: {apt['description']}\n"
            result += f"👑 Владелец: @{apt['owner']}\n\n"
        await message.answer(result)
    else:
        await message.answer("😔 Квартира с указанными параметрами не найдена.")

    await state.clear()


# Обрабатываем команду "👁️ Показать все доступные варианты"
@dp.message(lambda message: message.text == "👁️ Показать все доступные варианты")
async def view_all(message: types.Message):
    apartments = load_apartments()
    print(f'✅️ Пользователь @{message.from_user.username} смотрит все варианты.')

    if apartments:
        result = "🔥 Найдены следующие квартиры:\n\n"
        for apt in apartments:
            result += f"🛌 Количество комнат: {apt['rooms']}\n"
            result += f"🚇 Станция метро: {apt['metro']}\n"
            result += f"💬 Описание: {apt['description']}\n"
            result += f"👑 Владелец: @{apt['owner']}\n\n"
        await message.answer(result)
    else:
        await message.answer('😔 Нет сдающихся квартир.')


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    print(f'🚀 Telegram-бот успешно запущен!')
    asyncio.run(main())
