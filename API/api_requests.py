import asyncio

import requests

from API.utils import logger_api_message
from censored import token_drf, drf_url
from all_func.log_func import create_transaction_log

from create_logger import logger
from service.service_func import get_body_of_get_balance


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
        logger.error(f"tg-organization-settings/ returns {r.status_code} on request:\n"
                     f"headers: {headers}, body: {body}\n"
                     f"Error info: {r.text}")
        return None


def get_token(telegram_id, group_id, telegram_name=None, first_name=None, last_name=None):
    """
    :param last_name:
    :param first_name:
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
        "first_name": first_name,
        "last_name": last_name,
    }
    r = requests.post(drf_url + 'tg-get-user-token/', headers=headers, json=body)

    if r.status_code == 200:
        return r.json()['token']
    else:
        logger.error(f"tg-get-user-token/ returns {r.status_code} on request:\n"
                     f"headers: {headers}, body: {body}\n"
                     f"Error info: {r.text}")
        return None


def get_user(telegram_id, group_id=None, organization_id=None, telegram_name=None, first_name=None, last_name=None):
    """
    Возвращает json с токеном и id пользователя.
    Принимает либо group_id либо organization_id, но не оба сразу.
    """
    headers = {
        "accept": "application/json",
        "Authorization": token_drf,
    }
    body = {
        "telegram_id": telegram_id,
        "group_id": group_id,
        "tg_name": telegram_name,
        "first_name": first_name,
        "last_name": last_name,
        "organization_id": organization_id,
    }
    r = requests.post(drf_url + 'tg-get-user-token/', headers=headers, json=body)

    if r.status_code == 200:
        return r.json()
    else:
        logger.error(f"tg-get-user-token/ returns {r.status_code} on request:\n"
                     f"headers: {headers}, body: {body}\n"
                     f"Error info: {r.text}")
        return None


def get_token_by_organization_id(telegram_id, organization_id, telegram_name=None, first_name=None, last_name=None) \
        -> str or None:
    """
    :param last_name:
    :param first_name:
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
        "first_name": first_name,
        "last_name": last_name,
    }
    r = requests.post(drf_url + 'tg-get-user-token/', headers=headers, json=body)

    if r.status_code == 200:
        return r.json()['token']
    else:
        logger.error(f"tg-get-user-token/ returns {r.status_code} on request:\n"
                     f"headers: {headers}, body: {body}\n"
                     f"Error info: {r.text}")
        return None


