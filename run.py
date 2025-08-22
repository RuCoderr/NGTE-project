from aiogram import Dispatcher, F
from aiogram.filters import CommandObject, CommandStart, Command, BaseFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import TelegramObject
from aiogram.utils.deep_linking import create_start_link, decode_payload
from referral_storage import pending_referrals
from anketa import *
from admin_panel import *
from dotenv import load_dotenv
import os


load_dotenv()
admin_ids_str = os.getenv('ADMIN_IDS', '')
admins = list(map(int, admin_ids_str.split(','))) if admin_ids_str else []
DB_PATH = os.getenv('DATABASE_PATH', '/tmp/Form.db')


bot = Bot(TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class IsAdmin(BaseFilter):
    async def __call__(self, obj: TelegramObject) -> bool:
        return obj.from_user.id in admins



def get_ids():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT ID FROM Form')
    ids = cursor.fetchall()
    ids = [item[0] for item in ids]
    return ids

command_args = ''


async def start(message: Message, command: CommandObject):
    keyboard = [
        [types.KeyboardButton(text='💵 Работать')],
        [types.KeyboardButton(text='ℹ️ Информация'),
         types.KeyboardButton(text='📢 Написать куратору')],
        [types.KeyboardButton(text='🚪 Личный кабинет')]
    ]
    reply_markup = types.ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )
    user_id = message.from_user.id
    referrer_id = None

    if command.args:
        try:
            referrer_id = int(decode_payload(command.args))
        except:
            referrer_id = None
    conn = await aiosqlite.connect(DB_PATH)
    cursor = await conn.cursor()
    await cursor.execute("SELECT ID FROM Form")
    all_ids = [row[0] for row in await cursor.fetchall()]

    if referrer_id and referrer_id != user_id and user_id not in all_ids:
        await cursor.execute("SELECT 1 FROM Form WHERE ID = ?", (referrer_id,))
        if await cursor.fetchone():
            pending_referrals[user_id] = referrer_id


    await message.answer(
        'Привет! Я помогу тебе устроиться в престижную эстонскую компанию\n\n'
        'Для начала заполни анкету: /start_form',
        reply_markup=reply_markup
    )


async def rabota(message: Message):
    user_id = message.from_user.id
    if user_id not in get_ids():
        await message.answer("⛔ Сначала заполните анкету: \n/start_form")
        return

    user_id = message.from_user.id

    ref_link = await create_start_link(bot, payload=str(user_id), encode=True)
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(
            text="📤 Поделиться ссылкой",
            url=f"https://t.me/share/url?url={ref_link}&text=Присоединяйся!"
        )]
    ])

    conn = await aiosqlite.connect(DB_PATH)
    cursor = await conn.cursor()
    await cursor.execute("SELECT Status FROM Form WHERE ID = ?", (user_id,))
    status = await cursor.fetchone()
    t = (f"Вы ещё не полностью прошли процесс трудоустройства. Чтобы трудоустроиться - напишите куратору и он "
        f"вам всё объяснит" if status[0] == 'Не завершено' else "Вы трудоустроены, однако группа сотрудников ещё не полностью сформирована. "
                                                                "Основная работа пока не доступна") + ("\n\nА пока "
        "предлагаем вам воспользоваться нашей реферальной программой, приглашайте "
        f"рефералов и получайте дополнительный доход\n\n"
        f"🔗 Ваша реферальная ссылка:\n\n"
        f"<code>{ref_link}</code>\n\n"
        f"💰 За каждого приглашенного реферала вы получите 6 рублей!" )

    await message.answer(t, reply_markup=keyboard, parse_mode='HTML')


async def lk(message: Message):
    user_id = message.from_user.id
    if user_id not in get_ids():
        await message.answer("⛔ Сначала заполните анкету: \n/start_form")
        return
    conn = await aiosqlite.connect(DB_PATH)
    cursor = await conn.cursor()
    await cursor.execute("SELECT Balance FROM Form WHERE ID = ?", (user_id,))
    bal = await cursor.fetchone()
    await cursor.execute("SELECT Status FROM Form WHERE ID = ?", (user_id,))
    status = await cursor.fetchone()
    await cursor.execute("SELECT Code FROM Form WHERE ID = ?", (user_id,))
    code = await cursor.fetchone()
    await message.answer(f'Личный кабинет\n\n🆔 Ваш ID: <code>{user_id}</code>\n━━━━━━━━━━━━━━━━━━━━━━━━━\n💼 Ваш '
                         f'код сотрудника: <b>{int(code[0])}</b>\n💳 Ваш '
                         f'баланс: <b>{int(bal[0])} руб</b>\n📶 Трудоустройство: <b>{str(status[0])}</b>\n\n‼️Минимальный вывод: от 1000 рублей', parse_mode='HTML')


