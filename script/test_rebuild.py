import core.trader as trader
import talib
import numpy as np
import matplotlib.pyplot as plt
from core.cfg import Config


def main():
    cfg = Config("simulation.ini")
    exec = trader.MarkTrader(cfg)
    price = exec.price()["Close"].to_numpy()

    # 计算快慢均线
    fast = talib.SMA(price, timeperiod=cfg.factor_config.ma_fast_timeperiod)
    slow = talib.SMA(price, timeperiod=cfg.factor_config.ma_slow_timeperiod)

    # 等量去掉price、fast、slow中存在空的下标
    price = price[cfg.factor_config.ma_slow_timeperiod :]
    fast = fast[cfg.factor_config.ma_slow_timeperiod :]
    slow = slow[cfg.factor_config.ma_slow_timeperiod :]

    print("Price:", price)
    print("Fast MA:", fast)
    print("Slow MA:", slow)

    # 绘制图表
    plt.figure(figsize=(12, 6))
    plt.plot(price, label="Price")
    plt.plot(fast, label="Fast MA", color="green", linestyle="--")
    plt.plot(slow, label="Slow MA", color="red", linestyle="--")
    plt.legend()
    plt.title("Price and Moving Averages")
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.show()


if __name__ == "__main__":
    main()
