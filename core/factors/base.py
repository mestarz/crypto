from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RawData:
    price: list[float]
    volume: list[int]


class Signal(ABC):
    @abstractmethod
    def start(self, raw_data: RawData) -> bool:
        pass

    @abstractmethod
    def create(self, raw_data: RawData) -> bool:
        pass

    @abstractmethod
    def stop(self, raw_data: RawData) -> bool:
        pass

    @abstractmethod
    def valid(self, raw_data: RawData) -> bool:
        pass


class Factor(ABC):
    @abstractmethod
    def __bool__(self) -> bool:
        pass

    def value(self, raw_data: RawData) -> float:
        pass
