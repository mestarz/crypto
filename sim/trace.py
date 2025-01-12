import talib
import numpy as np


from datetime import datetime, timedelta
from abc import ABC, abstractmethod

from core.execute import Execute
from strategy.factor import Factor
from core.cfg import Config
from sim.plot.plotter import SimulationPlotter


class TraceExec(Execute, ABC):
    def __init__(self, cfg: Config, times: int = 500, balance: int = 5000):
        self.buy_history = []
        self.sell_history = []
        self.price_history = []

        self.balance = balance  # 资金
        self.position = 0  # 仓位
        self.debt = 0  # 合约负债
        self.commission = 0  # 手续费
        self.assert_price_history = [balance]

        self.cfg = cfg
        self.work_time = 0
        self.stop_time = times * 60
        self.buy_chance = cfg.trade_config.max_buy_chance

        self.init_price_history()
        self.init_baseline(balance=balance)
        self.initialize_indicators(cfg)

        self.sleep(20 * 60)
        self.start_time = datetime.now()

    @abstractmethod
    def init_price_history(self):
        pass

    def init_baseline(self, balance: int):
        self.baseline = []
        init_position = balance / self.price_history[0]
        for i in range(len(self.price_history)):
            self.baseline.append(init_position * self.price_history[i])

    def initialize_indicators(self, cfg):
        self.rsi = talib.RSI(np.array(self.price_history), timeperiod=cfg.factor_config.rsi_timeperiod)
        self.fast = talib.SMA(np.array(self.price_history), timeperiod=cfg.factor_config.ma_fast_timeperiod)
        self.slow = talib.SMA(np.array(self.price_history), timeperiod=cfg.factor_config.ma_slow_timeperiod)

    def _time(self) -> int:
        return self.work_time // 60

    def sleep(self, seconds: int):
        """模拟时间延迟"""
        for _ in range(seconds):
            self.work_time += 1
            if self.work_time % 60 == 0:
                self.assert_price_history.append(
                    self.balance
                    + self.position * self.price_history[self._time()]
                    - self.commission
                    - self.debt
                )

    def now(self) -> datetime:
        """返回当前模拟时间"""
        return self.start_time + timedelta(seconds=self.work_time)

    def stop(self) -> bool:
        return self.work_time >= self.stop_time

    def price(self):
        pass

    def _factor(self, _) -> Factor:
        return Factor(
            self.rsi[: self._time()],
            self.fast[: self._time()],
            self.slow[: self._time()],
        )

    def buy(self):
        """执行买入操作"""
        if self.buy_chance <= 0:
            return
        lever = self.cfg.trade_config.lever
        self.buy_history.append(self._time())
        buy_count = int((self.balance / self.buy_chance) / self.price_history[self._time()])
        self.position += buy_count * lever
        self.balance -= buy_count * self.price_history[self._time()]
        self.commission += lever * buy_count * self.price_history[self._time()] * 0.0005
        self.debt += buy_count * self.price_history[self._time()] * (lever - 1)
        self.buy_chance -= 1

    def sell(self):
        """执行卖出操作"""
        if self.buy_chance == self.cfg.trade_config.max_buy_chance:
            return
        lever = self.cfg.trade_config.lever
        self.sell_history.append(self._time())
        sell_count = int(self.position / (self.cfg.trade_config.max_buy_chance - self.buy_chance))
        self.position -= sell_count
        self.balance += sell_count * self.price_history[self._time()] / lever
        self.commission += sell_count * self.price_history[self._time()] * 0.0005
        self.debt -= sell_count * self.price_history[self._time()] * (lever - 1) / lever
        self.buy_chance += 1

    def display(self):
        """显示回测结果"""
        kline_data = np.array(self.price_history)
        rsi_data = self.rsi
        rsi_data[np.isnan(rsi_data)] = 50

        buy_timestamps = np.array(self.buy_history)
        sell_timestamps = np.array(self.sell_history)
        assert_price_history = np.array(self.assert_price_history)
        baseline = np.array(self.baseline)  # 添加基准数据
        fast = np.array(self.fast)  # 添加快均线数据
        slow = np.array(self.slow)  # 添加慢均线数据

        # 将数组统一长度
        min_len = min(
            len(kline_data), len(rsi_data), len(assert_price_history), len(baseline), len(fast), len(slow)
        )
        kline_data = kline_data[:min_len]
        rsi_data = rsi_data[:min_len]
        assert_price_history = assert_price_history[:min_len]
        baseline = baseline[:min_len]  # 截取基准数据
        fast = fast[:min_len]  # 截取快均线数据
        slow = slow[:min_len]  # 截取慢均线数据

        plotter = SimulationPlotter(
            kline_data=kline_data,
            buy_points=buy_timestamps,
            sell_points=sell_timestamps,
            rsi_data=rsi_data,
            assert_price_history=assert_price_history,
            baseline=baseline,  # 添加基准数据参数
            fast=fast,  # 添加快均线数据参数
            slow=slow,  # 添加慢均线数据参数
        )
        plotter.show()
