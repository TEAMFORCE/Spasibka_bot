import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))  # todo наверняка импорт можно сделать проще
from keyboards.inline_not_complited_transactions import get_not_complited_transactions_kb
from keyboards.inline_user_organizations import get_user_organization_keyboard
from keyboards.inline_webapp_test import start_web_app

from aiogram import types, Dispatcher
from create_bot import dp, bot
from API.api_requests import get_token, get_balance, get_token_by_organization_id, \
    export_file_transactions_by_group_id, export_file_transactions_by_organization_id, get_all_cancelable_likes, \
    all_like_tags, get_active_organization

from dict_cloud import dicts

import datetime

import asyncio
from contextlib import suppress
from aiogram.utils.exceptions import MessageCantBeDeleted, \
    MessageToDeleteNotFound, CantInitiateConversation

from dict_cloud.dicts import sleep_timer, messages


async def delete_message(message: types.Message, sleep_time: int = 0):
    """
    Удаляет сообщение по истечению таймера sleep_time
    """
    await asyncio.sleep(sleep_time)
    with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
        await message.delete()


# @dp.message_handler(commands=['start', 'help'])
async def start(message: types.Message):
    if message.chat.id == message.from_user.id:
        await bot.send_message(message.chat.id, messages['start_message'].format(user_name=message.from_user.username))
    else:
        try:
            await bot.send_message(
                message.from_user.id,
                messages['start_message'].format(user_name=message.from_user.username)
            )
            answer = await message.reply('Ответил в личку 😉')
            await delete_message(answer, sleep_timer)
        except CantInitiateConversation:
            answer = await message.reply(dicts.errors['no_chat_with_bot'])
            await delete_message(answer, sleep_timer)


# @dp.message_handler(commands=['test'])
async def test(message: types.Message):
    msg = await message.reply('Это сообщение будет удалено через 5 секунд')
    asyncio.create_task(delete_message(msg, 5))


# @dp.message_handler(commands=['баланс', 'balance'])
async def balance(message: types.Message):
    """
    Выводит в текущий чат количество спасибок у пользователя
    Если бот общается в ЛС, то выводит баланс по активной организации
    """
    telegram_id = message.from_user.id
    telegram_name = message.from_user.username
    if message.chat.id != telegram_id:
        group_id = message.chat.id
        token = get_token(telegram_id, group_id, telegram_name)
    else:
        organization_id = get_active_organization(telegram_id)
        if organization_id is not None:
            token = get_token_by_organization_id(telegram_id, organization_id, telegram_name)
        else:
            answer = await message.reply(dicts.errors['no_active_organization'])
            asyncio.create_task(delete_message(answer, sleep_time=sleep_timer))
            return
    balance = get_balance(token)
    if balance == 'Что то пошло не так':
        answer = await message.reply(balance)
        await delete_message(answer, sleep_timer)
    elif balance == 'Не найдена организация по переданному group_id':
        answer = await message.reply(token)
        await delete_message(answer, sleep_timer)
    else:
        try:
            start_balance = int(balance["distr"]["amount"]) + int(balance["distr"]["sent"])
            sent = int(balance["distr"]["sent"])
            recived = int(balance["income"]["amount"])
            allowed = int(balance["distr"]["amount"]) + int(balance["income"]["amount"])
            remain = int(balance["distr"]["amount"]) + int(balance["distr"]["sent"]) - int(balance["distr"]["sent"])
            answer = await message.reply(f'*Баланс:*\n'
                                         f'Начальный баланс: _{start_balance}_\n'
                                         f'Отправлено: _{sent}_\n'
                                         f'Получено: _{recived}_\n'
                                         f'Доступно для распределения: _{allowed}_\n'
                                         f'Осталось раздать: _{remain}_',
                                         parse_mode="Markdown")
            await delete_message(answer, sleep_timer)
        except KeyError:
            answer = await message.reply("Что то пошло не так")
            await delete_message(answer, sleep_timer)


