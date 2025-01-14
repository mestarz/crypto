
from abc import ABC, abstractmethod

class Factor(ABC):
    @abstractmethod
    def calculate_price(self, price: float) -> float:
        """计算因子价格
        Args:
            price (float): 输入价格
        Returns:
            float: 计算后的价格
        """
        pass
