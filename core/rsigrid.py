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

    def _factor(self, price: pd.DataFrame) -> Factor:
        close = price["Close"]
        rsi = talib.RSI(
            close, timeperiod=self.cfg.factor_param("rsi_timeperiod")
        ).tolist()[-1]
        ma_fast = talib.MA(
            close, timeperiod=self.cfg.factor_param("ma_fast_timeperiod")
        ).tolist()[-1]
        ma_slow = talib.MA(
            close, timeperiod=self.cfg.factor_param("ma_slow_timeperiod")
        ).tolist()[-1]
        self.logger.debug(f"rsi:{rsi:.2f}, fast:{ma_fast:.6f}, slow:{ma_slow:.6f}")
        return Factor(rsi, ma_fast, ma_slow)

    def _buy_condition(self, factor: Factor) -> bool:
        return factor.ma_slow > factor.ma_fast and factor.rsi < self.cfg.factor_param(
            "rsi_down"
        )

    def _sell_condition(self, factor: Factor) -> bool:
        return factor.ma_slow < factor.ma_fast and factor.rsi > self.cfg.factor_param(
            "rsi_up"
        )

    def run(self):
        last_buy_time = datetime.now()
        last_sell_time = datetime.now()
        buy_step = self.time_step
        sell_step = self.time_step

        while True:
            price = self.exec.price()
            factor = self._factor(price)
            if (
                self._buy_condition(factor)
                and (datetime.now() - last_buy_time).seconds > buy_step
            ):
                self.exec.buy()
                self.logger.info(f"<触发买入>")
            elif (
                self._sell_condition(factor)
                and (datetime.now() - last_sell_time).seconds > sell_step
            ):
                self.exec.sell()
                self.logger.info(f"<触发卖出>")
            self.exec.sleep(self.cfg.trade_timeperiod())
