import asyncio
from idlelib.query import Query
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters.command import Command
from aiogram.types import Message, CallbackQuery
import sqlite3, aiosqlite
from aiogram.types import TelegramObject
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from time import sleep
from contextlib import suppress
import html

bot = Bot('7917941566:AAH8P2I1wPKh7p0mEbL5K2LaSuxs_yqsM2c')
dp = Dispatcher()

admin_ids = [5262838200, 5771083827]


class IsAdmin(BaseFilter):
    async def __call__(self, obj: TelegramObject) -> bool:
        return obj.from_user.id in admin_ids

class AdminState(StatesGroup):
    newsletter = State()

admin_keyboard = [
    [
        types.InlineKeyboardButton(text='Рассылка', callback_data='admin_newsletter'),
        types.InlineKeyboardButton(text='Статистика', callback_data='admin_statistic')
    ]
]
admin_keyboard = types.InlineKeyboardMarkup(inline_keyboard=admin_keyboard)


async def add_user(user_id, full_name, username):
    conn = await aiosqlite.connect('my_database1.db')
    cursor = await conn.cursor()
    check_user = await cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    check_user = await check_user.fetchone()
    if check_user is None:
        await cursor.execute('INSERT INTO users (user_id, full_name, username) VALUES (?, ?, ?)',
                             (user_id, full_name, username))
        await conn.commit()
    await cursor.close()
    await conn.close()


@dp.message(Command('start'))
async def start(message: Message):
    await add_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    await message.answer(f'<b>{html.escape(message.from_user.full_name)}</b>, добро пожаловать!')


@dp.message(Command('admin'), IsAdmin())
async def admin_command(message: types.Message) -> None:
    await message.answer('Добро пожаловать в Админ-панель!', reply_markup=admin_keyboard)
@dp.callback_query(F.data == 'undo')
async def admin_command2(callback: types.CallbackQuery):
    await callback.message.answer('Добро пожаловать в Админ-панель!', reply_markup=admin_keyboard)


async def get_user_count():
    connect = await aiosqlite.connect('my_database1.db')
    cursor = await connect.cursor()
    user_count = await cursor.execute('SELECT COUNT(*) FROM users')
    user_count = await user_count.fetchone()
    await cursor.close()
    await connect.close()
    return user_count[0]

keyboard2 = [
    [types.InlineKeyboardButton(text='◀️ Назад', callback_data='undo')]
]
keyboard2 = types.InlineKeyboardMarkup(inline_keyboard=keyboard2)

@dp.callback_query(F.data == 'admin_statistic', IsAdmin())
async def admin_statistic(call: types.CallbackQuery):
    user_count = await get_user_count()
    await call.message.edit_text('Статистика\n\n'
                                 f'Количество пользователей: {user_count}', reply_markup=keyboard2)


@dp.callback_query(F.data == 'admin_newsletter', IsAdmin())
async def admin_newsletter(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text('Рассылка\n\nВведите сообщение, которое будет отправлено пользователем')
    await state.set_state(AdminState.newsletter)

@dp.message(Command('get_data'))
async def get_data_command(message: types.Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    message_newsletter = user_data['message_newsletter']
    await message_newsletter.send_copy(message.from_user.id)

async def get_all_users_id():
    connect = await aiosqlite.connect('my_database1.db')
    cursor = await connect.cursor()
    all_ids = await cursor.execute('SELECT user_id FROM users')
    all_ids = await all_ids.fetchall()
    await cursor.close()
    await connect.close()
    return all_ids

@dp.message(AdminState.newsletter)
async def admin_newsletter_step_2(message: types.Message, state: FSMContext):
    k = 0
    all_ids = await get_all_users_id()
    print(all_ids)
    for user_id in all_ids:
        with suppress(Exception):
            await message.send_copy(user_id[0])
            k += 1
            await sleep(0.3)
    await state.clear()
    await message.answer(f'Отправлено: {k} пользователям \nНе получилось отправить: {len(all_ids) - k} пользователям')



async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    print('Бот запущен...')
    asyncio.run(main())