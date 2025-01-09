from abc import ABC, abstractmethod


class Execute(ABC):

    @abstractmethod
    def sleep(self, time: int):
        pass

    @abstractmethod
    def price(self):
        pass

    @abstractmethod
    def buy(self):
        pass

    @abstractmethod
    def sell(self):
        pass
