from create_logger import logger
from datetime import datetime
import requests


def logger_api_message(status: str, url: str, method: str, status_code: str = None, request: requests = None,
                       headers: dict = None, body: dict = None):
    now = datetime.now().strftime('%d-%m-%Y %H:%M')
    if status == 'info':
        logger.info(f'{now}//request {method} to {url} get status {status_code}\nheaders:{headers}\nbody:{body}')
    elif status == 'warning':
        logger.warning(f'{now}//request {method} to {url} get status {status_code}\nheaders:{headers}\nbody:{body}')
    elif status == 'error':
        logger.error(f'{now}//request {method} to {url} get status {status_code}\nheaders:{headers}\nbody:{body}\n'
                     f'details:{request.text}')
    else:
        logger.critical(f'{now}//request {method} to {url} get status {status_code}\nheaders:{headers}\nbody:{body}\n'
                        f'details:{request.text}')