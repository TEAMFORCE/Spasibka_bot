import requests

from censored import token_drf, drf_url


def get_token(telegram_id, group_id, telegram_name):
    '''
    :param telegram_id: id пользователя
    :param group_id: id группы телеграм
    :param telegram_name: имя пользователя телеграм
    :return: токен пользователя в drf
    '''
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
        return r.json()['detail']
    else:
        return 'Что то пошло не так'


def get_balance(token):
    '''
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
                '''

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


def send_like(token, telegram_id, telegram_name, amount):
    headers = {
        "accept": "application/json",
        "Authorization": "Token " + token,
    }

    body = {
        "recipient_telegram_id": telegram_id,
        "recipient_tg_name": telegram_name,
        "amount": amount,
        "is_anonymous": True,
        "reason": "sended_by_bot",
    }

    r = requests.post('http://176.99.6.251:8888/send-coins/', headers=headers, json=body)
    try:
        result = f'Количество: {r.json()["amount"]}\n' \
                 f'Спасибка отправлена'
    except Exception:
        result = r.json()[0] # 'Что-то пошло не так'

    return result


if __name__ == "__main__":
    # just test
    print(get_token(
        telegram_id="5148438149",
        group_id="-888649764",
        telegram_name="WLeeto",
    ))

    print(send_like(
        token='Token da28bf6693a7018cedf679cc618d61a80529e3a6',
        telegram_id="183417405",
        telegram_name="Brukva2",
        amount=1
    ))
