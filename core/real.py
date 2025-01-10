import pandas as pd
import random
from abc import ABC
from time import sleep
from datetime import datetime

from core.cfg import Config
from core.execute import Execute
from api.api_service import APIService


class BaseExecute(Execute, ABC):
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.logger = self.cfg.logger
        self.api = APIService(
            self.cfg.accountAPI, self.cfg.marketAPI, self.cfg.tradeAPI, self.cfg.publicDataAPI
        )
        self._init_leverage()
        self._init_contract_params()

    def _init_leverage(self):
        """初始化杠杆设置"""
        self.real_lever = 20
        self.api.set_leverage(instId=self.cfg.trade_config.coin, lever=f"{self.real_lever}", mgnMode="cross")

    def _init_contract_params(self):
        """初始化合约参数"""
        self.ct_val = self.api.ct_val(self.cfg.trade_config.coin)
        self.lever = self.cfg.trade_config.lever
        self.buy_chance = self.cfg.trade_config.max_buy_chance


class OKXExecute(BaseExecute):

    def sleep(self, time: int):
        """休眠指定时间"""
        sleep(time)

    def now(self) -> datetime:
        return datetime.now()

    def price(self) -> pd.DataFrame:
        """获取市场价格数据"""
        raw_data = self.api.get_mark_price_candlesticks(
            instId=self.cfg.trade_config.coin, bar=self.cfg.trade_config.period
        )
        return self._format_price_data(raw_data)

    def stop(self) -> bool:
        return False

    def _format_price_data(self, raw_data: list) -> pd.DataFrame:
        """格式化价格数据"""
        df = pd.DataFrame(raw_data, columns=["ts", "Open", "High", "Low", "Close", "isOver"])
        df["ts"] = pd.to_datetime(df["ts"].astype(float), unit="ms", errors="coerce")
        df = df.astype(
            {
                "Open": float,
                "High": float,
                "Low": float,
                "Close": float,
                "isOver": int,
            }
        )
        df.set_index("ts", inplace=True)
        return df

    def buy(self):
        """执行买入操作"""
        if self.buy_chance <= 0:
            self.logger.info("没有买入次数了，不触发买入")
            return

        buy_count = self._calculate_buy_count()
        self._log_buy_info(buy_count)
        self._execute_buy(buy_count)
        self.buy_chance -= 1

    def _calculate_buy_count(self) -> int:
        """计算买入数量"""
        funds = self._get_available_funds_with_lever() / self.buy_chance
        now_price = self._get_tag_price()
        return int(funds / (now_price * self.ct_val)) * self.real_lever

    def _log_buy_info(self, buy_count: int):
        """记录买入日志"""
        now_price = self._get_tag_price()
        self.logger.info(f"触发买入: 数量={buy_count}, 价格={now_price}, 剩余买入次数={self.buy_chance}")

    def _execute_buy(self, buy_count: int):
        """执行买入操作"""
        self._long_buy(buy_count)

    def sell(self):
        """执行卖出操作"""
        if self.buy_chance == self.cfg.trade_config.max_buy_chance:
            self.logger.info("没有过买入，不触发卖出")
            return

        sell_count = self._calculate_sell_count()
        self._log_sell_info(sell_count)
        self._execute_sell(sell_count)

    def _calculate_sell_count(self) -> int:
        """计算卖出数量"""
        return int(self._get_position() / (self.cfg.trade_config.max_buy_chance - self.buy_chance))

    def _log_sell_info(self, sell_count: int):
        """记录卖出日志"""
        now_price = self._get_tag_price()
        self.logger.info(f"触发卖出: 数量={sell_count}, 价格={now_price}, 剩余买入次数={self.buy_chance}")

    def _execute_sell(self, sell_count: int):
        """执行卖出操作"""
        self._long_sell(sell_count)

    def _get_available_funds_with_lever(self) -> float:
        """
        获取计算杠杆后实际剩余可用资金
        :return:
        """
        balance = self._get_balance() - self.cfg.trade_config.reserved
        imr = self._get_imr()
        avail_funds = (self.lever / self.real_lever) * (balance + imr) - imr
        if avail_funds < 0:
            avail_funds = 0
        return avail_funds

    def _get_tag_price(self) -> float:
        """
        获取标记价格
        :return:
        """
        return self.api.get_mark_price(instType="SWAP", instId=self.cfg.trade_config.coin)

    def _long_buy(self, size: int):
        """
        批量限价单买入，将大单拆分为多个小单
        每个小单的价格在标记价格的98%-99%之间波动
        :return:
        """
        mark_price = self._get_tag_price()
        min_price = round(mark_price * 0.98, 2)  # 最低价格
        max_price = round(mark_price * 0.99, 2)  # 最高价格

        # 准备批量订单
        orders = []
        batch_size = 5
        order_size = size // batch_size
        remaining_size = size % batch_size

        for i in range(batch_size):
            price = round(min_price + (max_price - min_price) * random.random(), 2)
            orders.append(
                {
                    "instId": self.cfg.trade_config.coin,
                    "tdMode": "cross",
                    "clOrdId": f"batch_{i}",
                    "ccy": "USDT",
                    "side": "buy",
                    "posSide": "long",
                    "ordType": "limit",
                    "px": f"{price}",
                    "sz": f"{order_size}",
                }
            )

        if remaining_size > 0:
            orders.append(
                {
                    "instId": self.cfg.trade_config.coin,
                    "tdMode": "cross",
                    "clOrdId": "batch_remain",
                    "ccy": "USDT",
                    "side": "buy",
                    "posSide": "long",
                    "ordType": "limit",
                    "px": f"{max_price}",
                    "sz": f"{remaining_size}",
                }
            )

        return self.api.place_multiple_orders(orders)

    def _long_sell(self, size: int):
        """
        批量限价单卖出，将大单拆分为多个小单
        每个小单的价格在标记价格的101%-102%之间波动
        :return:
        """
        mark_price = self._get_tag_price()
        min_price = round(mark_price * 1.01, 2)  # 最低价格
        max_price = round(mark_price * 1.02, 2)  # 最高价格

        # 准备批量订单
        orders = []
        batch_size = 5
        order_size = size // batch_size
        remaining_size = size % batch_size

        for i in range(batch_size):
            price = round(min_price + (max_price - min_price) * random.random(), 2)
            orders.append(
                {
                    "instId": self.cfg.trade_config.coin,
                    "tdMode": "cross",
                    "clOrdId": f"batch_{i}",
                    "ccy": "USDT",
                    "side": "sell",
                    "posSide": "long",
                    "ordType": "limit",
                    "px": f"{price}",
                    "sz": f"{order_size}",
                }
            )

        if remaining_size > 0:
            orders.append(
                {
                    "instId": self.cfg.trade_config.coin,
                    "tdMode": "cross",
                    "clOrdId": "batch_remain",
                    "ccy": "USDT",
                    "side": "sell",
                    "posSide": "long",
                    "ordType": "limit",
                    "px": f"{max_price}",
                    "sz": f"{remaining_size}",
                }
            )

        return self.api.place_multiple_orders(orders)

    def _get_balance(self) -> float:
        """
        获取当前剩余资金
        :return:
        """
        return self.api.get_account_balance(ccy=self.cfg.ccy())

    def _get_position(self) -> float:
        """
        获取当前仓位
        :return:
        """
        return self.api.get_positions(instId=self.cfg.trade_config.coin)

    def _get_imr(self) -> float:
        """
        获取保证金
        :return:
        """
        return self.api.get_imr(instId=self.cfg.trade_config.coin)
