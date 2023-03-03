import requests

from censored import token_drf, drf_url


def messages_lifetime(group_id: str) -> dict:
    """
    Возвращает словарь со значениями времени жизни сообщений для группы
    :param group_id: id группы из тг
    :return: словарь с ключами bot_messages_lifetime и bot_commands_lifetime
    """
    headers = {
        "accept": "application/json",
        "Authorization": token_drf,
    }
    body = {
        "group_id": group_id,
    }
    r = requests.post(drf_url + 'tg-organization-settings/', headers=headers, json=body)
    if r.status_code == 200:
        return r.json()
    else:
        return None


def get_token(telegram_id, group_id, telegram_name=None):
    """
    :param telegram_id: id пользователя
    :param group_id: id группы телеграм
    :param telegram_name: имя пользователя телеграм
    :return: токен пользователя в drf
    """
    headers = {
        "accept": "application/json",
        "Authorization": token_drf,
    }
    body = {
        "telegram_id": telegram_id,
        "group_id": group_id,
        "tg_name": telegram_name,
    }
    r = requests.post(drf_url + 'tg-get-user-token/', headers=headers, json=body)
    if 'token' in r.json():
        return r.json()['token']
    elif 'status' in r.json():
        return r.json()['status']
    elif 'detail' in r.json():
        print(r.json()['detail'])
    else:
        print('Что то пошло не так')


def get_token_by_organization_id(telegram_id, organization_id, telegram_name=None):
    """
    :param telegram_id: id пользователя
    :param organization_id: id группы в RestAPI
    :param telegram_name: имя пользователя телеграм
    :return: токен пользователя в drf
    """
    headers = {
        "accept": "application/json",
        "Authorization": token_drf,
    }
    body = {
        "telegram_id": telegram_id,
        "organization_id": organization_id,
        "tg_name": telegram_name,
    }
    r = requests.post(drf_url + 'tg-get-user-token/', headers=headers, json=body)

    if 'token' in r.json():
        return r.json()['token']
    elif 'status' in r.json():
        return r.json()['status']
    elif 'detail' in r.json():
        return r.json()['detail']
    else:
        return 'Что то пошло не так'


def get_balance(token: str):
    """
    :param token: токен пользователя в drf
    :return: json со статистикой пользователя
    :format:
    {
    'income':
    {'amount': 17.0, 'frozen': 0.0, 'sent': 0.0, 'received': 17.0, 'cancelled': 0.0},
    'distr':
    {'amount': 0.0, 'frozen': 0.0, 'sent': 0.0, 'received': 0.0, 'cancelled': 0.0, 'expire_date': '2023-01-30'}
    }
    - income - заработанные спасибки
                - amount - общее количество
                - frozen - на подтверждении
                - sent - отправлено
                - received - получено
                - cancelled - аннулировано
    - distr - спасибки для раздачи
                - amount - общее количество
                - expire_date - дата сгорания
                - frozen - на подтверждении
                - sent - отправлено
                - received - получено
                - cancelled - аннулировано
                """

    if token == 'Что то пошло не так':
        return token
    elif token == 'Не найдена организация по переданному group_id':
        return token
    else:
        headers = {
            "accept": "application/json",
            'Authorization': f"Token {token}",
        }
        r = requests.get(drf_url + 'user/balance/', headers=headers)
        return r.json()


def send_like(user_token: str,
              telegram_id: str = None,
              telegram_name: str = None,
              amount: str = None,
              tags: str = None,
              reason: str = None,
              ):
    headers = {
        "accept": "application/json",
        "Authorization": "Token " + user_token,
    }

    body = {
        "recipient_telegram_id": telegram_id,
        "recipient_tg_name": telegram_name,
        "amount": amount,
        "is_anonymous": False,
        "reason": reason,
        "tags": tags,
    }

    r = requests.post(drf_url + 'send-coins/', headers=headers, json=body)

    #  Перевод 1 спасибки пользователю
    thx = 'спасибки'
    if int(amount) >= 5:
        thx = 'спасибок'
    tag_name = None
    if r.status_code == 201 and tags:
        all_tags = all_like_tags(user_token)
        for i in all_tags:
            if i['id'] == int(tags):
                tag_name = i['name']
        return f'Перевод {amount} {thx} пользователю @{telegram_name} сформирован с тегом #{tag_name}'
    elif r.status_code == 201:
        return f'Перевод {amount} {thx} пользователю @{telegram_name}'
    elif r.status_code == 500:
        return 'Что то пошло не так\n' \
               'Проверьте что группа зарегистрирована в системе'
    else:
        return r.json()[0]


