import core.trace as trace
import core.strategy as strategy

from core.cfg import Config


def main():
    cfg = Config("simulation.ini")
    cfg.factor_config.ma_fast_timeperiod = 20
    cfg.factor_config.ma_slow_timeperiod = 200
    backtrace = trace.BackTrace(cfg=cfg, times=1000)
    engine = strategy.RSIGrid(backtrace, cfg=cfg)
    engine.run()
    backtrace.display()
    pass


if __name__ == "__main__":
    main()
