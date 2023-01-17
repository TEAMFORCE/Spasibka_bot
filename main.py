from logging import shutdown

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

from censored import token_tg

from API.api_requests import get_token, get_balance, send_like

import re


bot = Bot(token=token_tg)
dp = Dispatcher(bot)

'''
Часть бота
'''


async def on_startup(_):
    print('Бот запущен')


@dp.message_handler(content_types=['text'])
async def test(message: types.Message):
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

        await bot.send_message(message.chat.id, result)


@dp.message_handler(commands=['like'])
async def like(message: types.Message):
    '''
    Добавляет 1 лайк пользователю по цитируемому сообщению
    '''

    telegram_id = message.from_user.id
    group_id = str(message.chat.id)
    telegram_name = message.from_user.username
    token = get_token(telegram_id, group_id, telegram_name)

    telegram_id = str(message.reply_to_message.from_user.id)
    telegram_name = message.reply_to_message.from_user.username
    amount = 1

    result = send_like(token, telegram_id, telegram_name, amount)

    await bot.send_message(message.chat.id, result)


@dp.message_handler(commands=['баланс', 'balance'])
async def count(message: types.Message):
    '''
    Выводит в текущий чат количество спасибок у пользователя
    '''
    telegram_id = message.from_user.id
    group_id = message.chat.id
    telegram_name = message.from_user.username
    token = get_token(telegram_id, group_id, telegram_name)
    balance = get_balance(token)

    if balance == 'Что то пошло не так':
        await message.reply(balance)
    elif balance == 'Не найдена организация по переданному group_id':
        await message.reply(token)
    else:
        try:
            await message.reply(f"Заработанные спасибки: {int(balance['income']['amount'])}\n"
                                f"Спасибки для раздачи: {int(balance['distr']['amount'])}")
        except KeyError:
            await message.reply("Что то пошло не так")


@dp.message_handler(commands=['who'])
async def who(message: types.Message):
    try:
        telegram_id = message.reply_to_message.from_user.id
        telegram_name = message.reply_to_message.from_user.username

        await bot.send_message(message.chat.id, f'Id: {telegram_id}\n'
                                                f'Ник пользователя: {telegram_name}')
    except AttributeError:
        await bot.send_message(message.chat.id, 'Необходимо цитировать сообщение')


@dp.message_handler(commands=['info'])
async def info(message: types.Message):
    await message.reply(f'id пользователя: {message.from_user.id}\n'
                        f'имя пользователя {message.from_user.username}\n'
                        f'id группы: {message.chat.id}')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=shutdown)
