import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))  # todo наверняка импорт можно сделать проще
from keyboards.inline_not_complited_transactions import get_not_complited_transactions_kb
from keyboards.inline_user_organizations import get_user_organization_keyboard
from keyboards.inline_webapp_test import start_web_app

from aiogram import types, Dispatcher
from create_bot import dp, bot, logger
from API.api_requests import get_token, get_balance, get_token_by_organization_id, \
    export_file_transactions_by_group_id, export_file_transactions_by_organization_id, get_all_cancelable_likes, \
    all_like_tags, get_active_organization, messages_lifetime, tg_handle_start, get_ratings, get_rating_xls

from dict_cloud import dicts

import datetime

import asyncio
from contextlib import suppress
from aiogram.utils.exceptions import MessageCantBeDeleted, \
    MessageToDeleteNotFound, CantInitiateConversation

from dict_cloud.dicts import messages, errors


async def delete_message_bot_answer(answer, group_id):
    """
    Удаляет только одно сообщение от бота, в соответствии с настройками сервера
    """
    lifetime_dict = messages_lifetime(group_id)
    if lifetime_dict is None:
        lifetime_dict = {'bot_messages_lifetime': 10, 'bot_commands_lifetime': 3}
    if lifetime_dict["bot_messages_lifetime"] != 0:
        await asyncio.sleep(lifetime_dict["bot_messages_lifetime"])
        with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
            await answer.delete()
    else:
        return


async def delete_message_and_command(message: list[types.Message], group_id: str = None):
    """
    Вычисляет время жизни сообщений относительно настроек группы и удаляет их
    В message передается список ["команда", "ответ"]
    """
    lifetime_dict = messages_lifetime(group_id)

    if lifetime_dict is None:
        lifetime_dict = {'bot_messages_lifetime': 5, 'bot_commands_lifetime': 0}

    if lifetime_dict['bot_messages_lifetime'] == 0 and lifetime_dict['bot_commands_lifetime'] != 0:
        await asyncio.sleep(lifetime_dict["bot_commands_lifetime"])
        with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
            await message[0].delete()
        return
    elif lifetime_dict['bot_commands_lifetime'] == 0 and lifetime_dict['bot_messages_lifetime'] != 0:
        await asyncio.sleep(lifetime_dict["bot_messages_lifetime"])
        with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
            await message[1].delete()
        return
    elif lifetime_dict['bot_messages_lifetime'] == 0 and lifetime_dict['bot_commands_lifetime'] == 0:
        return

    if lifetime_dict["bot_messages_lifetime"] > lifetime_dict["bot_commands_lifetime"]:
        await asyncio.sleep(lifetime_dict["bot_commands_lifetime"])
        with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
            await message[0].delete()
        sleep_rest = lifetime_dict["bot_messages_lifetime"] - lifetime_dict["bot_commands_lifetime"]
        await asyncio.sleep(sleep_rest)
        with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
            await message[1].delete()
    if lifetime_dict["bot_messages_lifetime"] < lifetime_dict["bot_commands_lifetime"]:
        await asyncio.sleep(lifetime_dict["bot_messages_lifetime"])
        with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
            await message[1].delete()
        sleep_rest = lifetime_dict["bot_commands_lifetime"] - lifetime_dict["bot_messages_lifetime"]
        await asyncio.sleep(sleep_rest)
        with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
            await message[0].delete()
    else:
        await asyncio.sleep(lifetime_dict["bot_commands_lifetime"])
        with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
            for i in message:
                await i.delete()


@dp.message_handler(commands="r")
async def ready(message: types.Message):
    temp = message.from_user
    print(temp)


