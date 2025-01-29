import core.trader as trader
from core.strategy.reverse.avgrsi import AvgRSI
from core.cfg import Config
from init_env import load_env_variables

def main():
    load_env_variables()
    # 初始化配置和执行器
    cfg = Config("simulation.ini")
    cfg.print_cfg()
    exec = trader.PositionTrader(cfg)
    engine = AvgRSI(exec, cfg)
    engine.run()


if __name__ == "__main__":
    main()
