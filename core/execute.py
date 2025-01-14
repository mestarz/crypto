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
    def price(self, nums: int = 100) -> np.ndarray:
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

    """position"""

    @abstractmethod
    def all_in_long(self):
        pass

    @abstractmethod
    def all_in_short(self):
        pass

    @abstractmethod
    def clear_long(self):
        pass

    @abstractmethod
    def clear_short(self):
        pass

    @abstractmethod
    def set_long_position(self, percentage: float):
        pass

    @abstractmethod
    def set_short_position(self, percentage: float):
        pass
