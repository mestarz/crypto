import math
from time import sleep
from core.kronos.main import main_infer
from core.okx.api_service import APIService
from core.config import Config


class Machine:
    def __init__(self) -> None:
        self.config = Config()
        self.api = APIService()
        self.target_coins = self.config.target_coins

    @staticmethod
    def isZero(f: float):
        return math.isclose(f, 0.0, abs_tol=1e-7)

    def log(self, msg: str):
        print(msg)

    def init(self):
        # 设置杠杆
        for coin in self.target_coins:
            self.api.set_leverage(f"{coin}-USDT-SWAP", "1", "cross")
            self.log(f"设置{coin}杠杆为1")

    def avail_balance(self) -> float:
        bl = self.api.get_account_usdt() * 1.0 / len(self.target_coins)
        a = self.api.get_account_balance("USDT")
        # 预留100刀，防止交易失败
        return min(a - 100, bl)

    def short(self, coin: str):
        [long, short] = self.api.get_position_size_long_and_short(
            instId=f"{coin}-USDT-SWAP"
        )
        if not self.isZero(short):
            return
        if not self.isZero(long):
            self.api.market_long_sell(f"{coin}-USDT-SWAP", str(long))
            self.log(f"[平仓] long sell {coin} {long}")
        sz = self.api.get_sz_by_value(f"{coin}-USDT-SWAP", self.avail_balance())
        self.log(f"[交易] short buy {coin} {sz}")
        self.api.market_short_buy(f"{coin}-USDT-SWAP", sz)

    def long(self, coin: str):
        [long, short] = self.api.get_position_size_long_and_short(
            instId=f"{coin}-USDT-SWAP"
        )
        if not self.isZero(long):
            return
        if not self.isZero(short):
            self.api.market_short_sell(f"{coin}-USDT-SWAP", str(short))
            self.log(f"[平仓] short sell {coin} {short}")
        sz = self.api.get_sz_by_value(f"{coin}-USDT-SWAP", self.avail_balance())
        self.log(f"[交易] long buy {coin} {sz}")
        self.api.market_long_buy(f"{coin}-USDT-SWAP", sz)

    def run_once(self):
        infer_results = main_infer()
        for coin in self.target_coins:
            r = infer_results[coin]
            self.log(f"[infer] {coin}: {r[0]}")
            if r[0] > 0.6:
                self.long(coin)
            elif r[0] < 0.4:
                self.short(coin)


def main():
    mac = Machine()
    mac.init()

    while True:
        mac.run_once()
        sleep(5 * 60)


if __name__ == "__main__":
    main()