def get_balance(telegram_id: int, tg_name: str = None, group_id: int = None, organization_id: int = None):
    """
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

    if not group_id and not organization_id:
        return False
    headers = {
        "accept": "application/json",
        'Authorization': token_drf,
    }

    body = get_body_of_get_balance(telegram_id, tg_name, group_id, organization_id)

    r = requests.post(drf_url + 'tg-balance/', headers=headers, json=body)
    if r.status_code == 200:
        return r.json()
    else:
        logger.error(f"user/balance/ returns {r.status_code} on request:\n"
                     f"headers: {headers}\n"
                     f"Error info: {r.text}")
        return None


def send_like(user_token: str, **kwargs):
    global tag_name
    headers = {
        "accept": "application/json",
        "Authorization": "Token " + user_token,
    }
    body = {
        "recipient_telegram_id": kwargs.get("telegram_id"),
        "recipient_tg_name": kwargs.get("telegram_name"),
        "group_id": kwargs.get("group_id"),
        "amount": kwargs.get("amount"),
        "is_anonymous": False,
        "reason": kwargs.get("reason"),
        "tags": kwargs.get("tags"),
        "recipient_name": kwargs.get("recipient_name"),
        "recipient_second_name": kwargs.get("recipient_last_name"),
    }

    r = requests.post(drf_url + 'send-coins/', headers=headers, json=body)

    # Пишем лог
    asyncio.create_task(create_transaction_log(
        user_token=user_token,
        group_id=kwargs.get("group_id"),
        telegram_id=kwargs.get("telegram_id"),
        telegram_name=kwargs.get("telegram_name"),
        amount=kwargs.get("amount"),
        tags=kwargs.get("tags"),
        reason=kwargs.get("reason"),
        response_code=r.status_code,
    ))

    amount_word = r.json().get('amount_word')
    logger.info(r.json())

    if r.status_code == 201 and kwargs.get("tags"):
        all_tags = all_like_tags(user_token)
        for i in all_tags:
            if i['id'] == int(kwargs.get("tags")):
                tag_name = i['name']
        return f'Перевод {kwargs.get("amount")} {amount_word} пользователю {kwargs.get("mention")} ' \
               f'сформирован с тегом #{tag_name.replace(" ", "_")}'
    elif r.status_code == 201:
        return f'Перевод {kwargs.get("amount")} {amount_word} пользователю {kwargs.get("mention")}'
    elif r.status_code == 500:
        return 'Что то пошло не так\n' \
               'Проверьте что группа зарегистрирована в системе'
    else:
        logger.error(f"send-coins/ returns {r.status_code} on request:\n"
                     f"headers: {headers}, body: {body}\n"
                     f"Error info: {r.text}")
        return r.json()[0]


def user_organizations(telegram_id: str, tg_name: str = None, first_name: str = None, last_name: str = None):
    """
    Выводит json со всеми организациями пользователя
    """
    headers = {
        "accept": "application/json",
        "Authorization": token_drf,
    }
    body = {
        'telegram_id': telegram_id,
        'tg_name': tg_name,
        'first_name': first_name,
        'last_name': last_name,
    }

    r = requests.post(drf_url + 'tg-user-organizations/', headers=headers, json=body)

    if r.status_code == 200:
        return r.json()
    else:
        logger.error(f"user/balance/ returns {r.status_code} on request:\n"
                     f"headers: {headers}\n"
                     f"Error info: {r.text}")
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
        logger.error(f"tg-export/ returns {r.status_code} on request:\n"
                     f"headers: {headers}, body: {body}\n"
                     f"Error info: {r.text}")
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
        logger.error(f"cancel-transaction/ returns {r.status_code} on request:\n"
                     f"headers: {headers}, body: {body}\n"
                     f"Error info: {r.text}")
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
        logger.error(f"send-coins-settings/ returns {r.status_code} on request:\n"
                     f"headers: {headers}\n"
                     f"Error info: {r.text}")
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
        logger.error(f"set-bot-organization/ returns {r.status_code} on request:\n"
                     f"headers: {headers}, body: {body}\n"
                     f"Error info: {r.text}")
        return False


def get_active_organization(telegram_id: str):
    """
    Отдает id активной организации или None если таких нет.
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
        logger.error(f"tg-user-organizations/ returns {r.status_code} on request:\n"
                     f"headers: {headers} body: {body}\n"
                     f"Error info: {r.text}")
        return None


def tg_handle_start(tg_name: str, telegram_id: str, group_id: int = None,
                    group_name: str = None, first_name: str = None, last_name: str = None,
                    organization_id: int = None, is_group_owner: bool = False) -> str or None:
    """
    Для команды /start. Возвращает номер статуса или str если запрос выполнен неверно.
    """
    headers = {
        "accept": "application/json",
        "Authorization": token_drf,
    }
    body = {
        "tg_name": tg_name,
        "telegram_id": telegram_id,
        "group_id": group_id,
        "group_name": group_name,
        "first_name": first_name,
        "last_name": last_name,
        "organization_id": organization_id,
        'is_owner': is_group_owner,
    }
    logger.info(f"Sending post to tg-handle-start/. Body: {body}")
    r = requests.post(drf_url + 'tg-handle-start/', headers=headers, json=body)

    if r.status_code == 200:
        return r.json()
    else:
        logger.error(f"tg-handle-start/ returns {r.status_code} on request:\n"
                     f"headers: {headers} body: {body}\n"
                     f"Error info: {r.text}")
        return None


def get_ratings(user_token: str) -> list or None:
    """
    Возвращает статистику по группе. Группа определяется токеном.
    """
    headers = {
        "accept": "application/json",
        "Authorization": f"Token {user_token}",
    }

    r = requests.get(drf_url + 'rating/overall/', headers=headers)

    if r.status_code == 200:
        return r.json()
    else:
        logger.error(f"rating/overall/ returns {r.status_code} on request:\n"
                     f"headers: {headers}\n"
                     f"Error info: {r.text}")
        return None


def get_rating_xls(user_token: str) -> tuple or None:
    """
    Возвращает rb tuple для формирования xls.
    """
    headers = {
        "accept": "application/json",
        "Authorization": f"Token {user_token}",
    }
    body = {
        "format": "excel",
    }

    r = requests.post(drf_url + 'rating/download/', headers=headers, json=body)

    if r.status_code == 200:
        return r.content
    else:
        logger.error(f"rating/download/ returns {r.status_code} on request:\n"
                     f"headers: {headers} body: {body}\n"
                     f"Error info: {r.text}")
        return None


