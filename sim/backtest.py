from abc import ABC
from core.execute import Execute


class BackTest(Execute, ABC):
    def __init__(self):
        self.work_time = 0
        self.stop_time = 500 * 60

    def sleep(self, seconds: int):
        self.work_time += seconds

    def now(self):
        return self.work_time

    def stop(self):
        return self.work_time >= self.stop_time

    def price():
        pass

    def buy(self):
        return super().buy()

    def sell(self):
        return super().sell()
