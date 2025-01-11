import pandas as pd
import random
from abc import ABC
from time import sleep
from datetime import datetime

from core.cfg import Config
from core.execute import Execute
from api.api_service import APIService


class RealExecute(Execute, ABC):
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

    def sleep(self, time: int):
        """休眠指定时间"""
        sleep(time)

    def now(self) -> datetime:
        return datetime.now()

    def stop(self) -> bool:
        return False


class OKXExecute(RealExecute):

    def price(self) -> pd.DataFrame:
        """获取市场价格数据"""
        raw_data = self.api.get_mark_price_candlesticks(
            instId=self.cfg.trade_config.coin, bar=self.cfg.trade_config.period
        )
        return self._format_price_data(raw_data)

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
        now_price = self._get_tag_price()
        self.buy_chance -= 1
        self.logger.info(f"触发买入: 预计数量={buy_count}, 价格={now_price}, 剩余买入次数={self.buy_chance}")
        remain_count = buy_count
        while remain_count > buy_count * 0.2:
            remain_count = self._long_buy(remain_count)
            self.logger.info(f"剩余数量={remain_count}")
            cprice = self._get_tag_price()
            if cprice > now_price:
                self.logger.info(f"当前价格{cprice}高于买入价格{now_price}，停止买入")
                break
        self.logger.info(f"买入完成: 实际数量={buy_count - remain_count}")

    def _calculate_buy_count(self) -> int:
        """计算买入数量"""
        funds = self._get_available_funds_with_lever() / self.buy_chance
        now_price = self._get_tag_price()
        return int(funds / (now_price * self.ct_val)) * self.real_lever

    def sell(self):
        """执行卖出操作"""
        if self.buy_chance == self.cfg.trade_config.max_buy_chance:
            self.logger.info("没有过买入，不触发卖出")
            return

        sell_count = self._calculate_sell_count()
        now_price = self._get_tag_price()
        self.buy_chance += 1
        self.logger.info(
            f"触发卖出: 预计卖出数量={sell_count}, 价格={now_price}, 剩余买入次数={self.buy_chance}"
        )
        remain_count = sell_count
        while remain_count > sell_count * 0.2:
            remain_count = self._long_sell(remain_count)
            self.logger.info(f"剩余数量={remain_count}")
            cprice = self._get_tag_price()
            if cprice < now_price:
                self.logger.info(f"当前价格{cprice}低于卖出价格{now_price}，停止卖出")
                break
        self.logger.info(f"卖出完成: 实际数量={sell_count - remain_count}")

    def _calculate_sell_count(self) -> int:
        """计算卖出数量"""
        return int(self._get_position() / (self.cfg.trade_config.max_buy_chance - self.buy_chance))

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
        :return:
        """
        mark_price = self._get_tag_price()
        min_price = mark_price * (1 - 0.005)
        max_price = mark_price
        split_size = 5

        # 在最低到最高价格区间随机采样5个数
        sampled_prices = [
            min_price + (max_price - min_price) * random.random() ** 2 for _ in range(split_size)
        ]

        # 将数量非均匀分割成5分
        sampled = [0.5 + random.random() for _ in range(split_size)]
        sampled_sizes = [int(size * sampled[i] / sum(sampled)) for i in range(split_size - 1)]
        sampled_sizes.append(size - sum(sampled_sizes))

        # 随机生成8位数字作为订单ID
        id_prefix = random.randint(10000000, 99999999)

        # 准备批量订单
        orders = [
            {
                "instId": self.cfg.trade_config.coin,
                "tdMode": "cross",
                "clOrdId": f"{id_prefix}buy{i}",
                "ccy": "USDT",
                "side": "buy",
                "posSide": "long",
                "ordType": "limit",
                "px": f"{sampled_prices[i]}",
                "sz": f"{sampled_sizes[i]}",
            }
            for i in range(5)
        ]

        self.api.place_multiple_orders(orders)
        sleep(self.cfg.trade_config.order_wait)
        self.api.cancel_orders(
            orders=[
                {"instId": self.cfg.trade_config.coin, "clOrdId": f"{id_prefix}buy{i}"}
                for i in range(split_size)
            ]
        )

        remain = 0
        for i in range(split_size):
            remain += self.api.get_order_unclosed_count(
                instid=self.cfg.trade_config.coin, cid=f"{id_prefix}buy{i}"
            )
        return remain

    def _long_sell(self, size: int):
        """
        批量限价单卖出，将大单拆分为多个小单
        :return:
        """
        mark_price = self._get_tag_price()
        min_price = mark_price
        max_price = mark_price * (1 + 0.005)
        split_size = 5

        # 在最低到最高价格区间随机采样5个数
        sampled_prices = [
            max_price - (max_price - min_price) * random.random() ** 2 for _ in range(split_size)
        ]

        # 将数量非均匀分割成5分
        sampled = [0.5 + random.random() for _ in range(split_size)]
        sampled_sizes = [int(size * sampled[i] / sum(sampled)) for i in range(split_size)]
        sampled_sizes.append(size - sum(sampled_sizes))

        # 随机生成8位数字作为订单ID
        id_prefix = random.randint(10000000, 99999999)

        # 准备批量订单
        orders = [
            {
                "instId": self.cfg.trade_config.coin,
                "tdMode": "cross",
                "clOrdId": f"{id_prefix}sell{i}",
                "ccy": "USDT",
                "side": "sell",
                "posSide": "long",
                "ordType": "limit",
                "px": f"{sampled_prices[i]}",
                "sz": f"{sampled_sizes[i]}",
            }
            for i in range(split_size)
        ]

        self.api.place_multiple_orders(orders)
        sleep(self.cfg.trade_config.order_wait)
        self.api.cancel_orders(
            orders=[
                {"instId": self.cfg.trade_config.coin, "clOrdId": f"{id_prefix}sell{i}"}
                for i in range(split_size)
            ]
        )

        remain = 0
        for i in range(split_size):
            remain += self.api.get_order_unclosed_count(
                instid=self.cfg.trade_config.coin, cid=f"{id_prefix}sell{i}"
            )
        return remain

    def _get_balance(self) -> float:
        """
        获取当前剩余资金
        :return:
        """
        return self.api.get_account_balance(ccy=self.cfg.trade_config.ccy)

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
