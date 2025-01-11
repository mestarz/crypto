from abc import ABC
from core.cfg import Config
import numpy as np
from strategy.rsigrid import RSIGrid
import talib
from strategy.factor import Factor
from datetime import datetime, timedelta

from core.execute import Execute
from sim.display import show_simulation_result


class SimulationExec(Execute, ABC):
    def __init__(self, cfg: Config):
        self.buy_history: list[int] = []
        self.sell_history: list[int] = []
        self.price_history: list[int] = []
        self.logger = cfg.logger
        self.logger.disabled = True
        self.cfg = cfg
        self.max_buy_chance = cfg.trade_config.max_buy_chance

        # 模拟工作时间
        self.work_time = 0
        # 停止时间
        self.stop_time = 500 * 60
        self._init_random_price()

        self.rsi = talib.RSI(np.array(self.price_history), timeperiod=cfg.factor_config.rsi_timeperiod)
        self.fast = talib.SMA(np.array(self.price_history), timeperiod=cfg.factor_config.ma_fast_timeperiod)
        self.slow = talib.SMA(np.array(self.price_history), timeperiod=cfg.factor_config.ma_slow_timeperiod)

        self.sleep(20 * 60)
        self.start_time = datetime.now()  # 添加开始时间

    def sleep(self, seconds: int):
        """模拟时间延迟"""
        self.work_time += seconds

    def now(self) -> datetime:
        """返回当前模拟时间"""
        return self.start_time + timedelta(seconds=self.work_time)

    def stop(self):
        """停止执行"""
        return self.work_time >= self.stop_time

    def _init_random_price(self):
        current_price = 100
        # 生成正态分布的随机数，均值0，标准差0.0333，限制在[-0.1, 0.1]范围内
        for _ in range(int(self.stop_time / 60) + 10):
            random_factor = np.clip(np.random.normal(0, 0.00333), -0.01, 0.01)
            current_price = current_price * (1 + random_factor)
            self.price_history.append(current_price)

    def _factor(self, _) -> Factor:
        return Factor(
            self.rsi[: int(self.work_time / 60)],
            self.fast[: int(self.work_time / 60)],
            self.slow[: int(self.work_time / 60)],
        )

    def price(self) -> np.ndarray:
        """将price_history从秒压缩到1分钟, 并返回"""
        self.logger.info(f"{self.work_time}秒: 当前价格{self.price_history[self.work_time]:.2f}")
        return np.array(self.price_history[: int(self.work_time / 60)])

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


if __name__ == "__main__":
    cfg = Config("simulation.ini")
    sim = SimulationExec(cfg=cfg)
    strategy = RSIGrid(sim, cfg=cfg)
    strategy.run()

    # 获取K线数据（每分钟价格）
    kline_data = np.array(sim.price_history)
    # 获取RSI数据
    rsi_data = talib.RSI(np.array(kline_data), timeperiod=cfg.factor_config.rsi_timeperiod)
    # 替换掉nan
    rsi_data[np.isnan(rsi_data)] = 50

    # 获取买卖点时间戳
    buy_timestamps = np.array(sim.buy_history)
    sell_timestamps = np.array(sim.sell_history)

    show_simulation_result(
        kline_data=kline_data, buy_points=buy_timestamps, sell_points=sell_timestamps, rsi_data=rsi_data
    )
