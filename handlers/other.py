from aiogram import types, Dispatcher

from all_func.utils import get_reason, send_like_in_group, send_like_in_private_msg, check_tag, check_recipient_id, \
    send_like_to_user
from create_bot import dp, bot
from create_logger import logger
from API.api_requests import send_like, get_token, cansel_transaction, get_token_by_organization_id, all_like_tags, \
    set_active_organization, get_active_organization, change_group_id
from dict_cloud.dicts import messages, errors
from handlers.client import delete_message_bot_answer
import re

from service.misc import find_tag_id


# @dp.message_handler(content_types=[types.ContentType.MIGRATE_TO_CHAT_ID, types.ContentType.MIGRATE_FROM_CHAT_ID])
async def handle_migration(message: types.Message):
    if message.migrate_from_chat_id:
        old_id = message.migrate_from_chat_id
        new_id = message.chat.id

        text = f"Id группы был изменен с <code>{old_id}</code> на <code>{new_id}</code>\n" \
               f"Возможно вам придется снова сделать меня администратором\n"

        response = change_group_id(old_id, new_id)
        if response:
            text += "Я изменил id внутри базы, все хорошо ;)"
        else:
            text += "Пожалуйста перешлите это сообщение администратору"
        await message.answer(text, parse_mode=types.ParseMode.HTML)


# @dp.message_handler(lambda message: message.text.startswith('+'))
async def likes(message: types.Message):
    """
    При получении сообщения начинающегося с '+' отправляет лайки пользователю цитируемого сообщения
    Формат: +n 'необязательное сообщение', n-количество спасибок
    Формат +n @Nickname 'необязательное сообщение', n-количество спасибок по никнейму
    Формат +n @Nickname 'необязательное сообщение' #тэг, n-количество спасибок по никнейму с тэгом
    """
    pattern_username = re.search(r'@(\w+)', message.text)
    pattern_tag = re.search(r'#(\D*)', message.text)
    pattern_amount = re.match(r'\+(\d*)(.*)', message.text)
    pattern_reason = re.match(r'\+\d*\s?(@\w*)?\s?(.*?)\s*(#|$)', message.text)
    amount = pattern_amount.group(1)

    reason = await get_reason(pattern_reason)

    if message.from_user.id != message.chat.id:
        send_like_dict = await send_like_in_group(amount, message, pattern_tag, pattern_username)
    else:
        send_like_dict = await send_like_in_private_msg(pattern_username, message, pattern_tag)

    if not await check_tag(send_like_dict, pattern_tag, message):
        return
    if not await check_recipient_id(send_like_dict, pattern_username, amount, message):
        return

    if send_like_dict.get('token'):
        await send_like_to_user(message, send_like_dict, amount, reason)


# @dp.callback_query_handler(lambda c: c.data.startswith('delete '))
async def cancel_like(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    organization_id = callback_query.data.split(" ")[2]
    telegram_name = callback_query.from_user.username
    first_name = callback_query.from_user.first_name
    last_name = callback_query.from_user.last_name
    token = get_token_by_organization_id(telegram_id, organization_id, telegram_name, first_name, last_name)
    await callback_query.answer(f'Отменяем транзакцию {callback_query.data.split(" ")[1]}')
    message = cansel_transaction(user_token=token, like_id=int(callback_query.data.split(" ")[1]))
    await bot.edit_message_text(text=message,
                                chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id)


# @dp.callback_query_handler(lambda c: c.data.startswith('org '))
async def change_active_organization(callback_query: types.CallbackQuery):
    organization_id = callback_query.data.split(" ")[1]
    telegram_id = callback_query.from_user.id
    result = set_active_organization(organization_id, telegram_id)
    if result:
        await callback_query.answer(f'Смена организации')
        await bot.delete_message(telegram_id, callback_query.message.message_id)
        await bot.send_message(telegram_id, f'Текущая организация изменена')
    else:
        await bot.delete_message(telegram_id, callback_query.message.message_id)
        await bot.send_message(telegram_id, 'Не удалось сменить организацию')


# @dp.message_handler(content_types=[types.ContentType.NEW_CHAT_MEMBERS])
async def greetings(message: types.Message):
    new_member = message.new_chat_members[0]
    me = await bot.get_me()
    bot_name = me.username
    answer = await bot.send_message(message.chat.id, messages['greetings'].format(user_name=new_member.username,
                                                                                  bot_name=bot_name))
    await delete_message_bot_answer(answer, message.chat.id)


def register_handlers_other(dp: Dispatcher):
    dp.register_message_handler(likes, lambda message: message.text.startswith('+'))
    dp.register_callback_query_handler(cancel_like, lambda c: c.data.startswith('delete '))
    dp.register_callback_query_handler(change_active_organization, lambda c: c.data.startswith('org '))
    dp.register_message_handler(greetings, content_types=[types.ContentType.NEW_CHAT_MEMBERS])
    dp.register_message_handler(handle_migration, content_types=[types.ContentType.MIGRATE_TO_CHAT_ID,
                                                                 types.ContentType.MIGRATE_FROM_CHAT_ID
                                                                 ])
