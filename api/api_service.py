from utils.retry import retry


class APIService:
    def __init__(self, accountAPI, marketAPI, tradeAPI, publicDataAPI):
        self.accountAPI = accountAPI
        self.marketAPI = marketAPI
        self.tradeAPI = tradeAPI
        self.publicDataAPI = publicDataAPI

    @retry()
    def set_leverage(self, instId: str, lever: str, mgnMode: str):
        """设置杠杆"""
        return self.accountAPI.set_leverage(instId=instId, lever=lever, mgnMode=mgnMode)

    @retry()
    def get_mark_price_candlesticks(self, instId: str, bar: str):
        """获取市场价格数据"""
        return self.marketAPI.get_mark_price_candlesticks(instId=instId, bar=bar)["data"][::-1]

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
        result = self.accountAPI.get_account_balance(ccy=ccy)["data"][0]["details"][0]["availBal"]
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
    def get_order_unclosed_count(self, instid: str, cid: str):
        """获取订单未成交的数量"""
        raw_data = self.tradeAPI.get_order(instId=instid, clOrdId=cid)["data"][0]
        return int(raw_data["sz"]) - int(raw_data["accFillSz"])
