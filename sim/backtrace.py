import pandas as pd

from sim.trace import TraceExec
from strategy.rsigrid import RSIGrid
from core.cfg import Config


class BackTrace(TraceExec):
    def init_price_history(self):
        """初始化价格数据"""
        self.price_history = self._get_okx_data(self.stop_time // 60 + 10)

    def _get_okx_data(self, nums: int) -> list[float]:
        r = self.cfg.marketAPI.get_mark_price_candlesticks(
            instId=self.cfg.trade_config.coin, bar=self.cfg.trade_config.period, limit=nums
        )["data"][::-1]
        timestamp = r[0][0]
        count = nums - len(r)
        while count > 0:
            limit = 100 if count > 100 else count
            count -= limit
            r = (
                self.cfg.marketAPI.get_mark_price_candlesticks(
                    instId=self.cfg.trade_config.coin,
                    bar=self.cfg.trade_config.period,
                    after=timestamp,
                    limit=limit,
                )["data"][::-1]
                + r
            )
            timestamp = r[0][0]

        df = pd.DataFrame(r, columns=["ts", "Open", "High", "Low", "Close", "isOver"])
        return [float(i) for i in df["Close"].tolist()]


if __name__ == "__main__":
    cfg = Config("simulation.ini")
    cfg.factor_config.ma_fast_timeperiod = 20
    cfg.factor_config.ma_slow_timeperiod = 200
    backtrace = BackTrace(cfg=cfg, times=1000)
    strategy = RSIGrid(backtrace, cfg=cfg)
    strategy.run()
    backtrace.display()
