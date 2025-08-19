import aiosqlite


pending_referrals = {'user_id': 0}


async def process_pending_referral(user_id: int, bot):
    if user_id in pending_referrals:
        referrer_id = pending_referrals[user_id]

        conn = await aiosqlite.connect('Form.db')
        cursor = await conn.cursor()

        try:
            await cursor.execute('UPDATE Form SET Balance = Balance + 6 WHERE ID = ?', (referrer_id,))
            await cursor.execute("SELECT Referals FROM Form WHERE ID = ?", (referrer_id,))
            referals_row = await cursor.fetchone()
            current_referals = referals_row[0] if referals_row and referals_row[0] else ""
            new_referals = f"{current_referals} {user_id}".strip()
            await cursor.execute('UPDATE Form SET Referals = ? WHERE ID = ?', (new_referals, referrer_id))
            await conn.commit()

            text = f'👋 Вы зарегистрировались по ссылке <a href="tg://user?id={referrer_id}">пользователя</a>\nЕму начислено вознаграждение!'
            text2 = f'🎉 У вас новый <a href="tg://user?id={user_id}">реферал</a>!\nВам начислено 6 рублей!'

            await bot.send_message(chat_id=user_id, text=text, parse_mode='HTML')
            await bot.send_message(chat_id=referrer_id, text=text2, parse_mode='HTML')

        except Exception as e:
            print(f'Ошибка обработки реферала: {e}')
        finally:
            if user_id in pending_referrals:
                del pending_referrals[user_id]