def user_organizations(telegram_id: str):
    """
    Выводит json со всеми организациями пользователя
    :type telegram_id: telegram_id пользователя str
    :return: json фаил
    """
    headers = {
        "accept": "application/json",
        "Authorization": token_drf,
    }
    body = {
        'telegram_id': telegram_id,
    }

    r = requests.post(drf_url + 'tg-user-organizations/', headers=headers, json=body)

    if r.status_code == 200:
        return r.json()
    else:
        print(r.json())
        return None


def export_file_transactions_by_group_id(telegram_id: str, group_id: str):
    """
    Для общения в группе. Возвращает фаил .xlxs со всеми транзакциями
    """
    headers = {
        "accept": "application/json",
        "Authorization": token_drf,
    }
    body = {
        "telegram_id": telegram_id,
        "group_id": group_id
    }

    r = requests.post(drf_url + 'tg-export/', headers=headers, json=body)

    if r.status_code == 200:
        return r.content
    elif r.status_code == 404:
        return r.json()
    elif r.status_code == 400:
        return r.json()
    else:
        return {"message": "Что то пошло не так"}


def export_file_transactions_by_organization_id(telegram_id: str, organization_id: int):
    """
    Для общения в ЛС. Возвращает фаил .xlxs со всеми транзакциями активной организации
    """
    headers = {
        "accept": "application/json",
        "Authorization": token_drf,
    }
    body = {
        "telegram_id": telegram_id,
        "organization_id": organization_id
    }

    r = requests.post(drf_url + 'tg-export/', headers=headers, json=body)

    if r.status_code == 200:
        return r.content
    elif r.status_code == 404:
        return r.json()
    elif r.status_code == 400:
        return r.json()
    else:
        return {"message": "Что то пошло не так"}


def get_all_cancelable_likes(user_token: str):
    """
    Выводит список всех транзакций, которые возможно отменить
    """
    headers = {
        "accept": "application/json",
        "Authorization": "Token " + user_token,
    }
    r = requests.get(drf_url + 'user/transactions/waiting/', headers=headers)

    likes_list = []

    for likes in r.json():
        if likes['can_user_cancel']:
            likes_list.append({'amount': likes['amount'],
                               'recipient': likes['recipient']['recipient_tg_name'],
                               'id': likes['id'],
                               'organization': likes['organization'],
                               })
    return likes_list


def cansel_transaction(user_token: str, like_id: int):
    """
    Отменяет спасибку, если это возможно
    """
    headers = {
        "accept": "application/json",
        "Authorization": "Token " + user_token,
    }
    body = {
        'status': 'C',
    }
    r = requests.put(f'{drf_url}cancel-transaction/{like_id}/', headers=headers, json=body)

    if r.status_code == 200:
        return 'Спасибка отменена'
    else:
        return 'Не получилось отменить спасибку'


def all_like_tags(user_token: str):
    """
    Возвращает все теги для спасибок
    """
    headers = {
        "accept": "application/json",
        "Authorization": "Token " + user_token,
    }
    r = requests.get(drf_url + 'send-coins-settings/', headers=headers)
    if r.status_code == 200:
        return r.json()['tags']
    else:
        return 'Что то пошло не так'


def set_active_organization(organization_id: int, telegram_id: str):
    """
    Делает активной выбранную организацию
    """
    headers = {
        "accept": "application/json",
        "Authorization": token_drf,
    }
    body = {
        "organization_id": organization_id,
        "telegram_id": telegram_id,
    }

    r = requests.post(drf_url + 'set-bot-organization/', headers=headers, json=body)
    if r.status_code == 201:
        return True
    else:
        return False


def get_active_organization(telegram_id: str):
    """
    Отдает id активной организации или None если таких нет
    """
    headers = {
        "accept": "application/json",
        "Authorization": token_drf,
    }
    body = {
        'telegram_id': telegram_id,
    }

    r = requests.post(drf_url + 'tg-user-organizations/', headers=headers, json=body)

    if r.status_code == 200:
        for i in r.json():
            if i['is_current']:
                return i['id']
    else:
        return None
