import talib
import numpy as np
from matplotlib import gridspec
import matplotlib.pyplot as plt
import time  # 添加time模块

from datetime import datetime, timedelta
from abc import ABC, abstractmethod

from core.execute import Execute
from strategy.factor import Factor
from core.cfg import Config


class SimulationPlotter:
    def __init__(self, kline_data, buy_points, sell_points, rsi_data, assert_price_history):
        self.kline_data = kline_data
        self.buy_points = buy_points
        self.sell_points = sell_points
        self.rsi_data = rsi_data
        self.assert_price_history = assert_price_history
        self.background = None
        self.last_time = time.time()  # 使用time.time()初始化
        self.throttle_interval = 1/30  # 限制更新频率为30fps
        self.resizing = False  # 添加重绘标志

    def show(self):
        self.validate_data()
        self.ax1, self.ax2, self.ax3 = self.setup_figure()

        self.plot_price_chart()
        self.plot_rsi_chart()
        self.plot_assert_price_chart()

        self.vert_line1, self.vert_line2, self.vert_line3, self.annotation = self.add_interactive_elements()
        
        # 修改显示逻辑
        self.fig = plt.gcf()
        plt.tight_layout()
        
        # 连接事件
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.fig.canvas.mpl_connect('resize_event', self.on_resize)
        
        # 初始化绘图
        self.update_background()
        plt.show()

    def validate_data(self):
        if (
            (self.kline_data is None or len(self.kline_data) < 2)
            or (self.rsi_data is None or len(self.rsi_data) < 2)
            or (self.assert_price_history is None or len(self.assert_price_history) < 2)
        ):
            raise ValueError("数据不足，无法绘制图表")

    def setup_figure(self):
        plt.figure(figsize=(12, 10))
        gs = gridspec.GridSpec(3, 1, height_ratios=[3, 1, 1])
        ax1 = plt.subplot(gs[0])
        ax2 = plt.subplot(gs[1])
        ax3 = plt.subplot(gs[2])
        return ax1, ax2, ax3

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

    def plot_assert_price_chart(self):
        self.ax3.set_title("Assert Price History")
        self.ax3.plot(self.assert_price_history, label="Assert Price", color="blue")
        self.ax3.legend()

    def add_interactive_elements(self):
        # 创建更高效的线条对象
        vert_line1 = self.ax1.axvline(x=0, color="k", linestyle="--", animated=True)
        vert_line2 = self.ax2.axvline(x=0, color="k", linestyle="--", animated=True)
        vert_line3 = self.ax3.axvline(x=0, color="k", linestyle="--", animated=True)
        
        annotation = self.ax1.annotate(
            "",
            xy=(0, 0),
            xytext=(15, 15),
            textcoords="offset points",
            fontsize=12,
            bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.5),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"),
            animated=True
        )
        return vert_line1, vert_line2, vert_line3, annotation

    def update_background(self):
        """更新背景缓存"""
        self.fig.canvas.draw()
        self.background = self.fig.canvas.copy_from_bbox(self.fig.bbox)
        # 隐藏动态元素
        self.vert_line1.set_visible(False)
        self.vert_line2.set_visible(False)
        self.vert_line3.set_visible(False)
        self.annotation.set_visible(False)

    def on_resize(self, event):
        """处理窗口大小改变事件"""
        self.resizing = True
        self.update_background()
        self.resizing = False

    def on_mouse_move(self, event):
        if event.inaxes in [self.ax1, self.ax2, self.ax3] and not self.resizing:
            current_time = time.time()
            
            if current_time - self.last_time < self.throttle_interval:
                return
            
            try:
                index = int(event.xdata)
                if 0 <= index < len(self.kline_data):
                    self.last_time = current_time
                    
                    # 确保背景是最新的
                    if self.background is None:
                        self.update_background()
                    
                    # 恢复背景
                    self.fig.canvas.restore_region(self.background)
                    
                    # 更新竖线
                    for line in [self.vert_line1, self.vert_line2, self.vert_line3]:
                        line.set_xdata([index])
                        line.set_visible(True)
                        ax = line.axes
                        ax.draw_artist(line)
                    
                    # 更新标注
                    price = self.kline_data[index]
                    rsi = self.rsi_data[index]
                    assert_price = self.assert_price_history[index]
                    
                    self.annotation.xy = (index, price)
                    self.annotation.set_text(
                        f"Price: {price:.2f}\nRSI: {rsi:.2f}\nAssert Price: {assert_price:.2f}"
                    )
                    self.annotation.set_visible(True)
                    self.ax1.draw_artist(self.annotation)
                    
                    # 刷新画布
                    self.fig.canvas.blit(self.fig.bbox)

            except Exception as e:
                print(f"Error in on_mouse_move: {e}")


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
            if self.work_time % 60 == 0:
                self.assert_price_history.append(
                    self.balance + self.position * self.price_history[self._time()]
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
        assert_price_history = np.array(self.assert_price_history)

        # 将kline_data、rsi_data、assert_price_history统一成长度相同的数组
        min_len = min(len(kline_data), len(rsi_data), len(assert_price_history))
        kline_data = kline_data[:min_len]
        rsi_data = rsi_data[:min_len]
        assert_price_history = assert_price_history[:min_len]

        plotter = SimulationPlotter(
            kline_data=kline_data,
            buy_points=buy_timestamps,
            sell_points=sell_timestamps,
            rsi_data=rsi_data,
            assert_price_history=assert_price_history,
        )
        plotter.show()
