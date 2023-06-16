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