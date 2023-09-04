import os
import sys

from all_func.delete_messages_func import delete_message_and_command, delete_command, delete_message_bot_answer
from all_func.utils import create_scores_message, create_rating_message, send_balances_xls
from service.service_func import is_bot_admin

sys.path.insert(1, os.path.join(sys.path[0], '..'))  # todo наверняка импорт можно сделать проще
from keyboards.inline_not_complited_transactions import get_not_complited_transactions_kb
from keyboards.inline_user_organizations import get_user_organization_keyboard
from keyboards.inline_webapp_test import start_web_app

from aiogram import types, Dispatcher
from create_bot import dp, bot, logger
from API.api_requests import get_token, get_balance, get_token_by_organization_id, \
    export_file_transactions_by_group_id, export_file_transactions_by_organization_id, get_all_cancelable_likes, \
    all_like_tags, get_active_organization, tg_handle_start, get_ratings, get_rating_xls, get_user, \
    get_scores, get_scoresxlsx, get_balances, get_balances_from_group

from dict_cloud import dicts

import datetime

import asyncio
from aiogram.utils.exceptions import MessageCantBeDeleted, CantInitiateConversation, BotBlocked

from dict_cloud.dicts import messages, errors, start_messages, sleep_timer


@dp.message_handler(commands="log")
async def ready(message: types.Message):
    await is_bot_admin(message)
    logger.warning(f"User info: {message.from_user}")
    logger.warning(f"Group info: {message.chat}")
    try:
        await message.delete()
    except MessageCantBeDeleted:
        logger.warning(errors['cant_delete_message'])


# @dp.message_handler(commands="start")
async def start(message: types.Message):
    logger.warning(message)
    await is_bot_admin(message)
    tg_name = message.from_user.username.replace("@", "") if message.from_user.username else None
    tg_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    group_name = None
    group_id = None
    organization_id = None
    is_user_admin = False
    if message.chat.type != types.ChatType.PRIVATE:
        chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        group_id = message.chat.id
        user_role = chat_member.status
        group_name = message.chat.title
        if user_role in ["creator", "administrator"]:
            is_user_admin = True
    else:
        organization_id = get_active_organization(tg_id)

    resp = tg_handle_start(tg_name, tg_id, group_id, group_name, first_name, last_name, organization_id,
                           is_user_admin)
    if resp:
        logger.warning(resp)
        resp_status = resp["status"]
        logger.info(resp_status)
        text = resp['verbose']
    else:
        text = start_messages["no_respose_from_server"]
    try:
        await message.delete()
    except MessageCantBeDeleted:
        pass

    try:
        answer = await bot.send_message(message.from_user.id, text, parse_mode=types.ParseMode.HTML)
    except CantInitiateConversation:
        answer = await message.answer(errors['cant_initiate_chat'].format(
            username=message.from_user.get_mention(as_html=True)), parse_mode=types.ParseMode.HTML)
    except BotBlocked:
        answer = await message.answer(errors['you_blocked_me'].format(
            username=message.from_user.get_mention(as_html=True)), parse_mode=types.ParseMode.HTML)

    if message.chat.type != types.ChatType.PRIVATE:
        await asyncio.sleep(sleep_timer)
        await answer.delete()


# @dp.message_handler(commands=['help'])
async def help_message(message: types.Message):
    await is_bot_admin(message)
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
    await is_bot_admin(message)
    if message.chat.id == message.from_user.id:
        await message.delete()
        answer = await message.answer('Бот работает. Это сообщение будет удалено')
        await asyncio.sleep(sleep_timer)
        await answer.delete()
    else:
        answer = await message.answer('Бот работает. Это сообщение будет удалено\n'
                                      f'Group_id: <code>{message.chat.id}</code>', parse_mode=types.ParseMode.HTML)
        chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        logger.info(chat_member)
        await delete_message_and_command([message, answer], message.chat.id)


