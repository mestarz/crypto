import core.trace as trace
import core.strategy as strategy

from core.cfg import Config


def main():
    cfg = Config("simulation.ini")
    cfg.factor_config.ma_fast_timeperiod = 20
    cfg.factor_config.ma_slow_timeperiod = 120
    sim = trace.RandomTrace(cfg=cfg)
    engine = strategy.RSIGrid(sim, cfg=cfg)
    engine.run()
    sim.display()


if __name__ == "__main__":
    main()
