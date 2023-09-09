from create_logger import logger
from datetime import datetime
import requests


def logger_api_message(status: str, url: str, method: str, status_code: str = None, request: requests = None):
    now = datetime.now().strftime('%d-%m-%Y %H:%M')
    if status == 'info':
        logger.error(f'{now}//request {method} to {url} get status {status_code}')
    elif status == 'warning':
        logger.error(f'{now}//request {method} to {url} get status {status_code}')
    elif status == 'error':
        logger.error(f'{now}//request {method} to {url} get status {status_code}\ndetails:{request.text}')