# @dp.message_handler(commands=['баланс', 'balance'])
async def balance(message: types.Message):
    """
    Выводит в текущий чат количество спасибок у пользователя
    Если бот общается в ЛС, то выводит баланс по активной организации
    """
    await is_bot_admin(message)
    telegram_id = message.from_user.id
    tg_name = message.from_user.username
    group_id = None
    organization_id = None
    if message.chat.id != message.from_user.id:
        group_id = message.chat.id
    else:
        organization_id = get_active_organization(telegram_id)
        if not organization_id:
            answer = await message.answer(errors["no_active_organization"].format(organization_id=message.chat.id),
                                          parse_mode=types.ParseMode.HTML)
            await delete_message_and_command([message, answer], message.chat.id)
            return
        if organization_id is None:
            answer = await message.reply(dicts.errors['no_active_organization'])
            asyncio.create_task(delete_message_and_command([message, answer], message.chat.id))
            return

    balance = get_balance(telegram_id, tg_name, group_id, organization_id)
    if not balance:
        await message.answer(errors["no_balance"])
        await asyncio.sleep(sleep_timer)
        await message.delete()
        return
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
        if message.chat.type != types.ChatType.PRIVATE:
            await delete_message_and_command([message, answer], message.chat.id)
    except KeyError:
        answer = await message.reply("Что то пошло не так")
        await delete_message_and_command([message, answer], message.chat.id)


# @dp.message_handler(commands='balances')
async def balances(message: types.Message):
    filename = f"{message.from_user.id}_{datetime.datetime.now().strftime('%d_%m_%y')}.xlsx"
    if message.chat.type == types.ChatType.PRIVATE:
        organization_id = get_active_organization(message.from_user.id)
        if not organization_id:
            await message.answer(errors['no_active_organization'])
            logger.warning(f'User {message.from_user.username} has no active organizations')
            return
        user_token = get_token_by_organization_id(telegram_id=message.from_user.id,
                                                  organization_id=organization_id,
                                                  telegram_name=message.from_user.username,
                                                  first_name=message.from_user.first_name,
                                                  last_name=message.from_user.last_name)
        if not user_token:
            error_message = await message.answer(errors['cant_find_token'])
            await asyncio.sleep(sleep_timer)
            await error_message.delete()
            return
        content = get_balances(user_token, organization_id)
        await send_balances_xls(content, filename, message)
    else:
        user = get_user(telegram_id=message.from_user.id,
                        group_id=message.chat.id,
                        telegram_name=message.from_user.username,
                        first_name=message.from_user.first_name,
                        last_name=message.from_user.last_name)
        if not user:
            error_message = await message.answer(errors['cant_find_token'])
            await asyncio.sleep(sleep_timer)
            await error_message.delete()
            return
        chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        user_role = chat_member.status
        if user_role in ["creator", "administrator"]:
            content = get_balances_from_group(user["token"], message.chat.id)
            await send_balances_xls(content, filename, message)
    await delete_command(message, message.chat.id)


# @dp.message_handler(commands=['ct'])
async def ct(message: types.Message):
    """
    Выводит инлайн клавиатуру с не проведенными транзакциями
    """
    await is_bot_admin(message)
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
            await bot.send_message(message.from_user.id, dicts.errors['no_likes_to_cancel'])
        except CantInitiateConversation:
            answer = await message.reply(dicts.errors['no_chat_with_bot'])
            await delete_message_and_command([message, answer], message.chat.id)
    else:
        try:
            await bot.send_message(
                message.from_user.id, 'Для отмены транзакции выберите соответствующую транзакции кнопку',
                reply_markup=not_complited_transactions)
        except CantInitiateConversation:
            answer = await message.reply(dicts.errors['no_chat_with_bot'])
            await delete_message_and_command([message, answer], message.chat.id)