def change_group_id(old_id: int, new_id: int):
    """
    Изменяет id группы в БД.
    """
    headers = {
        "accept": "application/json",
        "Authorization": token_drf,
    }
    body = {
        "old_group_id": old_id,
        "new_group_id": new_id,
    }
    r = requests.patch(drf_url + 'tg-group-migrate/', headers=headers, json=body)
    if r.status_code == 200:
        logger.info(f"Group id was changed from {old_id} to {new_id}")
        return True
    else:
        logger.error(f"tg-group-migrate/ returns {r.status_code} on request:\n"
                     f"headers: {headers} body: {body}\n"
                     f"Error info: {r.text}")
        return None


def get_scores(user_token: str) -> dict or None:
    """
    Возвращает общее число спасибок по токену пользователя.
    """
    headers = {
        "accept": "application/json",
        "Authorization": f"Token {user_token}",
    }
    r = requests.get(drf_url + 'tg-transaction-count/', headers=headers)
    if r.status_code == 200:
        return r.json()
    else:
        logger.error(f"tg-transaction-count/ returns {r.status_code} on request:\n"
                     f"headers: {headers}\n"
                     f"Error info: {r.text}")
        return None


def get_scoresxlsx(user_token: str) -> dict or None:
    """
    Возвращает общее число спасибок по токену пользователя.
    """
    headers = {
        "accept": "application/json",
        "Authorization": f"Token {user_token}",
    }
    r = requests.get(drf_url + 'tg-transaction-export/', headers=headers)
    if r.status_code == 200:
        return r.content
    else:
        logger.error(f"tg-transaction-export/ returns {r.status_code} on request:\n"
                     f"headers: {headers}\n"
                     f"Error info: {r.text}")
        return None


def get_balances(user_token: str, organization_id: int = None, group_tg_id: int = None):
    """
    Returns b xls with balance stat.
    """
    headers = {
        "accept": "application/json",
        "Authorization": f"Token {user_token}",
    }
    r = requests.get(drf_url + f'api/{organization_id}/stats/balances/', headers=headers)
    if r.status_code == 200:
        return r.content
    else:
        logger.error(f"api/{organization_id}/stats/balances/ returns {r.status_code} on request:\n"
                     f"headers: {headers}\n"
                     f"Error info: {r.text}")
        return None


def get_balances_from_group(user_token: str, group_tg_id: int = None):
    """
    Returns b xls with balance stat.
    """
    group_tg_id = abs(group_tg_id)
    headers = {
        "accept": "application/json",
        "Authorization": f"Token {user_token}",
    }
    r = requests.get(drf_url + f'api/{group_tg_id}/tg_stats/balances/', headers=headers)
    if r.status_code == 200:
        return r.content
    else:
        logger.error(f"api/{group_tg_id}/tg_stats/balances/ returns {r.status_code} on request:\n"
                     f"headers: {headers}\n"
                     f"Error info: {r.text}")
        return None


class UserRequests:
    def __init__(self):
        self.url = drf_url

    def withdraw_amount_check(self, token: str, amount: int) -> dict:
        url = f'{self.url}api/withdraw/request/check/{amount}/'
        headers = {
            "accept": "application/json",
            "Authorization": f"Token {token}",
        }
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return r.json()
        else:
            logger_api_message('error', url, r.request.method, r.status_code, r, headers)
            return

    def get_organization_admin_list(self, token: str, organization_id: int = None, group_id: int = None) -> list:
        """
        Get organization's admin tg list by organization id or tg group id.
        """
        url = f'{self.url}api/withdraw/request/organization_admins/?organization_id={organization_id}'
        headers = {
            "accept": "application/json",
            "Authorization": f"Token {token}",
        }
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return r.json()['details']['list_of_admins']
        else:
            logger_api_message('error', url, r.request.method, r.status_code, r, headers)
            return

    def get_organization_id_by_group_id(self, token: str, group_id: int) -> int:
        """
        Get organization id by group tg id.
        """
        url = f'{self.url}api/withdraw/request/organization/?group_id={group_id}'
        headers = {
            "accept": "application/json",
            "Authorization": f"Token {token}",
        }
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            logger.warning(r.json())
            return r.json()['details']['organization_id']
        else:
            logger_api_message('error', url, r.request.method, r.status_code, r, headers)
            return

    def create_withdraw_record(self, token: str, amount: int):
        """
        Create withdraw request record.
        """
        url = f'{self.url}api/withdraw/withdraw_request/create_from_bot/'
        headers = {
            "accept": "application/json",
            "Authorization": f"Token {token}",
        }
        body = {
            'amount': amount
        }
        r = requests.post(url, headers=headers, json=body)
        if r.status_code == 200:
            return r.json()
        else:
            logger_api_message('error', url, r.request.method, r.status_code, r, headers, body)
            return

    def confirm_withdraw(self, withdraw_id: int, controller_tg_id: int):
        """
        Confirm withdraw request.
        """
        url = f'{self.url}api/withdraw/confirm/'
        headers = {
            "accept": "application/json",
            "Authorization": token_drf,
        }
        body = {
            'withdraw_request_id': withdraw_id,
            'controller_tg_id': controller_tg_id,
        }
        r = requests.post(url, headers=headers, json=body)
        if r.status_code == 200:
            return r.json()
        else:
            logger_api_message('error', url, r.request.method, r.status_code, r, headers, body)
            return

    def decline_withdraw(self, withdraw_id: int, controller_tg_id: int):
        """
        Decline withdraw request.
        """
        url = f'{self.url}api/withdraw/decline/'
        headers = {
            "accept": "application/json",
            "Authorization": token_drf,
        }
        body = {
            'withdraw_request_id': withdraw_id,
            'controller_tg_id': controller_tg_id,
        }
        r = requests.post(url, headers=headers, json=body)
        if r.status_code == 200:
            return r.json()
        else:
            logger_api_message('error', url, r.request.method, r.status_code, r, headers, body)
            return


