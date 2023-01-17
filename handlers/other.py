from aiogram import types, Dispatcher
from create_bot import dp, bot
from api_requests import send_like, get_token
import re
import time


# @dp.message_handler(content_types=['text'])
async def likes(message: types.Message):
    '''
    При получении сообщения начинающегося с '+' отправляет лайки пользователю цитируемого сообщения
    :param message: Формат: +n 'необязательное сообщение', n-количество спасибок
    :return:
    '''
    if message.text.startswith('+'):
        pattern = r'\+(\d*)(.*)'
        likes = re.match(pattern, message.text).group(1)
        other = re.match(pattern, message.text).group(2)

        # await bot.send_message(message.chat.id, f'Количество лайков: {likes}\nНеобязательное сообщение: {other}')

        telegram_id = message.from_user.id
        group_id = str(message.chat.id)
        telegram_name = message.from_user.username
        token = get_token(telegram_id, group_id, telegram_name)

        telegram_id = str(message.reply_to_message.from_user.id)
        telegram_name = message.reply_to_message.from_user.username
        amount = likes

        result = send_like(token, telegram_id, telegram_name, amount)

        if result == 'Спасибка отправлена':
            await message.reply(f'Получатель: {telegram_name}\n'
                                f'{result}')
        else:
            await message.reply(result)


def register_handlers_other(dp: Dispatcher):
    dp.register_message_handler(likes, content_types=['text'])
