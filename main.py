from abc import ABC, abstractmethod
import argparse
from typing import Type, Dict
from core.cfg import Config
from core.real import OKXExecute


class Strategy(ABC):
    """策略接口"""

    @abstractmethod
    def run(self):
        pass


class StrategyFactory:
    """策略工厂"""

    def __init__(self):
        self._strategies: Dict[str, Type[Strategy]] = {}

    def register_strategy(self, name: str, strategy: Type[Strategy]):
        """注册策略"""
        self._strategies[name] = strategy

    def get_strategy(self, name: str, exec: OKXExecute, cfg: Config) -> Strategy:
        """获取策略实例"""
        strategy = self._strategies.get(name)
        if not strategy:
            raise ValueError(f"未知策略: {name}")
        return strategy(exec, cfg)


def register_strategies(factory: StrategyFactory):
    """注册所有可用策略"""
    from strategy.rsigrid import RSIGrid

    factory.register_strategy("rsi_grid", RSIGrid)
    # 在此添加更多策略


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="交易策略执行器")
    parser.add_argument("-s", "--strategy", default="rsi_grid", help="选择要执行的策略 (默认: rsi_grid)")
    parser.add_argument(
        "-c", "--config", default="simulation.ini", help="配置文件路径 (默认: simulation.ini)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 初始化配置和执行器
    cfg = Config(args.config)
    cfg.print_cfg()
    exec = OKXExecute(cfg)

    # 初始化策略工厂并注册策略
    factory = StrategyFactory()
    register_strategies(factory)

    # 获取并运行策略
    strategy = factory.get_strategy(args.strategy, exec, cfg)
    strategy.run()


if __name__ == "__main__":
    main()
