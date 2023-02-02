from aiogram import types, Dispatcher

from create_bot import dp, bot
from API.api_requests import send_like, get_token, cansel_transaction, get_token_by_organization_id, all_like_tags
from database.database import deactivate_all, activate_org
from dict_cloud.dicts import messages, sleep_timer
from handlers.client import delete_message
import re


# @dp.message_handler(content_types=['text'])
async def likes(message: types.Message):
    '''
    При получении сообщения начинающегося с '+' отправляет лайки пользователю цитируемого сообщения
    Формат: +n 'необязательное сообщение', n-количество спасибок
    Формат +n @Nickname 'необязательное сообщение', n-количество спасибок по никнейму
    Формат +n @Nickname 'необязательное сообщение' #тэг, n-количество спасибок по никнейму с тэгом
    '''
    if message.text.startswith('+'):
        pattern_username = re.search(r'@(\w+)', message.text)
        pattern_tag = re.search(r'#(\D*)', message.text)
        pattern_amount = re.match(r'\+(\d*)(.*)', message.text)
        amount = pattern_amount.group(1)
        result = None

        if amount:
            sender_telegram_id = message.from_user.id
            group_id = str(message.chat.id)
            sender_telegram_name = message.from_user.username
            token = get_token(telegram_id=sender_telegram_id,
                              group_id=group_id,
                              telegram_name=sender_telegram_name)

            if message.reply_to_message:
                recipient_telegram_id = str(message.reply_to_message.from_user.id)
                recipient_telegram_name = message.reply_to_message.from_user.username
                if pattern_tag:
                    tag = pattern_tag.group(1)
                    all_tags = all_like_tags(user_token=token)
                    for i in all_tags:
                        if i['name'] == tag:
                            tag_id = str(i['id'])
                            break
                        else:
                            tag_id = None
                else:
                    tag_id = None

                result = send_like(user_token=token,
                                   telegram_id=recipient_telegram_id,
                                   telegram_name=recipient_telegram_name,
                                   amount=amount,
                                   tags=tag_id)

            elif pattern_username:
                recipient_telegram_name = pattern_username.group(1)
                if pattern_tag:
                    tag = pattern_tag.group(1)
                    all_tags = all_like_tags(user_token=token)
                    for i in all_tags:
                        if i['name'] == tag:
                            tag_id = str(i['id'])
                            break
                        else:
                            tag_id = None

                    result = send_like(user_token=token,
                                       telegram_name=recipient_telegram_name,
                                       amount=amount,
                                       tags=tag_id)
                else:
                    result = send_like(user_token=token,
                                       telegram_name=recipient_telegram_name,
                                       amount=amount)
        if result is not None:
            answer = await message.reply(result)
            await delete_message(answer, sleep_timer)


# @dp.callback_query_handler(lambda c: c.data.startswith('delete '))
async def cancel_like(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    organization_id = callback_query.data.split(" ")[2]
    telegram_name = callback_query.from_user.username
    token = get_token_by_organization_id(telegram_id, organization_id, telegram_name)
    await callback_query.answer(f'Отменяем транзакцию {callback_query.data.split(" ")[1]}')
    message = cansel_transaction(user_token=token, like_id=int(callback_query.data.split(" ")[1]))
    await bot.edit_message_text(text=message,
                                chat_id=callback_query.from_user.id,
                                message_id=callback_query.message.message_id)


# @dp.callback_query_handler(lambda c: c.data.startswith('org '))
async def change_active_organization(callback_query: types.CallbackQuery):
    await callback_query.answer(f'Активируем {callback_query.data.split(" ")[1]}')
    deactivate_all(tg_id=callback_query.from_user.id)
    activate_org(tg_id=callback_query.from_user.id, org_id=callback_query.data.split(" ")[1])
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
    await bot.send_message(callback_query.from_user.id, f'Текущая организация изменена на {callback_query.data.split(" ")[2]}')


# @dp.message_handler(content_types=[types.ContentType.NEW_CHAT_MEMBERS])
async def greetings(message: types.Message):
    new_member = message.new_chat_members[0]
    me = await bot.get_me()
    bot_name = me.username
    answer = await bot.send_message(message.chat.id, messages['greetings'].format(user_name=new_member.username,
                                                                                  bot_name=bot_name))
    await delete_message(answer, sleep_timer)


def register_handlers_other(dp: Dispatcher):
    dp.register_message_handler(likes, content_types=['text'])
    dp.register_callback_query_handler(cancel_like, lambda c: c.data.startswith('delete '))
    dp.register_callback_query_handler(change_active_organization, lambda c: c.data.startswith('org '))
    dp.register_message_handler(greetings, content_types=[types.ContentType.NEW_CHAT_MEMBERS])