# @dp.message_handler(commands=['ct'])
async def ct(message: types.Message):
    """
    Выводит инлайн клавиатуру с не проведенными транзакциями
    """
    telegram_id = message.from_user.id
    group_id = message.chat.id
    telegram_name = message.from_user.username

    if telegram_id == group_id:
        organization_id = get_active_organization(telegram_id)
        token = get_token_by_organization_id(telegram_id, organization_id, telegram_name)
    else:
        token = get_token(telegram_id, group_id, telegram_name)

    list_of_cancelable_likes = get_all_cancelable_likes(user_token=token)
    not_complited_transactions = get_not_complited_transactions_kb(list_of_canceleble_likes=list_of_cancelable_likes)

    if len(list_of_cancelable_likes) == 0:
        try:
            answer = await bot.send_message(message.from_user.id, dicts.errors['no_likes_to_cancel'])
            await delete_message(answer, sleep_time=sleep_timer)
        except CantInitiateConversation:
            answer = await message.reply(dicts.errors['no_chat_with_bot'])
            await delete_message(answer, sleep_timer)
    else:
        try:
            answer = await bot.send_message(
                message.from_user.id, 'Для отмены транзакции выберите соответствующую транзакции кнопку',
                reply_markup=not_complited_transactions)
            await delete_message(answer, sleep_timer)
        except CantInitiateConversation:
            answer = await message.reply(dicts.errors['no_chat_with_bot'])
            await delete_message(answer, sleep_timer)


# @dp.message_handler(commands=['go'])
async def go(message: types.Message):
    """
    В личном общении выводит список доступных организаций в виде инлайн клавиатуры
    """
    try:
        answer = await bot.send_message(
            message.from_user.id,
            'Укажите вашу организацию:',
            reply_markup=get_user_organization_keyboard(telegram_id=message.from_user.id)
        )
        asyncio.create_task(delete_message(answer, sleep_timer))
    except CantInitiateConversation:
        answer = await message.reply(dicts.errors['no_chat_with_bot'])
        asyncio.create_task(delete_message(answer, sleep_timer))


# @dp.message_handler(commands=['export'])
async def export(message: types.Message):
    """
    Отправляет .xlxs фаил со списком транзакций, если общение в ЛС - то фаил формируется по активной группе
    """
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
            organization_id = get_active_organization(telegram_id)
            response = export_file_transactions_by_organization_id(telegram_id=telegram_id,
                                                                   organization_id=organization_id)
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
    except CantInitiateConversation:
        answer = await message.reply(dicts.errors['no_chat_with_bot'])
        await delete_message(answer, sleep_timer)


# @dp.message_handler(commands=['webwiev'])
async def webwiev(message: types.Message):
    try:
        answer = await bot.send_message(chat_id=message.from_user.id, text='Для перехода в приложение нажимай:',
                                        reply_markup=start_web_app)
        await delete_message(answer, sleep_timer)
    except CantInitiateConversation:
        answer = await message.reply(dicts.errors['no_chat_with_bot'])
        await delete_message(answer, sleep_timer)


# @dp.message_handler(commands=['tags'])
async def tags(message: types.Message):
    telegram_id = message.from_user.id
    group_id = message.chat.id
    telegram_name = message.from_user.username

    if telegram_id == group_id:
        organization_id = get_active_organization(telegram_id)
        if organization_id is not None:
            token = get_token_by_organization_id(telegram_id, organization_id, telegram_name)
        else:
            answer = await message.reply(dicts.errors['no_active_organization'])
            await delete_message(answer, sleep_time=sleep_timer)
            return
    else:
        token = get_token(telegram_id, group_id, telegram_name)

    tag_list = 'Вот список основных тэгов:\n'
    for i in all_like_tags(user_token=token):
        tag_list += f'{i["id"]} - {i["name"]}\n'

    answer = await message.reply(tag_list)
    await delete_message(answer, sleep_timer)


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(balance, commands=['баланс', 'balance'])
    dp.register_message_handler(ct, commands=['ct'])
    dp.register_message_handler(go, commands=['go'])
    dp.register_message_handler(export, commands=['export'])
    dp.register_message_handler(webwiev, commands=['webwiev'])
    dp.register_message_handler(test, commands=['test'])
    dp.register_message_handler(start, commands=['start', 'help'])
    dp.register_message_handler(tags, commands=['tags'])