# @dp.message_handler(commands=['go'])
async def go(message: types.Message):
    """
    В личном общении выводит список доступных организаций в виде инлайн клавиатуры
    """
    await is_bot_admin(message)
    try:
        answer = await bot.send_message(
            message.from_user.id,
            'Укажите вашу организацию:',
            reply_markup=get_user_organization_keyboard(telegram_id=message.from_user.id,
                                                        tg_name=message.from_user.username,
                                                        first_name=message.from_user.first_name,
                                                        last_name=message.from_user.last_name)
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
    await is_bot_admin(message)
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
                await bot.send_document(document=open(f'{filename}.xlsx', 'rb'),
                                        chat_id=message.from_user.id
                                        )
                os.remove(f'{filename}.xlsx')
    except CantInitiateConversation:
        answer = await message.reply(dicts.errors['no_chat_with_bot'])
        await delete_message_and_command([message, answer], message.chat.id)


# @dp.message_handler(commands=['webwiev'])
async def webwiev(message: types.Message):
    await is_bot_admin(message)
    try:
        answer = await bot.send_message(chat_id=message.from_user.id, text='Для перехода в приложение нажимай:',
                                        reply_markup=start_web_app)
        await delete_message_and_command([message, answer], message.chat.id)
    except CantInitiateConversation:
        answer = await message.reply(dicts.errors['no_chat_with_bot'])
        await delete_message_and_command([message, answer], message.chat.id)


# @dp.message_handler(commands=['tags'])
async def tags(message: types.Message):
    await is_bot_admin(message)
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
        tag_list += f'{i["id"]} - {i["name"].replace(" ", "_")}\n'

    answer = await message.reply(tag_list)
    if message.chat.type != types.ChatType.PRIVATE:
        await delete_message_and_command([message, answer], message.chat.id)


# @dp.message_handler(commands='rating')
async def rating(message: types.Message):
    await is_bot_admin(message)
    limit = 5
    if message.chat.type != types.ChatType.PRIVATE:
        user = get_user(telegram_id=message.from_user.id,
                        group_id=message.chat.id,
                        telegram_name=message.from_user.username,
                        first_name=message.from_user.first_name,
                        last_name=message.from_user.last_name)
    else:
        limit = 500
        active_organization_id = get_active_organization(message.from_user.id)
        if not active_organization_id:
            await message.answer(errors["no_active_organization"])
            return
        user = get_user(telegram_id=message.from_user.id,
                        organization_id=active_organization_id,
                        telegram_name=message.from_user.username,
                        first_name=message.from_user.first_name,
                        last_name=message.from_user.last_name)
    if not user:
        error = await message.answer(errors["no_token"])
        await asyncio.sleep(sleep_timer)
        await error.delete()
        return
    statistics_list = get_ratings(user["token"])
    if statistics_list:
        text = create_rating_message(statistics_list, user["user_id"], limit)
        answer = await message.answer(text, parse_mode=types.ParseMode.HTML)
    else:
        error = await message.answer(errors["server_error"])
        await asyncio.sleep(sleep_timer)
        await error.delete()
        return
    if message.chat.type != types.ChatType.PRIVATE:
        await delete_message_and_command([message, answer], message.chat.id)


# @dp.message_handler(commands='ratingxls')
async def ratingxls(message: types.Message):
    await is_bot_admin(message)
    user_token = None
    filename = f"{message.from_user.id}_{datetime.datetime.now().strftime('%d_%m_%y')}.xlsx"
    if message.chat.type == types.ChatType.GROUP:
        user_token = get_token(telegram_id=message.from_user.id,
                               group_id=message.chat.id,
                               telegram_name=message.from_user.username,
                               first_name=message.from_user.first_name,
                               last_name=message.from_user.last_name)
    elif message.chat.type == types.ChatType.PRIVATE:
        active_organization_id = get_active_organization(message.from_user.id)
        if not active_organization_id:
            await message.answer(errors["no_active_organization"])
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
            await message.answer(errors["no_chat_with_bot"])
            await asyncio.sleep(sleep_timer)
            await message.delete()
        os.remove(filename)
    else:
        error_message = await temp_answer.edit_text(errors["server_error"])
        await asyncio.sleep(sleep_timer)
        await error_message.delete()


# @dp.message_handler(commands='scores')
async def scores(message: types.Message):
    await is_bot_admin(message)
    user_tg_id = message.from_user.id
    user_tg_name = message.from_user.username
    user_first_name = message.from_user.first_name
    user_last_name = message.from_user.last_name
    group_id = None
    active_organization_id = None
    index = 20
    if message.chat.type != types.ChatType.PRIVATE:
        group_id = message.chat.id
        user_token = get_token(user_tg_id, group_id, user_tg_name, user_first_name, user_last_name)
        index = 5
    else:
        active_organization_id = get_active_organization(message.from_user.id)
        user_token = get_token_by_organization_id(user_tg_id, active_organization_id, user_tg_name, user_first_name,
                                                  user_last_name)
    likes_list = get_scores(user_token)
    if likes_list:
        user = get_user(user_tg_id, group_id, active_organization_id, user_tg_name, user_first_name, user_last_name)
        text = create_scores_message(likes_list['likes'], user['user_id'], index)
    else:
        text = errors['server_error']
    answer = await message.answer(text, parse_mode=types.ParseMode.HTML)
    if message.chat.type != types.ChatType.PRIVATE:
        await delete_message_bot_answer(answer, group_id)


# @dp.message_handler(commands='scoresxlsx')
async def scoresxlsx(message: types.Message):
    await is_bot_admin(message)
    user_tg_id = message.from_user.id
    user_tg_name = message.from_user.username
    user_first_name = message.from_user.first_name
    user_last_name = message.from_user.last_name
    group_id = None
    active_organization_id = None
    filename = f"{message.from_user.id}_{datetime.datetime.now().strftime('%d_%m_%y')}.xlsx"
    if message.chat.type != types.ChatType.PRIVATE:
        group_id = message.chat.id
    else:
        active_organization_id = get_active_organization(user_tg_id)
    user = get_user(user_tg_id, group_id, active_organization_id, user_tg_name, user_first_name, user_last_name)
    content = get_scoresxlsx(user['token'])
    temp_answer = await bot.send_message(chat_id=message.from_user.id, text="Формирую фаил")
    if content:
        with open(filename, "wb") as file:
            file.write(content)
        try:
            await bot.send_document(chat_id=message.from_user.id, document=open(filename, "rb"))
            await temp_answer.delete()
        except CantInitiateConversation:
            await message.answer(errors["no_chat_with_bot"])
            await asyncio.sleep(sleep_timer)
            await message.delete()
        os.remove(filename)


# @dp.message_handler(commands='consent')
async def consent(message: types.Message):
    await is_bot_admin(message)
    await message.delete()
    if message.chat.type == types.ChatType.PRIVATE:
        text = messages['consent']
        await message.answer(text)
        with open('files/agreement.pdf', 'rb') as file:
            input_agree_file = types.InputFile(file)
            await bot.send_document(message.chat.id, input_agree_file)
        with open('files/privacy_policy.pdf', 'rb') as file:
            input_policy_file = types.InputFile(file)
            await bot.send_document(message.chat.id, input_policy_file)
    else:
        try:
            sender_id = message.from_user.id
            text = messages['consent']
            await bot.send_message(sender_id, text)
            with open('files/agreement.pdf', 'rb') as file:
                input_agree_file = types.InputFile(file)
                await bot.send_document(sender_id, input_agree_file)
            with open('files/privacy_policy.pdf', 'rb') as file:
                input_policy_file = types.InputFile(file)
                await bot.send_document(sender_id, input_policy_file)
        except CantInitiateConversation:
            await message.answer(errors['no_chat_with_bot'])


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(scores, commands='scores')
    dp.register_message_handler(scoresxlsx, commands='scoresxlsx')
    dp.register_message_handler(start, commands=['start'])
    dp.register_message_handler(balance, commands=['баланс', 'balance'])
    dp.register_message_handler(balances, commands='balances')
    dp.register_message_handler(ct, commands=['ct'])
    dp.register_message_handler(go, commands=['go'])
    dp.register_message_handler(export, commands=['export'])
    dp.register_message_handler(webwiev, commands=['webwiev'])
    dp.register_message_handler(test, commands=['test'])
    dp.register_message_handler(help_message, commands=['help'])
    dp.register_message_handler(tags, commands=['tags'])
    dp.register_message_handler(rating, commands=['rating'])
    dp.register_message_handler(ratingxls, commands=['ratingxls'])
    dp.register_message_handler(consent, commands=['consent'])
