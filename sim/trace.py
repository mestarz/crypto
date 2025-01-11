import talib
import numpy as np
from matplotlib import gridspec
import matplotlib.pyplot as plt

from datetime import datetime, timedelta
from abc import ABC, abstractmethod

from core.execute import Execute
from strategy.factor import Factor
from core.cfg import Config


class SimulationPlotter:
    def __init__(self, kline_data, buy_points, sell_points, rsi_data):
        self.kline_data = kline_data
        self.buy_points = buy_points
        self.sell_points = sell_points
        self.rsi_data = rsi_data

    def show(self):
        self.validate_data()
        self.ax1, self.ax2 = self.setup_figure()

        self.plot_price_chart()
        self.plot_rsi_chart()

        self.vert_line1, self.vert_line2, self.annotation = self.add_interactive_elements()

        plt.connect("motion_notify_event", self.on_mouse_move)
        plt.tight_layout()
        plt.show()

    def validate_data(self):
        if (self.kline_data is None or len(self.kline_data) < 2) or (
            self.rsi_data is None or len(self.rsi_data) < 2
        ):
            raise ValueError("数据不足，无法绘制图表")

    def setup_figure(self):
        plt.figure(figsize=(12, 8))
        gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])
        ax1 = plt.subplot(gs[0])
        ax2 = plt.subplot(gs[1])
        return ax1, ax2

    def plot_price_chart(self):
        self.ax1.set_title("Simulation Price Chart")
        self.ax1.plot(self.kline_data, label="Price")
        if self.buy_points is not None and len(self.buy_points) > 0:
            self.ax1.scatter(
                self.buy_points, self.kline_data[self.buy_points], marker="^", color="g", label="Buy", s=200
            )
        if self.sell_points is not None and len(self.sell_points) > 0:
            self.ax1.scatter(
                self.sell_points,
                self.kline_data[self.sell_points],
                marker="v",
                color="r",
                label="Sell",
                s=200,
            )
        self.ax1.legend()

    def plot_rsi_chart(self):
        self.ax2.set_title("RSI")
        self.ax2.plot(self.rsi_data, label="RSI", color="orange")
        self.ax2.axhline(70, color="red", linestyle="--")
        self.ax2.axhline(30, color="green", linestyle="--")
        self.ax2.legend()

    def add_interactive_elements(self):
        vert_line1 = self.ax1.axvline(color="k", linestyle="--")
        vert_line2 = self.ax2.axvline(color="k", linestyle="--")
        annotation = self.ax1.annotate(
            "",
            xy=(0, 0),
            xytext=(15, 15),
            textcoords="offset points",
            fontsize=12,
            bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.5),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
        )
        annotation.set_visible(False)
        return vert_line1, vert_line2, annotation

    def on_mouse_move(self, event):
        if event.inaxes in [self.ax1, self.ax2]:
            self.vert_line1.set_xdata([event.xdata])
            self.vert_line2.set_xdata([event.xdata])
            index = int(event.xdata)
            if 0 <= index < len(self.kline_data):
                price = self.kline_data[index]
                rsi = self.rsi_data[index]
                self.annotation.xy = (event.xdata, price)
                self.annotation.set_text(f"Price: {price:.2f}\nRSI: {rsi:.2f}")
                self.annotation.set_visible(True)
            plt.draw()


class TraceExec(Execute, ABC):
    def __init__(self, cfg: Config):
        self.buy_history = []
        self.sell_history = []
        self.price_history = []

        self.balance = 5000
        self.position = 0
        self.assert_price_history = [5000]

        self.cfg = cfg
        self.work_time = 0
        self.stop_time = 500 * 60
        self.buy_chance = cfg.trade_config.max_buy_chance

        self.init_price_history()
        self.initialize_indicators(cfg)

        self.sleep(20 * 60)
        self.start_time = datetime.now()

    @abstractmethod
    def init_price_history(self):
        pass

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
            self.assert_price_history.append(self.balance + self.position * self.price_history[self._time()])

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
        self.buy_history.append(self._time())
        buy_count = int((self.balance / self.buy_chance) / self.price_history[self._time()])
        self.position += buy_count
        self.balance -= buy_count * self.price_history[self._time()]
        self.buy_chance -= 1

    def sell(self):
        """执行卖出操作"""
        if self.buy_chance == self.cfg.trade_config.max_buy_chance:
            return
        self.sell_history.append(self._time())
        sell_count = int(self.position / (self.cfg.trade_config.max_buy_chance - self.buy_chance))
        self.position -= sell_count
        self.balance += sell_count * self.price_history[self._time()]
        self.buy_chance += 1

    def display(self):
        """显示回测结果"""
        kline_data = np.array(self.price_history)
        rsi_data = self.rsi
        rsi_data[np.isnan(rsi_data)] = 50

        buy_timestamps = np.array(self.buy_history)
        sell_timestamps = np.array(self.sell_history)

        plotter = SimulationPlotter(
            kline_data=kline_data, buy_points=buy_timestamps, sell_points=sell_timestamps, rsi_data=rsi_data
        )
        plotter.show()
