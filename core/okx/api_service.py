from logging import logProcesses
from typing import Tuple
from core.okx.retry import retry
from core.config import Config

import okx.Account
import okx.Trade
import okx.PublicData
import okx.MarketData


class APIService:
    def __init__(self):
        config = Config()
        self.config = config
        apikey = config.apikey
        secretkey = config.secretkey
        passphrase = config.passphrase
        self.accountAPI = okx.Account.AccountAPI(
            apikey, secretkey, passphrase, False, config.flag, debug=config.debug
        )
        self.marketAPI = okx.MarketData.MarketAPI(
            apikey, secretkey, passphrase, False, config.flag, debug=config.debug
        )
        self.tradeAPI = okx.Trade.TradeAPI(
            apikey, secretkey, passphrase, False, config.flag, debug=config.debug
        )
        self.publicDataAPI = okx.PublicData.PublicAPI(
            apikey, secretkey, passphrase, False, config.flag, debug=config.debug
        )

    @retry()
    def set_leverage(self, instId: str, lever: str, mgnMode: str):
        """设置杠杆"""
        self.accountAPI.set_leverage(
            instId=instId, lever=lever, mgnMode=mgnMode, posSide="long"
        )
        self.accountAPI.set_leverage(
            instId=instId, lever=lever, mgnMode=mgnMode, posSide="short"
        )

    @retry()
    def get_mark_price(self, instId: str):
        """获取标记价格"""
        if instId.endswith("SWAP"):
            instType = "SWAP"
        else:
            instType = "MARGIN"
        result = self.publicDataAPI.get_mark_price(instType=instType, instId=instId)
        return float(result["data"][0]["markPx"])

    @retry()
    def place_multiple_orders(self, orders: list):
        """批量下单"""
        return self.tradeAPI.place_multiple_orders(orders)

    @retry()
    def get_account_balance(self, ccy: str):
        """获取账户余额"""
        result = self.accountAPI.get_account_balance(ccy=ccy)["data"][0]["details"][0][
            "availBal"
        ]
        return float(result) if result != "" else 0

    @retry()
    def get_positions(self, instId: str):
        """获取仓位信息"""
        result = self.accountAPI.get_positions(instId=instId)["data"]
        if len(result) == 0:
            return 0
        result = result[0]["availPos"]
        return float(result) if result != "" else 0

    @retry()
    def get_position_size_long_and_short(self, instId: str) -> Tuple[float, float]:
        """获取long & short的持仓"""
        result = self.accountAPI.get_positions(instId=instId)["data"]
        long = 0
        short = 0
        for item in result:
            if item["posSide"] == "long" and item["availPos"] != "":
                long += float(item["availPos"])
            elif item["posSide"] == "short" and item["availPos"] != "":
                short += float(item["availPos"])
        return long, short

    @retry()
    def get_imr(self, instId=""):
        """获取保证金（不传入instId时表示全仓保证金）"""
        if len(instId) == 0:
            result = self.accountAPI.get_positions()["data"]
        else:
            result = self.accountAPI.get_positions(instId=instId)["data"]

        if len(result) == 0:
            return 0
        imr = 0
        for item in result:
            if item["imr"] != "":
                imr += float(item["imr"])
        return imr

    @retry()
    def ct_val(self, instId: str) -> float:
        """获取合约面值"""
        coin_info = self.get_instruments(instId)
        return float(coin_info["ctVal"])

    @retry()
    def get_instruments(self, instId: str):
        result = self.publicDataAPI.get_instruments(instType="SWAP", instId=instId)
        coin_info = result["data"][0]
        return coin_info

    def get_sz_by_value(self, instId: str, value: float) -> str:
        """获取指定资金可以购买的合约张数 (1倍杠杆)"""
        coin_info = self.get_instruments(instId)
        lotSz = float(coin_info["lotSz"])  # 下单精度
        minSz = float(coin_info["minSz"])  # 最小下单数
        ctVal = float(coin_info["ctVal"])  # 合约面值
        markVal = self.get_mark_price(instId)  # 标记价格

        sz = value / (ctVal * markVal)  # 可买张数

        # 对齐到下单精度
        # OKX 的 lotSz 表示张数的最小递增单位，例如 1 或 0.001
        sz = (sz // lotSz) * lotSz

        # 不得小于最小下单数
        if sz < minSz:
            return "0"

        if lotSz.is_integer():
            return str(int(sz))
        # 转字符串返回，符合下单 API 规范
        return str(round(sz, len(str(lotSz).split(".")[-1])))

    def get_account_usdt(self):
        """获取账户usdt计价全资产（usdt余额+合约保证金）"""
        imr = self.get_imr()
        imr += self.get_account_balance("USDT")
        return imr

    @retry()
    def cancel_orders(self, orders: list):
        """批量撤单"""
        return self.tradeAPI.cancel_multiple_orders(orders)

    @retry()
    def get_order_unclosed_count(self, instId: str, cid: str):
        """获取订单未成交的数量"""
        raw_data = self.tradeAPI.get_order(instId=instId, clOrdId=cid)["data"][0]
        return int(raw_data["sz"]) - int(raw_data["accFillSz"])

    @retry()
    def _market_order(self, instId: str, sz: str, side: str, pos: str):
        return self.tradeAPI.place_order(
            instId=instId,
            tdMode="cross",
            ccy="USDT",
            side=side,
            posSide=pos,
            ordType="market",
            sz=sz,
        )

    @retry()
    def market_long_buy(self, instId: str, sz: str):
        """long市价开仓"""
        return self._market_order(instId, sz, "buy", "long")

    @retry()
    def market_long_sell(self, instId: str, sz: str):
        """long市价平仓"""
        return self._market_order(instId, sz, "sell", "long")

    @retry()
    def market_short_buy(self, instId: str, sz: str):
        """short市价开仓"""
        return self._market_order(instId, sz, "sell", "short")

    @retry()
    def market_short_sell(self, instId: str, sz: str):
        """short市价平仓"""
        return self._market_order(instId, sz, "buy", "short")
