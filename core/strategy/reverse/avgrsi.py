import talib
import numpy as np

from core.execute import Execute
from core.cfg import Config


class AvgRSI:
    def __init__(self, execution: Execute, cfg: Config):
        self.exec = execution
        self.cfg = cfg

        self.lever = 10
        self.rsi_up = 70
        self.rsi_down = 30

        self.ct_val = self.cfg.api.ct_val(self.cfg.trade_config.coin)
        self.cfg.api.set_leverage(self.cfg.trade_config.coin, self.lever, "cross")
        self.current_price = 0

    def run(self):
        while True:
            price = self.exec.price(nums=300)["Close"].to_numpy()
            self.current_price = price[-1]
            slow = talib.SMA(price, timeperiod=200)
            rebuild_price = (price - slow) + price[0]
            fast_rebuild = talib.SMA(rebuild_price, timeperiod=20)
            rsi_rebuild = talib.RSI(fast_rebuild, timeperiod=14)

            self.cfg.logger.debug(f"当前价格: {self.current_price}")

            # 根据慢线判断仓位方向
            if slow[-1] > slow[-10]:
                self._run_up(rsi_rebuild)
            else:
                self._run_down(rsi_rebuild)

            self.exec.sleep(10)

    def _run_up(self, rsi_list: np.array):
        """趋势作多"""
        self.exec.clear_short()
        rsi = rsi_list[-1]
        self.cfg.logger.debug(f"RSI (多头): {rsi}")
        if rsi < 0 or rsi > 100:
            raise ValueError("RSI值异常")
        if rsi < self.rsi_down:
            """加仓区间"""
            min_position = 0.5 + ((self.rsi_down - rsi) / self.rsi_down) * 0.5
            real_position = self._get_long_position()
            self.cfg.logger.debug(
                f"加仓区间 - 最小仓位 (多头): {min_position:.4f}, 实际仓位: {real_position:.4f}"
            )
            if real_position < min_position:
                self.exec.set_long_position(min_position)
        elif rsi > self.rsi_up:
            """减仓区间"""
            max_position = 0.1 - ((rsi - self.rsi_up) / (100 - self.rsi_up)) * 0.1
            real_position = self._get_long_position()
            self.cfg.logger.debug(
                f"减仓区间 - 最大仓位 (多头): {max_position:.4f}, 实际仓位: {real_position:.4f}"
            )
            if real_position > max_position:
                self.exec.set_long_position(max_position)

    def _run_down(self, rsi_list: np.array):
        """趋势作空"""
        self.exec.clear_long()
        rsi = rsi_list[-1]
        self.cfg.logger.debug(f"RSI (空头): {rsi}")
        if rsi < 0 or rsi > 100:
            raise ValueError("RSI值异常")
        if rsi > self.rsi_up:
            """加仓区间"""
            min_position = 0.5 + ((rsi - self.rsi_up) / (100 - self.rsi_up)) * 0.5
            real_position = self._get_short_position()
            self.cfg.logger.debug(
                f"加仓区间 - 最小仓位 (空头): {min_position:.4f}, 实际仓位: {real_position:.4f}"
            )
            if real_position < min_position:
                self.exec.set_short_position(min_position)
        elif rsi < self.rsi_down:
            """减仓区间"""
            max_position = 0.1 - ((self.rsi_down - rsi) / self.rsi_down) * 0.1
            real_position = self._get_short_position()
            self.cfg.logger.debug(
                f"减仓区间 - 最大仓位 (空头): {max_position:.4f}, 实际仓位: {real_position:.4f}"
            )
            if real_position > max_position:
                self.exec.set_short_position(max_position)

    def _get_long_position(self) -> float:
        long, short = self.cfg.api.get_position_size_long_and_short(self.cfg.trade_config.coin)
        balance = self.cfg.api.get_account_balance(self.cfg.trade_config.ccy)
        if short > long:
            return 0
        value = self.ct_val * (long - short) * self.current_price / self.lever
        all_value = balance + self.ct_val * (long + short) * self.current_price / self.lever
        return value / all_value

    def _get_short_position(self) -> float:
        long, short = self.cfg.api.get_position_size_long_and_short(self.cfg.trade_config.coin)
        balance = self.cfg.api.get_account_balance(self.cfg.trade_config.ccy)
        if long > short:
            return 0
        value = self.ct_val * (short - long) * self.current_price / self.lever
        all_value = balance + self.ct_val * (long + short) * self.current_price / self.lever
        return value / all_value
