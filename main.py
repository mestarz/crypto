import core.trader as trader
import core.strategy as strategy

from core.cfg import Config


def main():
    # 初始化配置和执行器
    cfg = Config("simulation.ini")
    cfg.print_cfg()
    exec = trader.MarkTrader(cfg)
    engine = strategy.AvgRSI(exec, cfg)
    engine.run()


if __name__ == "__main__":
    main()
    
