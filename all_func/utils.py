from aiogram import types


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
    ])


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
            text += f"Пользователь: <code>{i['user']['tg_name'].replace('<', '').replace('>', '')}</code>\n" \
                    f"Получено: <code>{i['income_likes']}</code>\n\n"
    return start_text + text
