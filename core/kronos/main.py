from core.okx.kline import get_okx_data
from core.kronos.infer.infer import infer_predict
from core.config import Config

configs = Config()


def main_infer():
    target_coin = [
        "BTC",
        "ETH",
        "XRP",
        "BNB",
        "SOL",
    ]

    dfs = []
    tps = []
    for coin in target_coin:
        df = get_okx_data(f"{coin}-USDT", configs.lookback_window)
        x_df = df.loc[:, ["open", "high", "low", "close", "volume", "amount"]]
        x_timestamp = df.loc[:, "timestamps"]
        dfs.append(x_df)
        tps.append(x_timestamp)

    r = infer_predict(dfs, tps)


if __name__ == "__main__":
    main_infer()
