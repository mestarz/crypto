from core.kronos.main import main_infer
from core.okx.api_service import APIService
from core.config import Config


def log(msg: str):
    print(msg)


def main():
    config = Config()
    api = APIService()
    target_coins = config.target_coins
    # 设置杠杆
    # for coin in target_coins:
    #    api.set_leverage(f"{coin}-USDT-SWAP", "2", "cross")
    #    log(f"设置{coin}杠杆为2")

    # sz = api.get_sz_by_value("BTC-USDT-SWAP", 1000)
    # a = api.market_long_buy("BTC-USDT-SWAP", sz)
    # print(a)

    # a = api.get_position_size_long_and_short(instId="BTC-USDT-SWAP")
    # a = api.get_account_usdt()
    # print(a)
    # r = api.get_account_balance("USDT")
    # print(r)

    r = main_infer()
    print(r)


if __name__ == "__main__":
    main()
