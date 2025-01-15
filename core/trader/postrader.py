from core.trader.base import RealExecute


class PositionTrader(RealExecute):
    """按仓位比例买卖"""

    def buy(self):
        raise ValueError("Hasn't implemented yet")

    def shell(self):
        raise ValueError("Hasn't implemented yet")

    def _buy(self, buy_count, now_price):
        raise ValueError("Hasn't implemented yet")

    def _sell(self, sell_count, now_price):
        raise ValueError("Hasn't implemented yet")

    def clear_long(self):
        """清掉多头仓位"""
        self.cfg.logger.debug("清空多头仓位")
        self._clear_position("long")

    def clear_short(self):
        """清掉空头仓位"""
        self.cfg.logger.debug("清空空头仓位")
        self._clear_position("short")

    def _clear_position(self, position_type):
        """清掉指定类型的仓位"""
        long, short = self.cfg.api.get_position_size_long_and_short(self.cfg.trade_config.coin)
        if position_type == "long" and long > 0:
            self.cfg.logger.debug(f"清空多头仓位: {long}")
            self.cfg.api.market_long_sell(self.cfg.trade_config.coin, long)
        elif position_type == "short" and short > 0:
            self.cfg.logger.debug(f"清空空头仓位: {short}")
            self.cfg.api.market_short_sell(self.cfg.trade_config.coin, short)

    def set_long_position(self, percentage: float):
        self._set_position(percentage, "long")

    def set_short_position(self, percentage: float):
        self._set_position(percentage, "short")

    def _set_position(self, percentage: float, position_type: str):
        percentage = percentage * (self.cfg.trade_config.lever / self.real_lever)
        long, short = self.cfg.api.get_position_size_long_and_short(self.cfg.trade_config.coin)
        """清空反向仓位"""
        self._clear_position("short" if position_type == "long" else "long")
        self.sleep(1)

        """计算目标仓位"""
        current_price = self.cfg.api.get_mark_price(instType="SWAP", instId=self.cfg.trade_config.coin)
        balance = self.cfg.api.get_account_balance(self.cfg.trade_config.ccy) - self.cfg.trade_config.reserved
        position_size = long if position_type == "long" else short
        adjusted_balance = int((balance * self.real_lever) // (current_price * self.ct_val))
        target_position = int((adjusted_balance + position_size) * percentage) - position_size
        self.cfg.logger.debug(f"设置{position_type}仓位: {target_position}")
        if target_position < 0:
            getattr(self.cfg.api, f"market_{position_type}_sell")(
                self.cfg.trade_config.coin, -target_position
            )
        else:
            getattr(self.cfg.api, f"market_{position_type}_buy")(self.cfg.trade_config.coin, target_position)

    def all_in_long(self):
        self.clear_short()
        self.set_long_position(1)

    def all_in_short(self):
        self.clear_long()
        self.set_short_position(1)
