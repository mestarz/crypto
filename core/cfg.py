import logging
import os
import configparser

from configparser import ConfigParser
from logging import Logger

import okx.Account
import okx.Trade
import okx.PublicData
import okx.MarketData

from core.retry import retry

current_path = os.path.dirname(os.path.abspath(__file__))


def get_config(file_name: str) -> ConfigParser:
    config_path = os.path.join(f"{current_path}/../config", file_name)
    config = configparser.ConfigParser()
    config.read(config_path)
    return config


class Config:
    def __init__(self, ctg_path: str):
        self._cfg = get_config(ctg_path)
        flag = "0"
        if self._cfg.getboolean("DEFAULT", "simulate"):
            flag = "1"
        proxy = self._cfg.get("DEFAULT", "proxy")
        apikey = self._cfg.get("OKX", "apikey")
        secretkey = self._cfg.get("OKX", "secretkey")
        passphrase = self._cfg.get("OKX", "passphrase")

        self.accountAPI = okx.Account.AccountAPI(
            api_key=apikey,
            api_secret_key=secretkey,
            passphrase=passphrase,
            use_server_time=False,
            proxy=proxy,
            flag=flag
        )
        self.tradeAPI = okx.Trade.TradeAPI(
            api_key=apikey,
            api_secret_key=secretkey,
            passphrase=passphrase,
            use_server_time=False,
            flag=flag,
            proxy=proxy,
        )
        self.publicDataAPI = okx.PublicData.PublicAPI(
            flag=flag,
            proxy=proxy
        )
        self.marketAPI = okx.MarketData.MarketAPI(
            flag=flag,
            proxy=proxy
        )

        self.logger = self._logger()

    def print_cfg(self):
        # TODO
        pass

    def coin(self) -> str:
        return self._cfg.get("TRADE", "coin")

    def period(self) -> str:
        return self._cfg.get("TRADE", "period")

    def lever(self) -> float:
        return self._cfg.getfloat("TRADE", "lever")

    def ccy(self) -> str:
        return self._cfg.get("TRADE", "ccy")

    def reserved(self) -> float:
        return self._cfg.getfloat("TRADE", "reserved")

    def max_buy_chance(self) -> int:
        return self._cfg.getint("TRADE", "max_buy_chance")

    def trade_timeperiod(self) -> int:
        return self._cfg.getint("TRADE", "trade_timeperiod")

    def factor_param(self, param: str) -> float:
        return self._cfg.getfloat("FACTOR", param)

    @retry()
    def ct_val(self) -> float:
        result = self.publicDataAPI.get_instruments(
            instType="SWAP",
            instId=self.coin()
        )
        coin_info = result['data'][0]
        # 合约面值
        return float(coin_info['ctVal'])

    def _logger(self) -> Logger:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        handle = logging.FileHandler(self._cfg.get("LOG", "filename"))
        handle.setLevel(logging.DEBUG)
        console_handle = logging.StreamHandler()
        console_handle.setLevel(logging.DEBUG)

        formatter = logging.Formatter("%(asctime)s [%(levelname)s] - %(message)s")
        handle.setFormatter(formatter)
        console_handle.setFormatter(formatter)

        logger.addHandler(handle)
        logger.addHandler(console_handle)
        return logger
