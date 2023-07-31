import asyncio

from aiogram import types
from aiogram.utils.exceptions import MessageCantBeDeleted

from create_bot import bot
from dict_cloud.dicts import errors, sleep_timer


async def is_bot_admin(message: types.Message) -> None:
    """
    Check if bot is admin in group.
    """
    if message.chat.type != types.ChatType.PRIVATE:
        bot_as_chat_member = await bot.get_chat_member(message.chat.id, bot.id)
        if not bot_as_chat_member.is_chat_admin():
            await bot.send_message(message.chat.id, errors['not_chat_admin'])