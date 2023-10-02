import asyncio
import os
import re

from typing import Optional

from aiogram import types
from aiogram.utils.exceptions import CantInitiateConversation

from API.api_requests import get_token, get_active_organization, get_token_by_organization_id, send_like
from create_bot import bot
from dict_cloud.dicts import errors, sleep_timer
from all_func.delete_messages_func import delete_message_bot_answer
from service.misc import find_tag_id


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Start dialogue"),
        types.BotCommand("balance", "Show balance"),
        types.BotCommand("tags", "Show awailables tags"),
        types.BotCommand("ct", "Cancel transaction"),
        types.BotCommand("go", "Change organization"),
        types.BotCommand("export", "Export account like"),
        types.BotCommand("rating", "List rating in organization"),
        types.BotCommand("scores", "List of incoming likes"),
        types.BotCommand("consent", "Data processing agreement"),
    ])


def create_rating_message(statistics_list: list, user_id: int, amount_of_strings: int) -> str:
    """
    Creates a text message for rating function.
    """
    user_rating = None
    text_end = []
    for i in statistics_list:
        string_part = get_name_surname_tgname_string(i['user']['name'],
                                                     i['user']['surname'],
                                                     i['user']['tg_name'].replace('<', '').replace('>', ''))
        if i['user']['userId'] == user_id:
            user_rating = i['rating']
        text_end.append(f"Пользователь: <code>{string_part}</code>\n"
                        f"Рейтинг: <code>{i['rating']}</code>\n\n")
    text = f'<u><b>Твой рейтинг:</b></u> <code>{user_rating}</code>\n\n' \
           '<b>Статистика по ТОП пользователям:</b>\n\n' + "".join(text_end[:amount_of_strings])
    return text


def create_scores_message(likes_list: list, user_id: int, amount_of_strings: int) -> str:
    """
    Creates a text message for scores function.
    """
    text = ''
    start_text = ''
    sorted_likes_list = sorted(likes_list, key=lambda x: x['income_likes'], reverse=True)
    for i in sorted_likes_list:
        if i['user']['userId'] == user_id:
            start_text = f"<b><u>Вами получено:</u></b> <code>{i['income_likes']}</code>\n\n" \
                         f"<b>Статистика по пользователям:</b>\n\n"
    for i in sorted_likes_list[:amount_of_strings]:
        if i['user']['tg_name']:
            string_part = get_name_surname_tgname_string(i['user']['name'],
                                                         i['user']['surname'],
                                                         i['user']['tg_name'].replace('<', '').replace('>', ''))
            text += f"Пользователь: <code>{string_part}</code>\n" \
                    f"Получено: <code>{i['income_likes']}</code>\n\n"
    return start_text + text


def get_name_surname_tgname_string(name: str = None, surname: str = None, tgname: str = None) -> str:
    """
    Build a string from name surname and tgname for bot messages.
    """
    string_parts = []
    if name not in ('', None):
        string_parts.append(name)
    if surname not in ('', None):
        string_parts.append(surname)
    if tgname not in ('', None):
        string_parts.append(tgname)
    return ' '.join(string_parts)


async def send_balances_xls(content: Optional[bytes], filename: str, message: types.Message) -> None:
    """
    Sending balances xls and removes file.
    """
    if content:
        with open(filename, "wb") as file:
            file.write(content)
        try:
            await bot.send_document(chat_id=message.from_user.id, document=open(filename, "rb"))
        except CantInitiateConversation:
            await message.answer(errors["no_chat_with_bot"])
            await asyncio.sleep(sleep_timer)
            await message.delete()
        os.remove(filename)
    else:
        error_message = await message.answer(errors["no_permitions"])
        await asyncio.sleep(sleep_timer)
        await error_message.delete()


async def get_reason(pattern_reason: re) -> str:
    """
    Get str reason from user message.
    """
    if len(pattern_reason.group(2)) > 0:
        return pattern_reason.group(2).capitalize()
    else:
        return "Отправлено через telegram"


