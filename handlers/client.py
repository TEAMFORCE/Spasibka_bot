import os
import sys

import aiogram.utils.exceptions

sys.path.insert(1, os.path.join(sys.path[0], '..'))  # todo наверняка импорт можно сделать проще
from keyboards.inline_not_complited_transactions import not_complited_transactions
from keyboards.inline_user_organizations import get_user_organization_keyboard
from keyboards.inline_webapp_test import start_web_app

from aiogram import types, Dispatcher
from create_bot import dp, bot
from API.api_requests import send_like, get_token, get_balance, user_organizations, get_token_by_organization_id,\
    export_file_transactions_by_group_id, export_file_transactions_by_organization_id

from dict_cloud import dicts

from database.database import create_user_if_not_exist, create_organization_if_not_exist, bind_user_org,\
    find_active_organization

import datetime

import asyncio
from contextlib import suppress
from aiogram.utils.exceptions import MessageToEditNotFound, MessageCantBeEdited, MessageCantBeDeleted, \
    MessageToDeleteNotFound

from dict_cloud.dicts import sleep_timer


async def delete_message(message: types.Message, sleep_time: int = 0):
    '''
    Удаляет сообщение по истичению таймера sleep_time
    '''
    await asyncio.sleep(sleep_time)
    with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
        await message.delete()


# @dp.message_handler(commands=['test'])
async def test(message: types.Message):
    msg = await message.reply('Это сообщение будет удалено через 5 секунд')
    asyncio.create_task(delete_message(msg, 5))


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
        answer = await message.reply(balance)
        await delete_message(answer, sleep_timer)
    elif balance == 'Не найдена организация по переданному group_id':
        answer = await message.reply(token)
        await delete_message(answer, sleep_timer)
    else:
        try:
            answer = await message.reply(f'*Баланс:*\n'
                                f'Начальный баланс: _{int(balance["distr"]["amount"]) + int(balance["distr"]["sent"])}_\n'
                                f'Отправлено: _{int(balance["distr"]["sent"])}_\n'
                                f'Получено: _{int(balance["income"]["amount"])}_\n'
                                f'Доступно для распределения: _{int(balance["distr"]["amount"])}_\n'
                                f'Сгорят: _{int(balance["distr"]["amount"]) + int(balance["distr"]["sent"]) - int(balance["distr"]["sent"])}_',
                                parse_mode="Markdown")
            await delete_message(answer, sleep_timer)
        except KeyError:
            answer = await message.reply("Что то пошло не так")
            await delete_message(answer, sleep_timer)


# @dp.message_handler(commands=['ct'])
async def ct(message: types.Message):
    '''
    Выводит инлайн клавиатуру с не проведенными транзакциями
    '''
    try:
        answer = await bot.send_message(
            message.from_user.id, 'Для отмены транзакции выберите соответствующую транзакции кнопку',
            reply_markup=not_complited_transactions)
        await delete_message(answer, sleep_timer)
    except:
        answer = await message.reply(dicts.errors['no_chat_with_bot'])
        await delete_message(answer, sleep_timer)


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
        answer = await bot.send_message(
            message.from_user.id,
            'Укажите вашу организацию:',
            reply_markup=get_user_organization_keyboard(telegram_id=message.from_user.id)
        )
        await delete_message(answer, sleep_timer)
    except aiogram.utils.exceptions.CantInitiateConversation:
        answer = await message.reply(dicts.errors['no_chat_with_bot'])
        await delete_message(answer, sleep_timer)


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
    try:
        if telegram_id != group_id:
            response = export_file_transactions_by_group_id(telegram_id=telegram_id, group_id=group_id)
            try:
                r = response['message']
                answer = await message.reply(r)
                await delete_message(answer, sleep_timer)
            except TypeError or KeyError:
                with open(f'{filename}.xlsx', 'wb') as file:
                    file.write(response)
                answer = await message.reply('Отчет отправлен в ЛС')
                await bot.send_document(document=open(f'{filename}.xlsx', 'rb'),
                                        chat_id=message.from_user.id
                                        )
                os.remove(f'{filename}.xlsx')
                await delete_message(answer, sleep_timer)

        else:
            organization_id = find_active_organization(tg_id=telegram_id)
            response = export_file_transactions_by_organization_id(telegram_id=telegram_id, organization_id=organization_id)
            try:
                r = response['message']
                answer = await message.reply(r)
                await delete_message(answer, sleep_timer)
            except TypeError or KeyError:
                with open(f'{filename}.xlsx', 'wb') as file:
                    file.write(response)
                await bot.send_document(document=open(f'{filename}.xlsx', 'rb'),
                                        chat_id=message.from_user.id
                                        )
                os.remove(f'{filename}.xlsx')
    except aiogram.utils.exceptions.CantInitiateConversation:
        answer = await message.reply(dicts.errors['no_chat_with_bot'])
        await delete_message(answer, sleep_timer)


# @dp.message_handler(commands=['webwiev'])
async def webwiev(message: types.Message):
    try:
        answer = await bot.send_message(chat_id=message.from_user.id, text='Для перехода в приложение нажимай:',
                               reply_markup=start_web_app)
        await delete_message(answer, sleep_timer)
    except aiogram.utils.exceptions.CantInitiateConversation:
        answer = await message.reply(dicts.errors['no_chat_with_bot'])
        await delete_message(answer, sleep_timer)


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(balance, commands=['баланс', 'balance'])
    dp.register_message_handler(ct, commands=['ct'])
    dp.register_message_handler(go, commands=['go'])
    dp.register_message_handler(export, commands=['export'])
    dp.register_message_handler(webwiev, commands=['webwiev'])
    dp.register_message_handler(test, commands=['test'])