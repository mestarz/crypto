import talib
import numpy as np
from matplotlib import gridspec
import matplotlib.pyplot as plt

from datetime import datetime, timedelta
from abc import ABC, abstractmethod

from core.execute import Execute
from strategy.factor import Factor
from core.cfg import Config


def show_simulation_result(kline_data, buy_points, sell_points, rsi_data):
    """展示仿真结果"""
    try:
        if kline_data is None or len(kline_data) < 2:
            raise ValueError("K线数据不足，无法绘制图表")
        if rsi_data is None or len(rsi_data) < 2:
            raise ValueError("RSI数据不足，无法绘制图表")

        plt.figure(figsize=(12, 8))
        gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])

        # 价格图表
        ax1 = plt.subplot(gs[0])
        ax1.set_title("Simulation Price Chart")
        ax1.plot(kline_data, label="Price")

        # 绘制买卖点
        if buy_points is not None and len(buy_points) > 0:
            ax1.scatter(buy_points, kline_data[buy_points], marker="^", color="g", label="Buy", s=200)
        if sell_points is not None and len(sell_points) > 0:
            ax1.scatter(sell_points, kline_data[sell_points], marker="v", color="r", label="Sell", s=200)
        ax1.legend()

        # RSI图表
        ax2 = plt.subplot(gs[1])
        ax2.set_title("RSI")
        ax2.plot(rsi_data, label="RSI", color="orange")
        ax2.axhline(70, color="red", linestyle="--")
        ax2.axhline(30, color="green", linestyle="--")
        ax2.legend()

        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"展示仿真结果时出错: {str(e)}")
        plt.close()


class TraceExec(Execute, ABC):
    def __init__(self, cfg: Config):
        self.buy_history: list[int] = []
        self.sell_history: list[int] = []
        self.price_history: list[float] = []

        self.cfg = cfg
        self.work_time = 0
        self.stop_time = 500 * 60
        self.max_buy_chance = cfg.trade_config.max_buy_chance

        self.init_price()

        self.rsi = talib.RSI(np.array(self.price_history), timeperiod=cfg.factor_config.rsi_timeperiod)
        self.fast = talib.SMA(np.array(self.price_history), timeperiod=cfg.factor_config.ma_fast_timeperiod)
        self.slow = talib.SMA(np.array(self.price_history), timeperiod=cfg.factor_config.ma_slow_timeperiod)

        self.sleep(20 * 60)
        self.start_time = datetime.now()  # 添加开始时间

    @abstractmethod
    def init_price():
        pass

    def sleep(self, seconds: int):
        """模拟时间延迟"""
        self.work_time += seconds

    def now(self) -> datetime:
        """返回当前模拟时间"""
        return self.start_time + timedelta(seconds=self.work_time)

    def stop(self) -> bool:
        return self.work_time >= self.stop_time

    def price():
        # NOTHINE TO DO
        # use _factor
        pass

    def _factor(self, _) -> Factor:
        return Factor(
            self.rsi[: int(self.work_time / 60)],
            self.fast[: int(self.work_time / 60)],
            self.slow[: int(self.work_time / 60)],
        )

    def buy(self):
        """执行买入操作"""
        if self.max_buy_chance <= 0:
            return
        self.buy_history.append(int(self.work_time / 60))
        self.max_buy_chance -= 1

    def sell(self):
        """执行卖出操作"""
        if self.max_buy_chance == self.cfg.trade_config.max_buy_chance:
            return
        self.sell_history.append(int(self.work_time / 60))
        self.max_buy_chance += 1

    def display(self):
        """显示回测结果"""
        kline_data = np.array(self.price_history)
        rsi_data = self.rsi
        rsi_data[np.isnan(rsi_data)] = 50

        buy_timestamps = np.array(self.buy_history)
        sell_timestamps = np.array(self.sell_history)

        show_simulation_result(
            kline_data=kline_data, buy_points=buy_timestamps, sell_points=sell_timestamps, rsi_data=rsi_data
        )
