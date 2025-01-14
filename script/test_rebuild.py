import core.trader as trader
import talib
import numpy as np
import matplotlib.pyplot as plt
from core.cfg import Config
import time


def main():
    cfg = Config("simulation.ini")
    cfg.trade_config.period = "5m"
    exec = trader.MarkTrader(cfg)
    price = exec.price(nums=1000)["Close"].to_numpy()

    # 计算慢均线
    slow = np.array(talib.SMA(price, timeperiod=200))

    # 等量去掉price、slow中存在空的下标
    price = price[200:]
    slow = slow[200:]

    rebuild = (price - slow) + price[0]

    # 计算rebuild的快线
    fast_rebuild = talib.SMA(rebuild, timeperiod=20)

    price = price[20:]
    slow = slow[20:]
    rebuild = rebuild[20:]
    fast_rebuild = fast_rebuild[20:]

    # 计算fast_rebuild的rsi
    rsi_rebuild = talib.RSI(fast_rebuild, timeperiod=14)

    price = price[14:]
    slow = slow[14:]
    rebuild = rebuild[14:]
    fast_rebuild = fast_rebuild[14:]
    rsi_rebuild = rsi_rebuild[14:]

    print("Price:", price)
    print("Slow MA:", slow)
    print("Rebuild:", rebuild)
    print("Fast Rebuild:", fast_rebuild)
    print("RSI Rebuild:", rsi_rebuild)

    # 绘制图表
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    ax1.plot(price, label="Price")
    ax1.plot(slow, label="Slow MA", color="red", linestyle="--")
    ax1.plot(rebuild, label="Rebuild", color="blue", linestyle="-.")
    ax1.plot(fast_rebuild, label="Fast Rebuild", color="green", linestyle="--")
    ax1.legend()
    ax1.set_title("Price, Slow MA, Rebuild, and Fast Rebuild")
    ax1.set_xlabel("Time")
    ax1.set_ylabel("Price")

    ax2.plot(rsi_rebuild, label="RSI Rebuild", color="purple")
    ax2.axhline(70, color="red", linestyle="--")
    ax2.axhline(30, color="green", linestyle="--")
    ax2.legend()
    ax2.set_title("RSI of Rebuild")
    ax2.set_xlabel("Time")
    ax2.set_ylabel("RSI")

    # 添加跟随鼠标移动的竖线
    vert_line1 = ax1.axvline(x=0, color="k", linestyle="--")
    vert_line2 = ax2.axvline(x=0, color="k", linestyle="--")

    last_time = time.time()
    throttle_interval = 1 / 120  # 帧数/fps

    def on_mouse_move(event):
        nonlocal last_time
        current_time = time.time()
        if event.inaxes in [ax1, ax2] and current_time - last_time >= throttle_interval:
            index = int(event.xdata)
            if 0 <= index < len(price):
                vert_line1.set_xdata([index])
                vert_line2.set_xdata([index])
                fig.canvas.draw_idle()
                last_time = current_time

    fig.canvas.mpl_connect("motion_notify_event", on_mouse_move)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
