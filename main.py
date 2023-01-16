from logging import shutdown

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

from censored import token_tg, token_drf, drf_url

import requests
import json

bot = Bot(token=token_tg)
dp = Dispatcher(bot)

'''
Общие функции
'''


def get_token(telegram_id, group_id, telegram_name):
    '''
    :param telegram_id: id пользователя
    :param group_id: id группы телеграм
    :param telegram_name: имя пользователя телеграм
    :return: токен пользователя в drf
    '''
    headers = {
        "accept": "application/json",
        "Authorization": token_drf,
    }
    body = {
        "telegram_id": telegram_id,
        "group_id": group_id,
        "tg_name": telegram_name,
    }
    r = requests.post(drf_url + 'tg-get-user-token/', headers=headers, json=body)

    if 'token' in r.json():
        return r.json()['token']
    elif 'status' in r.json():
        return r.json()['status']
    elif 'detail' in r.json():
        return r.json()['detail']
    else:
        return 'Что то пошло не так'


def get_balance(token):
    '''
    :param token: токен пользователя в drf
    :return: json со статистикой пользователя
    :format:
    {
    'income':
    {'amount': 17.0, 'frozen': 0.0, 'sent': 0.0, 'received': 17.0, 'cancelled': 0.0},
    'distr':
    {'amount': 0.0, 'frozen': 0.0, 'sent': 0.0, 'received': 0.0, 'cancelled': 0.0, 'expire_date': '2023-01-30'}
    }
    - income - заработанные спасибки
                - amount - общее количество
                - frozen - на подтверждении
                - sent - отправлено
                - received - получено
                - cancelled - аннулировано
    - distr - спасибки для раздачи
                - amount - общее количество
                - expire_date - дата сгорания
                - frozen - на подтверждении
                - sent - отправлено
                - received - получено
                - cancelled - аннулировано
                '''

    if token == 'Что то пошло не так':
        return token
    elif token == 'Не найдена организация по переданному group_id':
        return token
    else:
        headers = {
            "accept": "application/json",
            'Authorization': token,
        }
        r = requests.get(drf_url + 'user/balance/', headers=headers)
        return r.json()


'''
Часть бота
'''


@dp.message_handler(commands=['count'])
async def count(message: types.Message):
    '''
    Выводит в текущий чат количество лайков у пользователя
    '''
    telegram_id = message.from_user.id
    group_id = message.chat.id
    telegram_name = message.from_user.username
    result = get_token(telegram_id, group_id, telegram_name)
    balance = get_balance(result)

    await message.reply(f"{balance}")


@dp.message_handler(commands=['like'])
async def like(message: types.Message):
    '''
    Добавляет лайк пользователю
    '''
    pass  # todo взаимодействие с DRF - запрос post , поставить лайк


@dp.message_handler(commands=['info'])
async def info(message: types.Message):
    await message.reply(f'id пользователя: {message.from_user.id}\n'
                        f'имя пользователя {message.from_user.username}\n'
                        f'id группы: {message.chat.id}')


@dp.message_handler()
async def donno(message: types.Message):
    await message.reply('Я не знаю что ответить')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_shutdown=shutdown)
