import core.trader as trader

from core.cfg import Config
from core.strategy import RandBuy


def main():
    # 初始化配置和执行器
    cfg = Config("simulation.ini")
    cfg.print_cfg()
    exec = trader.MarkTrader(cfg)
    strategy = RandBuy(exec, cfg)
    strategy.run()


if __name__ == "__main__":
    main()
