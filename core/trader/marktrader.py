from core.trader.base import RealExecute


class MarkTrader(RealExecute):
    def _buy(self, buy_count, now_price):
        """市价买入"""
        return self.api.market_long_buy(self.cfg.trade_config.coin, buy_count)

    def _sell(self, sell_count, now_price):
        """市价卖出"""
        return self.api.market_long_sell(self.cfg.trade_config.coin, sell_count)
