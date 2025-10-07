import pandas as pd

from typing import Tuple
from core.okx.retry import retry

import okx.Account
import okx.Trade
import okx.PublicData
import okx.MarketData


class APIService:
    def __init__(self):
        self.accountAPI = accountAPI
        self.marketAPI = marketAPI
        self.tradeAPI = tradeAPI
        self.publicDataAPI = publicDataAPI

    @retry()
    def set_leverage(self, instId: str, lever: str, mgnMode: str):
        """设置杠杆"""
        self.accountAPI.set_leverage(
            instId=instId, lever=lever, mgnMode=mgnMode, posSide="long"
        )
        self.accountAPI.set_leverage(
            instId=instId, lever=lever, mgnMode=mgnMode, posSide="short"
        )

    def get_more_data(self, instId: str, bar: str, nums: int = 100) -> pd.DataFrame:
        r = self.get_mark_price_candlesticks(instId=instId, bar=bar, limit=nums)
        timestamp = r[0][0]
        count = nums - len(r)
        while count > 0:
            limit = 100 if count > 100 else count
            count -= limit
            r = (
                self.get_mark_price_candlesticks(
                    instId=instId,
                    bar=bar,
                    after=timestamp,
                    limit=limit,
                )
                + r
            )
            timestamp = r[0][0]

        df = pd.DataFrame(r, columns=["ts", "Open", "High", "Low", "Close", "isOver"])
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

    @retry()
    def get_mark_price_candlesticks(
        self, instId: str, bar: str, limit: int = 100, after: str = ""
    ):
        """获取市场价格数据"""
        return self.marketAPI.get_mark_price_candlesticks(
            instId=instId, bar=bar, limit=f"{limit}", after=after
        )["data"][::-1]

    @retry()
    def get_mark_price(self, instType: str, instId: str):
        """获取标记价格"""
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
    def get_imr(self, instId: str):
        """获取保证金"""
        result = self.accountAPI.get_positions(instId=instId)["data"]
        if len(result) == 0:
            return 0
        result = result[0]["imr"]
        return float(result) if result != "" else 0

    @retry()
    def ct_val(self, instId: str) -> float:
        """获取合约面值"""
        result = self.publicDataAPI.get_instruments(instType="SWAP", instId=instId)
        coin_info = result["data"][0]
        return float(coin_info["ctVal"])

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
    def market_long_buy(self, instId: str, sz: int):
        """long市价开仓"""
        return self.tradeAPI.place_order(
            instId=instId,
            tdMode="cross",
            ccy="USDT",
            side="buy",
            posSide="long",
            ordType="market",
            sz=f"{sz}",
        )

    @retry()
    def market_long_sell(self, instId: str, sz: int):
        """long市价平仓"""
        return self.tradeAPI.place_order(
            instId=instId,
            tdMode="cross",
            ccy="USDT",
            side="sell",
            posSide="long",
            ordType="market",
            sz=f"{sz}",
        )

    @retry()
    def market_short_buy(self, instId: str, sz: int):
        """short市价开仓"""
        return self.tradeAPI.place_order(
            instId=instId,
            tdMode="cross",
            ccy="USDT",
            side="sell",
            posSide="short",
            ordType="market",
            sz=f"{sz}",
        )

    @retry()
    def market_short_sell(self, instId: str, sz: int):
        """short市价平仓"""
        return self.tradeAPI.place_order(
            instId=instId,
            tdMode="cross",
            ccy="USDT",
            side="buy",
            posSide="short",
            ordType="market",
            sz=f"{sz}",
        )
