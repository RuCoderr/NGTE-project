import aiosqlite, sqlite3
from time import sleep
from contextlib import suppress
from aiogram.fsm.context import FSMContext
from aiogram import types, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from states import *
from tok import TOKEN
from dotenv import load_dotenv
import os

load_dotenv()
bot = Bot(TOKEN)
DB_PATH = os.getenv('DATABASE_PATH', '/tmp/bot.db')


def get_ids():
    conn = sqlite3.connect('Form.db')
    cursor = conn.cursor()
    cursor.execute('SELECT ID FROM Form')
    ids = cursor.fetchall()
    ids = [item[0] for item in ids]
    return ids


async def admin_command(message: Message):
    t = types.InlineKeyboardButton
    admin_keyboard = [[t(text='Рассылка', callback_data='newsletter'), t(text='Письмо', callback_data='letter')],
                      [t(text='Изменить баланс', callback_data='balance'), t(text='Изменить статус',
                      callback_data='status')], [t(text='Получить список юзеров и банков', callback_data='list')]]
    admin_keyboard = types.InlineKeyboardMarkup(inline_keyboard=admin_keyboard)
    await message.answer('Здравствуйте, господин Американское Яйцо, что хотите сделать?',
                         reply_markup=admin_keyboard)


async def newsletter_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Введи сообщение для рассылки брат:')
    await state.set_state(AdminState.newsletter)
    await callback.answer()


async def process_newsletter_message(message: Message, state: FSMContext, bot: Bot):
    try:
        user_ids = get_ids()
        for user_id in user_ids:
            try:
                if message.photo:
                    caption = message.caption if message.caption else ""
                    await bot.send_photo(chat_id=user_id, photo=message.photo[-1].file_id, caption=caption)
                else:
                    await bot.send_message(chat_id=user_id, text=message.text)
                sleep(0.3)
            except Exception as e:
                await message.answer(f'☢️ Ошибка рассылки: {str(e)}')

        await message.answer('👽 Рассылка проведена успешно')
    except Exception as e:
        await message.answer(f'☢️ Ошибка рассылки: {str(e)}')
    finally:
        await state.clear()


async def letter_get_id(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Введи ID адресата')
    await state.set_state(Letter.idd)
    await callback.answer()

async def letter_get_message(message: Message, state: FSMContext):
    await state.update_data(idd=message.text)
    await message.answer('Введи сообщение')
    await state.set_state(Letter.mess)

async def letter_send_message(message: Message, state: FSMContext):
    data = await state.get_data()
    recipient_id = data.get('idd')
    try:
        with suppress(Exception):
            if message.photo:
                caption = message.caption if message.caption else ""
                await bot.send_photo(chat_id=recipient_id, photo=message.photo[-1].file_id, caption=caption)
            elif message.text:
                await bot.send_message(chat_id=recipient_id, text=message.text)
            await sleep(0.3)

        await message.answer('👽 Сообщение отправлено')
    except Exception as e:
        await message.answer(f'☢️ Ошибка отправки: {str(e)}')
    finally:
        await state.clear()


async def edit_balance(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Balance.idd)
    await callback.message.answer('Введи ID пользователя')
    await callback.answer()


async def edit_balance2(message: Message, state: FSMContext):
    await state.update_data(idd=message.text)
    data = await state.get_data()
    user_id = data.get('idd')
    conn = await aiosqlite.connect('Form.db')
    cursor = await conn.cursor()
    await cursor.execute("SELECT Balance FROM Form WHERE ID = ?", (user_id,))
    bal = await cursor.fetchone()
    await message.answer(f'Баланс этого болванчика: <b>{int(tuple(bal)[0])}</b> \n\nНапиши на какой хочешь изменить', parse_mode='HTML')
    await state.set_state(Balance.mess)

async def edit_balance3(message: Message, state: FSMContext):
    await state.update_data(mess=message.text)
    data = await state.get_data()
    user_id = data.get('idd')
    conn = await aiosqlite.connect('Form.db')
    cursor = await conn.cursor()
    await cursor.execute("UPDATE Form SET Balance = ? WHERE ID = ?", (int(message.text), user_id))
    await conn.commit()
    await message.answer('Всё готово брат. Сделали всё по красоте')
    await state.clear()


async def edit_status(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Status.idd)
    await callback.message.answer('Введи ID пользователя')
    await callback.answer()


async def edit_status2(message: Message, state: FSMContext):
    await state.update_data(idd=message.text)
    data = await state.get_data()
    user_id = data.get('idd')
    conn = await aiosqlite.connect('Form.db')
    cursor = await conn.cursor()
    await cursor.execute("SELECT Status FROM Form WHERE ID = ?", (user_id,))
    bal = await cursor.fetchone()
    await message.answer(f'Статус этого болванчика: <b>{tuple(bal)[0]}</b> \n\nНапиши на какой хочешь изменить', parse_mode='HTML')
    await state.set_state(Status.mess)

async def edit_status3(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get('idd')
    conn = await aiosqlite.connect('Form.db')
    cursor = await conn.cursor()
    await cursor.execute("UPDATE Form SET Status = ? WHERE ID = ?", (message.text, user_id))
    await conn.commit()
    await message.answer('Всё готово брат. Сделали всё по красоте')
    await state.clear()


async def get_list(callback: CallbackQuery):
    conn = await aiosqlite.connect('Form.db')
    cursor = await conn.cursor()
    lst = []
    ids = get_ids()
    for el in ids:
        await cursor.execute('SELECT Code, Username, ID, Banks FROM Form WHERE ID = ?', (el,))
        l = await cursor.fetchall()
        lst.append(l[0])

    formatted_lines = []
    for item in lst:
        line = (
            f"{item[0]} "
            f"<code>{item[1]}</code> "
            f"<code>{item[2]}</code> "
            f"{item[3]}"
        )
        formatted_lines.append(line)
    result = "\n\n".join(formatted_lines)
    await callback.message.answer(result, parse_mode='HTML')


async def get_db(message: Message):
    try:
        with open(DB_PATH, "rb") as file:
            db_data = file.read()

        await message.bot.send_document(
            chat_id=message.chat.id,
            document=BufferedInputFile(
                db_data,
                filename="Form.db"
            ),
            caption="📂 Резервная копия базы данных"
        )

    except Exception as e:
        await message.answer(f"Ошибка: {e}")
