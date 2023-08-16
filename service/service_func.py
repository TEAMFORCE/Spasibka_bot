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


def get_body_of_get_balance(telegram_id: int, tg_name: str = None, group_id: int = None,
                            organization_id: int = None) -> dict:
    """
    Creates dict body for get_balance request.
    """
    if organization_id and tg_name:
        body = {
            "telegram_id": telegram_id,
            "tg_name": tg_name,
            "group_id": group_id,
            "organization_id": organization_id
        }
    elif organization_id and not tg_name:
        body = {
            "telegram_id": telegram_id,
            "group_id": group_id,
            "organization_id": organization_id
        }
    elif not organization_id and tg_name:
        body = {
            "telegram_id": telegram_id,
            "group_id": group_id,
            "organization_id": organization_id
        }
    else:
        body = {
            "telegram_id": telegram_id,
            "group_id": group_id
        }
    return body