from aiogram import types, Dispatcher

from create_bot import dp, bot, logger
from API.api_requests import send_like, get_token, cansel_transaction, get_token_by_organization_id, all_like_tags, \
    set_active_organization, get_active_organization, change_group_id
from dict_cloud.dicts import messages, errors
from handlers.client import delete_message_bot_answer
import re


@dp.message_handler(content_types=[types.ContentType.MIGRATE_TO_CHAT_ID, types.ContentType.MIGRATE_FROM_CHAT_ID])
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


# @dp.message_handler(content_types=['text'])
async def likes(message: types.Message):
    """
    При получении сообщения начинающегося с '+' отправляет лайки пользователю цитируемого сообщения
    Формат: +n 'необязательное сообщение', n-количество спасибок
    Формат +n @Nickname 'необязательное сообщение', n-количество спасибок по никнейму
    Формат +n @Nickname 'необязательное сообщение' #тэг, n-количество спасибок по никнейму с тэгом
    """
    if message.text.startswith('+'):
        pattern_username = re.search(r'@(\w+)', message.text)
        pattern_tag = re.search(r'#(\D*)', message.text)
        pattern_amount = re.match(r'\+(\d*)(.*)', message.text)
        pattern_reason = re.match(r'\+\d*\s?(@\w*)?\s?(.*?)\s*(#|$)', message.text)
        amount = pattern_amount.group(1)
        result = None
        tag_id = None
        token = None
        recipient_telegram_id = None
        recipient_telegram_name = None
        tag = None
        group_id = None
        recipient_name = None
        recipient_last_name = None
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        sender_telegram_id = message.from_user.id
        sender_telegram_name = message.from_user.username

        if len(pattern_reason.group(2)) > 0:
            reason = pattern_reason.group(2).capitalize()
        else:
            reason = "Отправлено через telegram"

        if message.from_user.id != message.chat.id:
            if amount:
                group_id = str(message.chat.id)
                token = get_token(telegram_id=sender_telegram_id, group_id=group_id, telegram_name=sender_telegram_name,
                                  first_name=first_name, last_name=last_name)
                if not token:
                    await message.answer(errors["no_token"])
                    return
                if message.reply_to_message:
                    recipient_telegram_id = str(message.reply_to_message.from_user.id)
                    recipient_telegram_name = message.reply_to_message.from_user.username
                    recipient_name = message.reply_to_message.from_user.first_name
                    recipient_last_name = message.reply_to_message.from_user.last_name
                    if pattern_tag:
                        tag = pattern_tag.group(1).lower()
                        all_tags = all_like_tags(user_token=token)
                        for i in all_tags:
                            if i['name'].lower() == tag:
                                tag_id = str(i['id'])
                                break

                elif pattern_username:
                    recipient_telegram_name = pattern_username.group(1)
                    if pattern_tag:
                        tag = pattern_tag.group(1).lower()
                        all_tags = all_like_tags(user_token=token)
                        for i in all_tags:
                            if i['name'].lower() == tag:
                                tag_id = str(i['id'])
                                break
        else:
            if pattern_username:
                recipient_telegram_name = pattern_username.group(1)
                organization_id = get_active_organization(sender_telegram_id)
                group_id = None
                token = get_token_by_organization_id(telegram_id=sender_telegram_id,
                                                     telegram_name=sender_telegram_name,
                                                     organization_id=organization_id,
                                                     first_name=first_name,
                                                     last_name=last_name)
                if not token:
                    await message.answer(errors["no_token"])
                    return
                if pattern_tag:
                    tag = pattern_tag.group(1).lower()
                    all_tags = all_like_tags(user_token=token)
                    for i in all_tags:
                        if i['name'].lower() == tag:
                            tag_id = str(i['id'])
                            break
            else:
                return

        if tag_id is None and pattern_tag:
            answer = await message.answer(f"Тег {tag} не найден, спасибка не отправлена\n"
                                          f"Можно использовать только теги из списка /tags")
            if message.chat.type != types.ChatType.PRIVATE:
                await delete_message_bot_answer(answer, message .chat.id)
                return

        if not recipient_telegram_id and message.chat.type != types.ChatType.PRIVATE and not pattern_username \
                and amount:
            await message.answer("Я не смог найти id получателя. "
                                 "Возможно вы ответили на сообщение которое было в чате до моего добавления.")
            return

        if token:
            try:
                mention = message.reply_to_message.from_user.get_mention(as_html=True)
            except AttributeError:
                mention = recipient_telegram_name
            result = send_like(user_token=token,
                               telegram_id=recipient_telegram_id,
                               telegram_name=recipient_telegram_name,
                               amount=amount,
                               tags=tag_id,
                               reason=reason,
                               group_id=group_id,
                               recipient_name=recipient_name,
                               recipient_last_name=recipient_last_name,
                               mention=mention)
        if result is not None:
            answer = await message.reply(f"{result}", parse_mode=types.ParseMode.HTML)
            if message.chat.type != types.ChatType.PRIVATE:
                await delete_message_bot_answer(answer, message.chat.id)


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
    dp.register_message_handler(likes, content_types=['text'])
    dp.register_callback_query_handler(cancel_like, lambda c: c.data.startswith('delete '))
    dp.register_callback_query_handler(change_active_organization, lambda c: c.data.startswith('org '))
    dp.register_message_handler(greetings, content_types=[types.ContentType.NEW_CHAT_MEMBERS])
