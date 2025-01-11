import logging
from logging import Logger
from time import sleep

import httpx

default_logger = logging.getLogger()


def retry(tries: int = -1, delay: int = 1, logger: Logger = default_logger):
    """
    装饰器，用于重试（当出现异常时）

    :param tries: 尝试次数, 当tries==-1时，无限次重复
    :param delay: 重连等待时间 / 秒
    :type logger: 日志句柄

    """

    def deco_retry(func):
        def wrapper(self, *args, **kwargs):
            count = tries
            _logger = logger
            if hasattr(self, "logger"):
                _logger = self.logger

            while count > 0 or tries == -1:
                try:
                    return func(self, *args, **kwargs)
                except httpx.ConnectTimeout as e:
                    _logger.warning(f" {func.__name__} - {str(e)}, Retrying ...")
                except Exception as e:
                    _logger.error(f" {func.__name__} - {str(e)}, Unknown Error !!!")
                count -= 1
                sleep(delay)

        return wrapper  # true decorator

    return deco_retry
