from abc import ABC, abstractmethod
import numpy as np
from datetime import datetime


class Execute(ABC):

    @abstractmethod
    def now(self) -> datetime:
        pass

    @abstractmethod
    def sleep(self, time: int):
        pass

    @abstractmethod
    def price(self, nums: int) -> np.ndarray:
        pass

    @abstractmethod
    def buy(self):
        pass

    @abstractmethod
    def sell(self):
        pass

    @abstractmethod
    def stop(self) -> bool:
        pass