# @dp.message_handler(commands="start")
async def start(message: types.Message):
    tg_name = message.from_user.username.replace("@", "")
    tg_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    if message.chat.type == types.ChatType.GROUP:
        chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        group_id = message.chat.id
        user_role = chat_member.status
        group_name = message.chat.title
        resp = tg_handle_start(tg_name, tg_id, group_id, user_role, group_name, first_name, last_name)
    else:
        resp = tg_handle_start(tg_name, tg_id, first_name=first_name, last_name=last_name)
    if resp:
        resp_status = resp["status"]
        if resp_status == 0:
            text = f"Hello, {message.from_user.first_name}! Use /go to select Organization"
        elif resp_status == 2:
            text = f"Hello, {message.from_user.first_name}!\n" \
                   "You have to register in community to continue.\n" \
                   f"Please, use your invite link, or create your own community on tf360.com " \
                   f"(use <code>{message.from_user.username}</code> as login)"
        elif resp_status == -1:
            text = f"Hello, {message.from_user.first_name}! Your account blocked, please contact support."
        elif resp_status == 1:
            text = f"Hello, {message.from_user.first_name}! Your code is: <code>{resp['verification_code']}</code>"
        else:
            text = resp_status
        try:
            await bot.send_message(chat_id=message.from_user.id, text=text, parse_mode=types.ParseMode.HTML)
        except CantInitiateConversation:
            await message.answer("Начните чат с ботом чтобы я смог отправить ваш код вам в ЛС")

    else:
        await message.answer("Ошибка ответа от сервера, обратитесь к администратору")
    await message.delete()


# @dp.message_handler(commands=['help'])
async def help_message(message: types.Message):
    if message.chat.id == message.from_user.id:
        await bot.send_message(message.chat.id, messages['start_message'].format(user_name=message.from_user.username))
    else:
        try:
            await bot.send_message(
                message.from_user.id,
                messages['start_message'].format(user_name=message.from_user.username)
            )
            answer = await message.reply('Ответил в личку 😉')
            await delete_message_and_command([message, answer], message.chat.id)
        except CantInitiateConversation:
            answer = await message.reply(dicts.errors['no_chat_with_bot'])
            await delete_message_and_command([message, answer], message.chat.id)


# @dp.message_handler(commands=['test'])
async def test(message: types.Message):
    if message.chat.id == message.from_user.id:
        answer = await message.answer('Бот работает. Это сообщение будет удалено через 5 секунд')
        await delete_message_and_command([message, answer])
    else:
        answer = await message.answer('Бот работает. Это сообщение будет удалено через 5 секунд\n'
                                      f'Group_id: <code>{message.chat.id}</code>', parse_mode=types.ParseMode.HTML)
        await delete_message_and_command([message, answer], message.chat.id)


# @dp.message_handler(commands=['баланс', 'balance'])
async def balance(message: types.Message):
    """
    Выводит в текущий чат количество спасибок у пользователя
    Если бот общается в ЛС, то выводит баланс по активной организации
    """
    telegram_id = message.from_user.id
    telegram_name = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    if message.chat.type == types.ChatType.GROUP:
        group_id = message.chat.id
        token = get_token(telegram_id, group_id, telegram_name, first_name, last_name)
        if not token:
            answer = await message.answer(errors["no_organization_by_id"].format(organization_id=message.chat.id),
                                          parse_mode=types.ParseMode.HTML)
            await delete_message_and_command([message, answer], message.chat.id)
            return
    else:
        organization_id = get_active_organization(telegram_id)
        if not organization_id:
            answer = await message.answer(errors["no_active_organization"].format(organization_id=message.chat.id),
                                          parse_mode=types.ParseMode.HTML)
            await delete_message_and_command([message, answer], message.chat.id)
            return
        if organization_id is not None:
            token = get_token_by_organization_id(telegram_id, organization_id, telegram_name, first_name, last_name)
        else:
            answer = await message.reply(dicts.errors['no_active_organization'])
            asyncio.create_task(delete_message_and_command([message, answer], message.chat.id))
            return

    balance = get_balance(token)
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
        if message.chat.type == types.ChatType.GROUP:
            await delete_message_and_command([message, answer], message.chat.id)
    except KeyError:
        answer = await message.reply("Что то пошло не так")
        await delete_message_and_command([message, answer], message.chat.id)


