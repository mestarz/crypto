import pandas as pd
from abc import ABC
from time import sleep

from core.cfg import Config
from core.execute import Execute
from core.retry import retry


class OKXExecute(Execute, ABC):
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.logger = self.cfg.logger

        """
        杠杆通过仓位控制，实际买入杠杆为全仓20倍，这样做是为了方便在持有仓位的情况下调整杠杆数
        """
        self.real_lever = 20
        self.cfg.accountAPI.set_leverage(
            instId=self.cfg.coin(),
            lever=f"{self.real_lever}",
            mgnMode="cross"
        )

        """
        初始化合约相关参数
        合约面值， 杠杆数， 最大买入次数
        """
        self.ct_val = self.cfg.ct_val()
        self.lever = self.cfg.lever()
        self.buy_chance = self.cfg.max_buy_chance()

    def sleep(self, time: int):
        sleep(time)

    @retry()
    def price(self):
        result = self.cfg.marketAPI.get_mark_price_candlesticks(
            instId=self.cfg.coin(),
            bar=self.cfg.period(),
        )['data'][::-1]
        return pd.DataFrame(result, columns=['ts', 'Open', 'High', 'Low', 'Close', 'isOver'])

    def buy(self):
        if self.buy_chance <= 0:
            self.logger.info("没有买入次数了，不触发买入")
            return

        funds = self._get_available_funds_with_lever() / self.buy_chance
        now_price = self._get_tag_price()
        buy_count = int(funds / (now_price * self.ct_val)) * self.real_lever
        self._long_buy(buy_count)
        self.buy_chance -= 1

    def sell(self):
        if self.buy_chance == self.cfg.max_buy_chance():
            self.logger.info("没有过买入，不触发卖出")
            return

        sell_count = int(self._get_position() / (self.cfg.max_buy_chance() - self.buy_chance))
        self._long_sell(sell_count)

    def _get_available_funds_with_lever(self) -> float:
        """
        获取计算杠杆后实际剩余可用资金
        :return:
        """
        balance = self._get_balance() - self.cfg.reserved()
        imr = self._get_imr()
        avail_funds = (self.lever / self.real_lever) * (balance + imr) - imr
        if avail_funds < 0:
            avail_funds = 0
        return avail_funds

    @retry()
    def _get_tag_price(self) -> float:
        """
        获取标记价格
        :return:
        """
        result = self.cfg.publicDataAPI.get_mark_price(
            instType="SWAP",
            instId=self.cfg.coin()
        )
        return float(result['data'][0]['markPx'])

    @retry()
    def _long_buy(self, size: int):
        """
        TODO - 优化买入策略， 当前为市价单买入
        :return:
        """
        return self.cfg.tradeAPI.place_order(
            instId=self.cfg.coin(),
            tdMode="cross",
            clOrdId="",
            ccy="USDT",
            side="buy",
            posSide="long",
            ordType="market",
            # px=f"{price}",
            sz=f"{size}",
        )

    @retry()
    def _long_sell(self, size: int):
        """
        TODO - 优化卖出策略， 当前为市价单卖出
        :return:
        """
        return self.cfg.tradeAPI.place_order(
            instId=self.cfg.coin(),
            tdMode="cross",
            clOrdId="",
            ccy="USDT",
            side="sell",
            posSide="long",
            ordType="market",
            # px=f"{price}",
            sz=f"{size}",
        )

    @retry()
    def _get_balance(self) -> float:
        """
        获取当前剩余资金
        :return:
        """
        result = self.cfg.accountAPI.get_account_balance(ccy=self.cfg.ccy())['data'][0]['details'][0]['availBal']
        if result == "":
            return 0
        return float(result)

    @retry()
    def _get_position(self) -> float:
        """
        获取当前仓位
        :return:
        """
        result = self.cfg.accountAPI.get_positions(instId=self.cfg.coin())['data']
        if len(result) == 0:
            return 0
        result = result[0]['availPos']
        if result == "":
            return 0
        return float(result)

    @retry()
    def _get_imr(self) -> float:
        """
        获取保证金
        :return:
        """
        result = self.cfg.accountAPI.get_positions(instId=self.cfg.coin())['data']
        if len(result) == 0:
            return 0
        result = result[0]['imr']
        if result == "":
            return 0
        return float(result)