async def send_like_in_group(amount: int, message: types.Message, pattern_tag: re, pattern_username: re) -> dict:
    """
    Create a dict with values to send api req. For public chat only.
    """
    result = {}
    if amount:
        group_id = str(message.chat.id)
        result.setdefault('group_id', group_id)
        token = get_token(telegram_id=message.from_user.id, group_id=group_id,
                          telegram_name=message.from_user.username, first_name=message.from_user.first_name,
                          last_name=message.from_user.last_name)
        result.setdefault('token', token)
        if not token:
            await message.answer(errors["no_token"])
            return
        if message.reply_to_message:
            recipient_telegram_id = str(message.reply_to_message.from_user.id)
            result.setdefault('recipient_telegram_id', recipient_telegram_id)

            recipient_telegram_name = message.reply_to_message.from_user.username
            result.setdefault('recipient_telegram_name', recipient_telegram_name)

            recipient_name = message.reply_to_message.from_user.first_name
            result.setdefault('recipient_name', recipient_name)

            recipient_last_name = message.reply_to_message.from_user.last_name
            result.setdefault('recipient_last_name', recipient_last_name)

            if pattern_tag:
                tag_id = find_tag_id(pattern_tag, token)
                result.setdefault('tag_id', tag_id)

        elif pattern_username:
            recipient_telegram_name = pattern_username.group(1)
            result.setdefault('recipient_telegram_name', recipient_telegram_name)
            if pattern_tag:
                tag_id = find_tag_id(pattern_tag, token)
                result.setdefault('tag_id', tag_id)

        return result


async def send_like_in_private_msg(pattern_username: re, message: types.Message, pattern_tag: re) -> dict:
    """
    Create a dict with values to send api req. For private chat only.
    """
    result = {}
    if pattern_username:
        recipient_telegram_name = pattern_username.group(1)
        result.setdefault('recipient_telegram_name', recipient_telegram_name)
        organization_id = get_active_organization(message.from_user.id)
        token = get_token_by_organization_id(telegram_id=message.from_user.id,
                                             telegram_name=message.from_user.username,
                                             organization_id=organization_id,
                                             first_name=message.from_user.first_name,
                                             last_name=message.from_user.last_name)
        result.setdefault('token', token)
        if not token:
            await message.answer(errors["no_token"])
            return
        if pattern_tag:
            tag_id = find_tag_id(pattern_tag, token)
            result.setdefault('tag_id', tag_id)
    else:
        return
    return result


async def check_tag(send_like_dict: dict, pattern_tag: re, message: types.Message) -> bool:
    """
    Check is tag has id, so is it possible to use this tag.
    """
    if not send_like_dict.get('tag_id') and pattern_tag:
        answer = await message.answer(f"Тег {pattern_tag.group(1)} не найден, спасибка не отправлена\n"
                                      f"Можно использовать только теги из списка /tags")
        if message.chat.type != types.ChatType.PRIVATE:
            await delete_message_bot_answer(answer, message.chat.id)
            return False
    return True


async def check_recipient_id(send_like_dict: dict, pattern_username: re, amount: int, message: types.Message) -> bool:
    """
    Check if bot can send api req to send-coins/ endpoint.
    """
    if not send_like_dict.get('recipient_telegram_id')\
            and not pattern_username \
            and amount:
        await message.answer("Я не смог найти id получателя. "
                             "Возможно вы ответили на сообщение которое было в чате до моего добавления.")
        return False
    return True


async def send_like_to_user(message: types.Message, send_like_dict: dict, amount: int, reason: str):
    """
    Call an api endpoint to send like to user.
    """
    try:
        mention = message.reply_to_message.from_user.get_mention(as_html=True)
    except AttributeError:
        mention = send_like_dict.get('recipient_telegram_name')
    result = send_like(user_token=send_like_dict.get('token'),
                       telegram_id=send_like_dict.get('recipient_telegram_id'),
                       telegram_name=send_like_dict.get('recipient_telegram_name'),
                       amount=amount,
                       tags=send_like_dict.get('tag_id'),
                       reason=reason,
                       group_id=send_like_dict.get('group_id'),
                       recipient_name=send_like_dict.get('recipient_name'),
                       recipient_last_name=send_like_dict.get('recipient_last_name'),
                       mention=mention)
    if result:
        answer = await message.reply(f"{result}", parse_mode=types.ParseMode.HTML)
        if message.chat.type != types.ChatType.PRIVATE:
            await delete_message_bot_answer(answer, message.chat.id)