import os
import sys

import aiogram.utils.exceptions

sys.path.insert(1, os.path.join(sys.path[0], '..'))  # todo наверняка импорт можно сделать проще
from keyboards.inline_not_complited_transactions import not_complited_transactions
from keyboards.inline_user_organizations import get_user_organization_keyboard

from aiogram import types, Dispatcher
from create_bot import dp, bot
from API.api_requests import send_like, get_token, get_balance, user_organizations, get_token_by_organization_id

from dict_cloud import dicts

from database.database import create_user_if_not_exist, create_organization_if_not_exist, bind_user_org, find_active_organization


# @dp.message_handler(commands=['баланс', 'balance'])
async def balance(message: types.Message):
    '''
    Выводит в текущий чат количество спасибок у пользователя
    '''
    telegram_id = message.from_user.id
    telegram_name = message.from_user.username
    if message.chat.id != telegram_id:
        group_id = message.chat.id
        token = get_token(telegram_id, group_id, telegram_name)
    else:
        organization_id = str(find_active_organization(telegram_id))
        token = get_token_by_organization_id(telegram_id, organization_id, telegram_name)

    balance = get_balance(token)

    if balance == 'Что то пошло не так':
        await message.reply(balance)
    elif balance == 'Не найдена организация по переданному group_id':
        await message.reply(token)
    else:
        try:
            await message.reply(f'*Баланс:*\n'
                                f'Начальный баланс: _{int(balance["distr"]["amount"]) + int(balance["distr"]["sent"])}_\n'
                                f'Отправлено: _{int(balance["distr"]["sent"])}_\n'
                                f'Получено: _{int(balance["income"]["amount"])}_\n'
                                f'Доступно для распределения: _{int(balance["distr"]["amount"])}_\n'
                                f'Сгорят: _{int(balance["distr"]["amount"]) + int(balance["distr"]["sent"]) - int(balance["distr"]["sent"])}_',
                                parse_mode="Markdown")
        except KeyError:
            await message.reply("Что то пошло не так")


# @dp.message_handler(commands=['ct'])
async def ct(message: types.Message):
    try:
        await bot.send_message(
            message.from_user.id, 'Для отмены транзакции выберите соответствующую транзакции кнопку',
            reply_markup=not_complited_transactions)
    except:
        await message.reply(dicts.errors['no_chat_with_bot'])


# @dp.message_handler(commands=['go'])
async def go(message: types.Message):
    try:
        user = create_user_if_not_exist(tg_id=message.from_user.id, tg_username=message.from_user.username)

        for organization in user_organizations(telegram_id=message.from_user.id):
            org = create_organization_if_not_exist(org_name=organization['name'], id=organization['id'])
            bind_user_org(user=user, org=org)

        await bot.send_message(
            message.from_user.id,
            'Укажите вашу организацию:',
            reply_markup=get_user_organization_keyboard(telegram_id=message.from_user.id)
        )
    except aiogram.utils.exceptions.CantInitiateConversation:
        await message.reply(dicts.errors['no_chat_with_bot'])


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(balance, commands=['баланс', 'balance'])
    dp.register_message_handler(ct, commands=['ct'])
    dp.register_message_handler(go, commands=['go'])
