from API.api_requests import all_like_tags
from aiogram import types
from create_bot import bot
from dict_cloud.dicts import errors


def find_tag_id(pattern_tag, token: str) -> str:
    tag = pattern_tag.group(1).lower().replace("_", " ")
    all_tags = all_like_tags(user_token=token)
    for i in all_tags:
        if i['name'].lower() == tag:
            return str(i['id'])


async def is_bot_admin(message: types.Message) -> None:
    """
    Check if bot is admin in group.
    """
    if message.chat.type != types.ChatType.PRIVATE:
        bot_as_chat_member = await bot.get_chat_member(message.chat.id, bot.id)
        if not bot_as_chat_member.is_chat_admin():
            await bot.send_message(message.chat.id, errors['not_chat_admin'])


def get_challenge_vars(message: types.Message):
    challenge_id = None
    challenge_amount = None
    splitted_text = message.text.split(' ')
    if len(splitted_text) == 2:
        challenge_id = splitted_text[1]
    elif len(splitted_text) == 3:
        challenge_id = splitted_text[1]
        challenge_amount = splitted_text[2]
    else:
        pass
    return challenge_id, challenge_amount