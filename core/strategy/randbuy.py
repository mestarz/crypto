import random

from core.execute import Execute
from core.cfg import Config


class RandBuy:
    def __init__(self, execution: Execute, cfg: Config):
        self.exec = execution
        self.cfg = cfg
        self.logger = cfg.logger

    def run(self):
        while True:
            if random.randint(0, 1) == 0:
                self.exec.buy()
            else:
                self.exec.sell()
