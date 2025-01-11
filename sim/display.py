import matplotlib.pyplot as plt
from matplotlib import gridspec


def show_simulation_result(kline_data, buy_points, sell_points, rsi_data):
    """展示仿真结果"""
    try:
        if kline_data is None or len(kline_data) < 2:
            raise ValueError("K线数据不足，无法绘制图表")
        if rsi_data is None or len(rsi_data) < 2:
            raise ValueError("RSI数据不足，无法绘制图表")

        plt.figure(figsize=(12, 8))
        gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])

        # 价格图表
        ax1 = plt.subplot(gs[0])
        ax1.set_title("Simulation Price Chart")
        ax1.plot(kline_data, label="Price")

        # 绘制买卖点
        if buy_points is not None and len(buy_points) > 0:
            ax1.scatter(buy_points, kline_data[buy_points], marker="^", color="g", label="Buy", s=200)
        if sell_points is not None and len(sell_points) > 0:
            ax1.scatter(sell_points, kline_data[sell_points], marker="v", color="r", label="Sell", s=200)
        ax1.legend()

        # RSI图表
        ax2 = plt.subplot(gs[1])
        ax2.set_title("RSI")
        ax2.plot(rsi_data, label="RSI", color="orange")
        ax2.axhline(70, color="red", linestyle="--")
        ax2.axhline(30, color="green", linestyle="--")
        ax2.legend()

        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"展示仿真结果时出错: {str(e)}")
        plt.close()
