from core.trader.base import RealExecute


class MarkTrader(RealExecute):
    def _buy(self, buy_count, now_price):
        """市价买入"""
        r = self.api.market_buy(self.cfg.trade_config.coin, buy_count)
        print(r)
        return r

    def _sell(self, sell_count, now_price):
        """市价卖出"""
        return self.api.market_sell(self.cfg.trade_config.coin, sell_count)
