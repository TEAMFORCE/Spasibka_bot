import os
import sys

import aiogram.utils.exceptions

sys.path.insert(1, os.path.join(sys.path[0], '..'))  # todo наверняка импорт можно сделать проще
from keyboards.inline_not_complited_transactions import not_complited_transactions
from keyboards.inline_user_organizations import get_user_organization_keyboard

from aiogram import types, Dispatcher
from create_bot import dp, bot
from API.api_requests import send_like, get_token, get_balance, user_organizations, get_token_by_organization_id,\
    export_file_transactions_by_group_id, export_file_transactions_by_organization_id

from dict_cloud import dicts

from database.database import create_user_if_not_exist, create_organization_if_not_exist, bind_user_org,\
    find_active_organization

import datetime


# @dp.message_handler(commands=['баланс', 'balance'])
async def balance(message: types.Message):
    '''
    Выводит в текущий чат количество спасибок у пользователя
    Если бот общается в ЛС, то выводит баланс по активной организации
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
    '''
    Выводит инлайн клавиатуру с не проведенными транзакциями
    '''
    try:
        await bot.send_message(
            message.from_user.id, 'Для отмены транзакции выберите соответствующую транзакции кнопку',
            reply_markup=not_complited_transactions)
    except:
        await message.reply(dicts.errors['no_chat_with_bot'])


# @dp.message_handler(commands=['go'])
async def go(message: types.Message):
    '''
    В личном общении выводит список доступных организаций в виде инлайн клавиатуры
    '''
    try:
        user = create_user_if_not_exist(tg_id=message.from_user.id, tg_username=message.from_user.username)

        for organization in user_organizations(telegram_id=message.from_user.id):
            org = create_organization_if_not_exist(org_name=organization['name'], id=organization['id'])
            bind_user_org(user=user, org=org)
        if message.from_user.id != message.chat.id:
            bot.delete_message(message.chat.id, message.message_id)
        await bot.send_message(
            message.from_user.id,
            'Укажите вашу организацию:',
            reply_markup=get_user_organization_keyboard(telegram_id=message.from_user.id)
        )
    except aiogram.utils.exceptions.CantInitiateConversation:
        await message.reply(dicts.errors['no_chat_with_bot'])


# @dp.message_handler(commands=['export'])
async def export(message: types.Message):
    '''
    Отправляет .xlxs фаил со списком транзакций, если общение в ЛС - то фаил формируется по активной группе
    '''
    telegram_id = message.from_user.id
    group_id = message.chat.id
    telegram_name = message.from_user.username
    now_date = datetime.datetime.now().strftime("%y-%m-%d")
    filename = f'Transactions_{now_date}_{telegram_name}'
    if telegram_id != group_id:
        response = export_file_transactions_by_group_id(telegram_id=telegram_id, group_id=group_id)
        try:
            r = response['message']
            await message.reply(r)
        except TypeError or KeyError:
            with open(f'{filename}.xlsx', 'wb') as file:
                file.write(response)
            await bot.send_document(document=open(f'{filename}.xlsx', 'rb'),
                                    chat_id=message.from_user.id
                                    )
            os.remove(f'{filename}.xlsx')
            await bot.delete_message(message.chat.id, message.message_id)
    else:
        organization_id = find_active_organization(tg_id=telegram_id)
        response = export_file_transactions_by_organization_id(telegram_id=telegram_id, organization_id=organization_id)
        try:
            r = response['message']
            await message.reply(r)
        except TypeError or KeyError:
            with open(f'{filename}.xlsx', 'wb') as file:
                file.write(response)
            await bot.send_document(document=open(f'{filename}.xlsx', 'rb'),
                                    chat_id=message.from_user.id
                                    )
            os.remove(f'{filename}.xlsx')
            await bot.delete_message(message.chat.id, message.message_id)


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(balance, commands=['баланс', 'balance'])
    dp.register_message_handler(ct, commands=['ct'])
    dp.register_message_handler(go, commands=['go'])
    dp.register_message_handler(export, commands=['export'])