class ConfirmChallenge(UserRequests):

    def get_contenders_list(self, token: str, challenge_id: int):
        """

        :param token:
        :param challenge_id:
        :return:
        """
        url = f'{self.url}challenge-contenders/{challenge_id}/'
        headers = {
            "accept": "application/json",
            "Authorization": f"Token {token}",
        }
        r = requests.get(url, headers=headers)
        logger.info(f'Send {r.request.method} to {url} with headers {headers}')
        if r.status_code == 200:
            '''
            Resp example:
            [
                {
                    "nickname": null,
                    "challenge_id": 351,
                    "user_liked": false,
                    "my_report": false,
                    "can_approve": true,
                    "participant_id": 325,
                    "participant_photo": "/media/users_photo/c9b4a8e7430a4a248d2a86e5226c85d0_thumb.jpg",
                    "participant_name": "Олег",
                    "participant_surname": "Марченко",
                    "report_created_at": "2023-10-19T08:05:15.142268Z",
                    "report_text": "Просто тест",
                    "report_photo": null,
                    "report_id": 492,
                    "comments_amount": 0,
                    "likes_amount": 0,
                    "report_photos": null
                }
            ]
            '''
            logger.info(f'Status: {r.status_code}. Result: {r.text}')
            return r.json()
        else:
            logger.warning(f'Status: {r.status_code}. Result: {r.text}')
            return

    def create_contender_report(self, token: str, challenge_id: int, text: str) -> dict:
        """
        :param token:
        :param challenge_id:
        :param text:
        :return:
        """
        url = f'{self.url}create-challenge-report/'
        headers = {
            "accept": "application/json",
            "Authorization": f"Token {token}",
        }
        body = {
            'challenge': challenge_id,
            'text': text
        }
        r = requests.post(url, headers=headers, json=body)
        logger.info(f'Send {r.request.method} to {url} with headers: {headers} and body: {body}')
        if r.status_code == 201:
            '''
            Resp example:
            {
                "id": 497,
                "challenge": 351,
                "text": "Тест через апи"
            }
            '''
            logger.info(f'Status: {r.status_code}. Result: {r.text}')
            return r.json()
        else:
            logger.warning(f'Status: {r.status_code}. Result: {r.text}')
            return

    def confirm_winner(self, token: str, report_id: int):
        url = f'{self.url}check-challenge-report/{report_id}/'
        headers = {
            "accept": "application/json",
            "Authorization": f"Token {token}",
        }
        body = {
            'state': 'W',
            'text': 'Confirm from bot.'
        }
        r = requests.put(url, headers=headers, json=body)
        logger.info(f'Send {r.request.method} to {url} with headers: {headers} and body: {body}')
        if r.status_code == 200:
            '''
            Resp example:
            {
                "state": "W",
                "new_reports_exists": true
            }
            '''
            logger.info(f'Status: {r.status_code}. Result: {r.text}')
            return r.json()
        else:
            logger.warning(f'Status: {r.status_code}. Result: {r.text}')
            return