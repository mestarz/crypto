from core.cfg import Config
import numpy as np
from sim.trace import TraceExec
from strategy.rsigrid import RSIGrid


class RandomExec(TraceExec):
    def init_price(self):
        current_price = 100
        # 生成正态分布的随机数，均值0，标准差0.0333，限制在[-0.1, 0.1]范围内
        for _ in range(int(self.stop_time / 60) + 10):
            random_factor = np.clip(np.random.normal(0, 0.00333), -0.01, 0.01)
            current_price = current_price * (1 + random_factor)
            self.price_history.append(current_price)


if __name__ == "__main__":
    cfg = Config("simulation.ini")
    sim = RandomExec(cfg=cfg)
    strategy = RSIGrid(sim, cfg=cfg)
    strategy.run()
    sim.display()
