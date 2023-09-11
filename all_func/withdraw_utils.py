import asyncio

from aiogram import types
from aiogram.utils.exceptions import MessageNotModified

from API.api_requests import get_token, get_active_organization, get_token_by_organization_id, get_user
from create_bot import user_req
from create_logger import logger


def get_withdraw_amount(message: types.Message) -> int:
    """
    Get the amount of withdraw.
    """
    amount = message.text.replace("/withdraw ", "").replace(" ", "")
    try:
        return int(amount)
    except ValueError:
        return


def get_user_token_and_organization_id(message: types.Message) -> (str, int, int):
    if message.chat.id != message.from_id:
        organization_id = user_req.get_organization_id_by_group_id(message.chat.id)
        user = get_user(telegram_id=message.from_user.id,
                        group_id=message.chat.id,
                        telegram_name=message.from_user.username,
                        first_name=message.from_user.first_name,
                        last_name=message.from_user.last_name)
    else:
        organization_id = get_active_organization(message.from_user.id)
        user = get_user(telegram_id=message.from_user.id,
                        telegram_name=message.from_user.username,
                        organization_id=organization_id,
                        first_name=message.from_user.first_name,
                        last_name=message.from_user.last_name)
    return user['token'], user['user_id'], organization_id


async def message_timeout_without_keyboard(message: types.Message, timeout: int = 10) -> None:
    """
    Check if message have markup and hide it.
    """
    await asyncio.sleep(timeout)
    if message.reply_markup:
        try:
            await message.delete_reply_markup()
        except MessageNotModified:
            pass