# @dp.message_handler(commands=['ct'])
async def ct(message: types.Message):
    """
    Выводит инлайн клавиатуру с не проведенными транзакциями
    """
    telegram_id = message.from_user.id
    group_id = message.chat.id
    telegram_name = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    if telegram_id == group_id:
        organization_id = get_active_organization(telegram_id)
        token = get_token_by_organization_id(telegram_id, organization_id, telegram_name, first_name, last_name)
    else:
        token = get_token(telegram_id, group_id, telegram_name, first_name, last_name)

    list_of_cancelable_likes = get_all_cancelable_likes(user_token=token)
    not_complited_transactions = get_not_complited_transactions_kb(list_of_canceleble_likes=list_of_cancelable_likes)

    if len(list_of_cancelable_likes) == 0:
        try:
            answer = await bot.send_message(message.from_user.id, dicts.errors['no_likes_to_cancel'])
            await delete_message_and_command([message, answer], message.chat.id)
        except CantInitiateConversation:
            answer = await message.reply(dicts.errors['no_chat_with_bot'])
            await delete_message_and_command([message, answer], message.chat.id)
    else:
        try:
            answer = await bot.send_message(
                message.from_user.id, 'Для отмены транзакции выберите соответствующую транзакции кнопку',
                reply_markup=not_complited_transactions)
            await delete_message_and_command([message, answer], message.chat.id)
        except CantInitiateConversation:
            answer = await message.reply(dicts.errors['no_chat_with_bot'])
            await delete_message_and_command([message, answer], message.chat.id)


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
        if message.chat.type == types.ChatType.GROUP:
            await delete_message_and_command([message, answer], message.chat.id)
    except CantInitiateConversation:
        answer = await message.reply(dicts.errors['no_chat_with_bot'])
        await delete_message_and_command([message, answer], message.chat.id)


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
                await delete_message_and_command([message, answer], message.chat.id)
            except TypeError or KeyError:
                with open(f'{filename}.xlsx', 'wb') as file:
                    file.write(response)
                answer = await message.reply('Отчет отправлен в ЛС')
                await bot.send_document(document=open(f'{filename}.xlsx', 'rb'),
                                        chat_id=message.from_user.id
                                        )
                os.remove(f'{filename}.xlsx')
                await delete_message_and_command([message, answer], message.chat.id)

        else:
            organization_id = get_active_organization(telegram_id)
            response = export_file_transactions_by_organization_id(telegram_id=telegram_id,
                                                                   organization_id=organization_id)
            try:
                r = response['message']
                answer = await message.reply(r)
                await delete_message_and_command([message, answer], message.chat.id)
            except TypeError or KeyError:
                with open(f'{filename}.xlsx', 'wb') as file:
                    file.write(response)
                answer = await bot.send_document(document=open(f'{filename}.xlsx', 'rb'),
                                                 chat_id=message.from_user.id
                                                 )
                os.remove(f'{filename}.xlsx')
                await delete_message_and_command([message, answer], message.chat.id)
    except CantInitiateConversation:
        answer = await message.reply(dicts.errors['no_chat_with_bot'])
        await delete_message_and_command([message, answer], message.chat.id)


# @dp.message_handler(commands=['webwiev'])
async def webwiev(message: types.Message):
    try:
        answer = await bot.send_message(chat_id=message.from_user.id, text='Для перехода в приложение нажимай:',
                                        reply_markup=start_web_app)
        await delete_message_and_command([message, answer], message.chat.id)
    except CantInitiateConversation:
        answer = await message.reply(dicts.errors['no_chat_with_bot'])
        await delete_message_and_command([message, answer], message.chat.id)


# @dp.message_handler(commands=['tags'])
async def tags(message: types.Message):
    telegram_id = message.from_user.id
    group_id = message.chat.id
    telegram_name = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    if telegram_id == group_id:
        organization_id = get_active_organization(telegram_id)
        if organization_id is not None:
            token = get_token_by_organization_id(telegram_id, organization_id, telegram_name, first_name, last_name)
        else:
            answer = await message.reply(dicts.errors['no_active_organization'])
            await delete_message_and_command([message, answer], message.chat.id)
            return
    else:
        token = get_token(telegram_id, group_id, telegram_name, first_name, last_name)

    tag_list = 'Вот список основных тэгов:\n'
    for i in all_like_tags(user_token=token):
        tag_list += f'{i["id"]} - {i["name"]}\n'

    answer = await message.reply(tag_list)
    await delete_message_and_command([message, answer], message.chat.id)


