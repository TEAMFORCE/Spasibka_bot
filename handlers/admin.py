"""
Раздел только для тестов с проверкой ID
"""

from aiogram import types, Dispatcher
from create_bot import dp, bot
from API.api_requests import send_like, get_token


ID = [5148438149, ]


# @dp.message_handler(commands=['like'])
async def like(message: types.Message):
    """
    Добавляет 1 лайк пользователю по цитируемому сообщению
    """
    if message.from_user.id in ID:
        telegram_id = message.from_user.id
        group_id = str(message.chat.id)
        telegram_name = message.from_user.username
        token = get_token(telegram_id, group_id, telegram_name)

        telegram_id = str(message.reply_to_message.from_user.id)
        telegram_name = message.reply_to_message.from_user.username
        amount = 1

        result = send_like(token, telegram_id, telegram_name, amount)

        await bot.send_message(message.chat.id, result)


# @dp.message_handler(commands=['who'])
async def who(message: types.Message):
    """
    Необходимо цитировать сообщение. Выводит информацию о пользователе в ответном сообщении
    """
    if message.from_user.id in ID:
        try:
            telegram_id = message.reply_to_message.from_user.id
            telegram_name = message.reply_to_message.from_user.username
            telegram_group_id = message.reply_to_message.chat.id

            await bot.send_message(message.chat.id, f'Id: {telegram_id}\n'
                                                    f'Ник пользователя: {telegram_name}\n'
                                                    f'Id группы: {telegram_group_id}')
        except AttributeError:
            await bot.send_message(message.chat.id, 'Необходимо цитировать сообщение')


# @dp.message_handler(commands=['info'])
async def info(message: types.Message):
    """
    Выводит информацию об отправителе
    """
    if message.from_user.id in ID:
        await message.reply(f'id пользователя: {message.from_user.id}\n'
                            f'имя пользователя {message.from_user.username}\n'
                            f'id группы: {message.chat.id}')


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(like, commands=['like'])
    dp.register_message_handler(who, commands=['who'])
    dp.register_message_handler(info, commands=['info'])
