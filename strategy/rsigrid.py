import talib
import pandas as pd
from strategy.factor import Factor

from core.cfg import Config
from core.execute import Execute


class RSIGrid:
    def __init__(self, execution: Execute, cfg: Config):
        self.exec = execution
        self.cfg = cfg
        self.logger = cfg.logger

        # 买入触发间隔
        self.time_step = 5 * 60
        self.last_buy_time = self.exec.now()
        self.last_sell_time = self.exec.now()
        self.buy_step = self.time_step
        self.sell_step = self.time_step

    def _factor(self, price: pd.DataFrame) -> Factor:
        price["Mid"] = (price["Close"] + price["Open"]) / 2
        price["RSI"] = talib.RSI(price["Mid"], timeperiod=self.cfg.factor_int_param("rsi_timeperiod"))
        price["MA_FAST"] = talib.SMA(price["Mid"], timeperiod=self.cfg.factor_int_param("ma_fast_timeperiod"))
        price["MA_SLOW"] = talib.SMA(price["Mid"], timeperiod=self.cfg.factor_int_param("ma_slow_timeperiod"))

        rsi = price["RSI"].to_numpy()
        ma_fast = price["MA_FAST"].to_numpy()
        ma_slow = price["MA_SLOW"].to_numpy()
        self.logger.debug(f"rsi:{rsi[-1]:.2f}, fast:{ma_fast[-1]:.6f}, slow:{ma_slow[-1]:.6f}")
        return Factor(rsi, ma_fast, ma_slow)

    def _buy_condition(self, factor: Factor) -> bool:
        if (self.exec.now() - self.last_buy_time).seconds < self.buy_step:
            return False
        rsi_last = factor.rsi[-1]
        ma_fast_last = factor.ma_fast[-1]
        ma_slow_last = factor.ma_slow[-1]

        condition = ma_slow_last > ma_fast_last and rsi_last < self.cfg.factor_int_param("rsi_down")
        return condition

    def _sell_condition(self, factor: Factor) -> bool:
        if (self.exec.now() - self.last_sell_time).seconds < self.sell_step:
            return False
        rsi_last = factor.rsi[-1]
        ma_fast_last = factor.ma_fast[-1]
        ma_slow_last = factor.ma_slow[-1]

        condition = ma_slow_last < ma_fast_last and rsi_last > self.cfg.factor_int_param("rsi_up")
        return condition

    def run(self):

        while True:
            if hasattr(self.exec, "_factor"):
                """仿真模式"""
                factor = self.exec._factor(None)
            else:
                price = self.exec.price()
                factor = self._factor(price)

            if self._buy_condition(factor):
                self.exec.buy()
                self.buy_step *= 2
                self.last_buy_time = self.exec.now()
                self.sell_step = self.time_step
            elif self._sell_condition(factor):
                self.exec.sell()
                self.sell_step *= 2
                self.last_sell_time = self.exec.now()
                self.buy_step = self.time_step
            self.exec.sleep(self.cfg.trade_config.trade_timeperiod)

            if self.exec.stop():
                return