# @dp.message_handler(commands='rating')
async def rating(message: types.Message):
    statistics_list = None
    user_rating = None
    if message.chat.type == types.ChatType.GROUP:
        limit = 5
        user_token = get_token(telegram_id=message.from_user.id,
                               group_id=message.chat.id,
                               telegram_name=message.from_user.username,
                               first_name=message.from_user.first_name,
                               last_name=message.from_user.last_name)
        statistics_list = get_ratings(user_token)
    elif message.chat.type == types.ChatType.PRIVATE:
        limit = 500
        active_organization_id = get_active_organization(message.from_user.id)
        if not active_organization_id:
            await message.answer("У вас не выбрано ни одной организации.\n"
                                 "Используйте /go чтобы выбрать организацию")
            return
        user_token = get_token_by_organization_id(telegram_id=message.from_user.id,
                                                  organization_id=active_organization_id,
                                                  telegram_name=message.from_user.username,
                                                  first_name=message.from_user.first_name,
                                                  last_name=message.from_user.last_name)
        statistics_list = get_ratings(user_token)
    if statistics_list:
        for i in statistics_list:
            if i['user']['tg_name'] == message.from_user.username:
                user_rating = i['rating']
        if user_rating:
            text = f'<u><b>Твой рейтинг:</b> <code>{user_rating}</code></u>\n\n' \
                   '<b>Статистика по ТОП пользователям:</b>\n\n'
        else:
            text = '<b>Статистика по ТОП пользователям:</b>\n\n'
        for i in statistics_list[:limit]:
            text += f"Пользователь: <code>{i['user']['tg_name']}</code>\n" \
                    f"Рейтинг: <code>{i['rating']}</code>\n\n"
        answer = await message.answer(text, parse_mode=types.ParseMode.HTML)
    else:
        answer = await message.answer("Ошибка ответа от сервера")
    if message.chat.type == types.ChatType.GROUP:
        await delete_message_and_command([message, answer], message.chat.id)


# @dp.message_handler(commands='ratingxls')
async def ratingxls(message: types.Message):
    user_token = None
    filename = f"{message.from_user.id}_{datetime.datetime.now().strftime('%d_%m_%y_%H_%M')}.xlsx"
    if message.chat.type == types.ChatType.GROUP:
        user_token = get_token(telegram_id=message.from_user.id,
                               group_id=message.chat.id,
                               telegram_name=message.from_user.username,
                               first_name=message.from_user.first_name,
                               last_name=message.from_user.last_name)
    elif message.chat.type == types.ChatType.PRIVATE:
        active_organization_id = get_active_organization(message.from_user.id)
        if not active_organization_id:
            await message.answer("У вас не выбрано ни одной организации.\n"
                                 "Используйте /go чтобы выбрать организацию")
            return
        user_token = get_token_by_organization_id(telegram_id=message.from_user.id,
                                                  organization_id=active_organization_id,
                                                  telegram_name=message.from_user.username,
                                                  first_name=message.from_user.first_name,
                                                  last_name=message.from_user.last_name)
    temp_answer = await bot.send_message(chat_id=message.from_user.id, text="Формирую фаил")
    content = get_rating_xls(user_token)
    if content:
        with open(filename, "wb") as file:
            file.write(content)
        try:
            await bot.send_document(chat_id=message.from_user.id, document=open(filename, "rb"))
            await temp_answer.delete()
        except CantInitiateConversation:
            await message.answer("Чтобы получить фаил начни со мной диалог")
            await asyncio.sleep(5)
            await message.delete()
        os.remove(filename)
    else:
        error_message = await temp_answer.edit_text("Ошибка при обработке запроса")
        await asyncio.sleep(5)
        await error_message.delete()


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(start, commands=['start'])
    dp.register_message_handler(balance, commands=['баланс', 'balance'])
    dp.register_message_handler(ct, commands=['ct'])
    dp.register_message_handler(go, commands=['go'])
    dp.register_message_handler(export, commands=['export'])
    dp.register_message_handler(webwiev, commands=['webwiev'])
    dp.register_message_handler(test, commands=['test'])
    dp.register_message_handler(help_message, commands=['help'])
    dp.register_message_handler(tags, commands=['tags'])
    dp.register_message_handler(rating, commands=['rating'])
    dp.register_message_handler(ratingxls, commands=['ratingxls'])