async def info(message: Message):
    user_id = message.from_user.id
    if user_id not in get_ids():
        await message.answer("⛔ Сначала заполните анкету: \n/start_form")
        return

    await message.answer('ℹ️ Информация о компании:Мы — Эстонская компания Next-Gen Tech-Ecosystems, которая активно '
    'предоставляет наши консалтинговые услуги на всей территории Российской Федерации. Наши специалисты помогают '
    'настоящим технологическим IT гигантам модернизировать и внедрять новые технологии. Мы сотрудничаем на данный момент'
    ' с такими гигантами, как: Яндекс, Ozon, 3Logic Group, VK, Лаборатория Касперского. \n\nРуководство по пользованию ботом: \n\n💵 '
    'Работа - в этом разделе вы можете найти активные на данный момент задания, за выполнение которых получите средства '
    'на счёт \n🚪 Личный кабинет - в этом разделе содержится информация о вашем профиле в боте \n📢 Написать куратору - '
    'используйте эту кнопку, если у вас появился вопрос / вы хотите вывести деньги с вашего счета. Когда куратор '
    'появится в сети, он ответит на ваше сообщение \n\n❗ Чтобы вывести деньги с баланса бота, нужно завершить процесс '
                         'трудоустройства.  Все вопросы по поводу трудоустройства уточняйте у куратора')


async def curator(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in get_ids():
        await message.answer("⛔ Сначала заполните анкету: \n/start_form")
        return

    await message.answer('Введите сообщение, которое хотите отправить куратору \n\n❗Важно❗\n '
                         'Если вы подаёте заявку на вывод, то напишите: Я хочу вывести (сумма)')
    await state.set_state(ToCurator.mess)

async def curator2(message: Message, state: FSMContext):
    try:
        for user_id in admins:
            with suppress(Exception):
                if message.photo:
                    caption = message.caption if message.caption else ""
                    await bot.send_photo(chat_id=user_id, photo=message.photo[-1].file_id, caption=caption)
                else:
                    await bot.send_message(chat_id=user_id, text=f'{message.text}\n\nСообщение было отправлено пользователем <code>{message.from_user.id}</code>', parse_mode='HTML')
                await sleep(0.3)

        await message.answer('👽 Сообщение отправлено')
    except Exception as e:
        await message.answer(f'☢️ Ошибка отправки: {str(e)}')
    finally:
        await state.clear()



def register_handlers(dp: Dispatcher):
    dp.message.register(start, CommandStart())

    dp.message.register(start_form, F.text == '/start_form')
    dp.message.register(process_name, Form.name)
    dp.message.register(process_age, Form.age)
    dp.message.register(process_passport, Form.passport)
    dp.message.register(process_zarplata, Form.zarplata)
    dp.message.register(process_hobbies, Form.hobbies)
    dp.message.register(process_banks, Form.banks)

    dp.message.register(rabota, F.text == '💵 Работать')
    dp.message.register(lk, F.text == '🚪 Личный кабинет')
    dp.message.register(info, F.text == 'ℹ️ Информация')
    dp.message.register(curator, F.text == '📢 Написать куратору')

    dp.message.register(admin_command, Command('admin'), IsAdmin())
    dp.message.register(get_db, F.text == '/db', IsAdmin())

    dp.callback_query.register(newsletter_handler, F.data == 'newsletter')
    dp.message.register(process_newsletter_message, AdminState.newsletter)

    dp.callback_query.register(letter_get_id, F.data == 'letter')
    dp.message.register(letter_get_message, Letter.idd)
    dp.message.register(letter_send_message, Letter.mess)

    dp.callback_query.register(edit_balance, F.data == 'balance')
    dp.message.register(edit_balance2, Balance.idd)
    dp.message.register(edit_balance3, Balance.mess)

    dp.callback_query.register(edit_status, F.data == 'status')
    dp.message.register(edit_status2, Status.idd)
    dp.message.register(edit_status3, Status.mess)

    dp.callback_query.register(get_list, F.data == 'list')

    dp.message.register(curator2, ToCurator.mess)
