from datetime import datetime

import numpy
import pandas as pd

from dataclasses import dataclass

import talib

from core.cfg import Config
from core.execute import Execute


@dataclass
class Factor:
    rsi: float
    ma_fast: float
    ma_slow: float


class RSIGrid:
    def __init__(self, execution: Execute, cfg: Config):
        self.exec = execution
        self.cfg = cfg
        self.logger = cfg.logger

        # 买入触发间隔
        self.time_step = 5 * 60
        self.last_buy_time = datetime.now()
        self.last_sell_time = datetime.now()
        self.buy_step = self.time_step
        self.sell_step = self.time_step

    def _factor(self, price: pd.DataFrame) -> Factor:
        price["Mid"] = (price["Close"] + price["Open"]) / 2
        price["RSI"] = talib.RSI(price["Mid"], timeperiod=self.cfg.factor_param("rsi_timeperiod"))
        price["FAST"] = talib.MA(price["Mid"], timeperiod=self.cfg.factor_param("ma_fast_timeperiod"))
        price["SLOW"] = talib.MA(price["Mid"], timeperiod=self.cfg.factor_param("ma_slow_timeperiod"))

        rsi = price["RSI"].iloc[-1]
        ma_fast = price["FAST"].iloc[-1]
        ma_slow = price["SLOW"].iloc[-1]

        self.logger.debug(f"rsi:{rsi:.2f}, fast:{ma_fast:.6f}, slow:{ma_slow:.6f}")
        return Factor(rsi, ma_fast, ma_slow)

    def _buy_condition(self, factor: Factor) -> bool:
        if (datetime.now() - self.last_buy_time).seconds < self.buy_step:
            return False
        return factor.ma_slow > factor.ma_fast and factor.rsi < self.cfg.factor_param("rsi_down")

    def _sell_condition(self, factor: Factor) -> bool:
        if (datetime.now() - self.last_sell_time).seconds < self.sell_step:
            return False
        return factor.ma_slow < factor.ma_fast and factor.rsi > self.cfg.factor_param("rsi_up")

    def run(self):

        while True:
            price = self.exec.price()
            factor = self._factor(price)
            if self._buy_condition(factor):
                self.exec.buy()
                self.logger.info("<触发买入>")
                self.buy_step *= 2
                self.last_buy_time = datetime.now()
                self.sell_step = self.time_step
            elif self._sell_condition(factor):
                self.exec.sell()
                self.logger.info("<触发卖出>")
                self.sell_step *= 2
                self.last_sell_time = datetime.now()
                self.buy_step = self.time_step
            self.exec.sleep(self.cfg.trade_timeperiod())
