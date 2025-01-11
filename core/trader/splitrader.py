import random

from core.trader.base import RealExecute


class SplitTrader(RealExecute):
    def _buy(self, buy_count: int, now_price: float):
        remain_count = buy_count
        while remain_count > buy_count * 0.2:
            remain_count = self._long_buy(remain_count)
            self.logger.info(f"剩余数量={remain_count}")
            cprice = self._get_tag_price()
            if cprice > now_price:
                self.logger.info(f"当前价格{cprice}高于买入价格{now_price}，停止买入")
                break
        if remain_count > buy_count * 0.5:
            self.buy_chance += 1
        self.logger.info(f"买入完成: 实际数量={buy_count - remain_count}, 剩余买入次数={self.buy_chance}")

    def _sell(self, sell_count: int, now_price: float):
        remain_count = sell_count
        while remain_count > sell_count * 0.2:
            remain_count = self._long_sell(remain_count)
            self.logger.info(f"剩余数量={remain_count}")
            cprice = self._get_tag_price()
            if cprice < now_price:
                self.logger.info(f"当前价格{cprice}低于卖出价格{now_price}，停止卖出")
                break
        if remain_count > sell_count * 0.5:
            self.buy_chance -= 1
        self.logger.info(f"卖出完成: 实际数量={sell_count - remain_count}, 剩余买入次数={self.buy_chance}")

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
        self.sleep(self.cfg.trade_config.order_wait)
        self.api.cancel_orders(
            orders=[
                {"instId": self.cfg.trade_config.coin, "clOrdId": f"{id_prefix}buy{i}"}
                for i in range(split_size)
            ]
        )

        remain = 0
        for i in range(split_size):
            remain += self.api.get_order_unclosed_count(
                instId=self.cfg.trade_config.coin, cid=f"{id_prefix}buy{i}"
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
        self.sleep(self.cfg.trade_config.order_wait)
        self.api.cancel_orders(
            orders=[
                {"instId": self.cfg.trade_config.coin, "clOrdId": f"{id_prefix}sell{i}"}
                for i in range(split_size)
            ]
        )

        remain = 0
        for i in range(split_size):
            remain += self.api.get_order_unclosed_count(
                instId=self.cfg.trade_config.coin, cid=f"{id_prefix}sell{i}"
            )
        return remain
