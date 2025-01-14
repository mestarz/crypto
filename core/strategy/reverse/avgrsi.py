import talib

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

        self.state = "empty"

    def run(self):
        while True:
            price = self.exec.price(nums=300)["Close"].to_numpy()
            slow = talib.SMA(price, timeperiod=200)

            # 根据慢线判断仓位方向
            if (
                (slow[-1] - slow[-5]) > (slow[-5] - slow[-10])
                and slow[-1] > slow[-5]
                and self.state == "empty"
            ):
                """多头加速"""
                self._buy_up()
            elif (
                (slow[-1] - slow[-5]) < (slow[-5] - slow[-10])
                and slow[-1] < slow[-5]
                and self.state == "empty"
            ):
                """空头加速"""
                self._buy_down()
            elif self.state == "long" and ((slow[-1] - slow[-5]) < (slow[-5] - slow[-10])):
                """多头减速"""
                self._sell_up()
            elif self.state == "short" and ((slow[-1] - slow[-5]) > (slow[-5] - slow[-10])):
                """空头减速"""
                self._sell_down()

            self.exec.sleep(5)

    def _buy_up(self):
        self.exec.clear_short()

        while True:
            price = self.exec.price(nums=300)["Close"].to_numpy()
            slow = talib.SMA(price, timeperiod=200)
            rebuild_price = (price - slow) + price[0]
            fast_rebuild = talib.SMA(rebuild_price, timeperiod=20)
            rsi_rebuild = talib.RSI(fast_rebuild, timeperiod=14)

            if rsi_rebuild[-1] < 20:
                if slow[-1] < slow[-5]:
                    return
                self.exec.clear_long()
                self.exec.set_long_position(1)
                self.state = "long"
                break

            self.exec.sleep(5)

    def _sell_up(self):
        while True:
            price = self.exec.price(nums=300)["Close"].to_numpy()
            slow = talib.SMA(price, timeperiod=200)
            rebuild_price = (price - slow) + price[0]
            fast_rebuild = talib.SMA(rebuild_price, timeperiod=20)
            rsi_rebuild = talib.RSI(fast_rebuild, timeperiod=14)

            if rsi_rebuild[-1] > 70:
                if slow[-1] > slow[-5]:
                    return
                self.exec.clear_long()
                self.state = "empty"
                break

            self.exec.sleep(5)

    def _buy_down(self):
        self.exec.clear_long()

        while True:
            price = self.exec.price(nums=300)["Close"].to_numpy()
            slow = talib.SMA(price, timeperiod=200)
            rebuild_price = (price - slow) + price[0]
            fast_rebuild = talib.SMA(rebuild_price, timeperiod=20)
            rsi_rebuild = talib.RSI(fast_rebuild, timeperiod=14)

            if rsi_rebuild[-1] > 80:
                self.exec.clear_short()
                self.exec.set_short_position(1)
                self.state = "short"
                break

            self.exec.sleep(5)

    def _sell_down(self):
        while True:
            price = self.exec.price(nums=300)["Close"].to_numpy()
            slow = talib.SMA(price, timeperiod=200)
            rebuild_price = (price - slow) + price[0]
            fast_rebuild = talib.SMA(rebuild_price, timeperiod=20)
            rsi_rebuild = talib.RSI(fast_rebuild, timeperiod=14)

            if rsi_rebuild[-1] < 30:
                self.exec.clear_short()
                self.state = "empty"
                break

            self.exec.sleep(5)
