import pandas as pd

from core.trace.base import TraceExec


class BackTrace(TraceExec):
    def init_price_history(self):
        """初始化价格数据"""
        self.price_history = self._get_okx_data(self.stop_time // 60 + 10)

    def _get_okx_data(self, nums: int) -> list[float]:
        result = self.cfg.api.get_more_data(
            instId=self.cfg.trade_config.coin, bar=self.cfg.trade_config.period, nums=nums
        )["Close"].tolist()
        return [float(i) for i in result]
