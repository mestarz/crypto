import os
import configparser
import logging
from dataclasses import dataclass
from configparser import ConfigParser
from logging import Logger, getLogger

import okx.Account
import okx.Trade
import okx.PublicData
import okx.MarketData


@dataclass
class APIConfig:
    """OKX API 配置"""

    api_key: str
    secret_key: str
    passphrase: str
    proxy: str
    is_simulate: bool = False


@dataclass
class TradeConfig:
    """交易相关配置"""

    coin: str
    period: str
    lever: float
    ccy: str
    reserved: float
    max_buy_chance: int
    trade_timeperiod: int


@dataclass
class LogConfig:
    """日志配置"""

    filename: str
    level: int


class Config:
    """应用配置管理类"""

    def __init__(self, config_path: str):
        """
        初始化配置

        Args:
            config_path: 配置文件路径
        """
        self._cfg = self._load_config(config_path)
        self.api_config = self._init_api_config()
        self.trade_config = self._init_trade_config()
        self.log_config = self._init_log_config()
        self.logger = self._init_logger()
        self._init_apis()

    def _load_config(self, config_path: str) -> ConfigParser:
        """加载配置文件"""
        current_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(f"{current_path}/../config", config_path)
        config = configparser.ConfigParser()
        config.read(full_path)
        return config

    def _init_api_config(self) -> APIConfig:
        """初始化API配置"""
        return APIConfig(
            api_key=self._cfg.get("OKX", "apikey"),
            secret_key=self._cfg.get("OKX", "secretkey"),
            passphrase=self._cfg.get("OKX", "passphrase"),
            proxy=self._cfg.get("DEFAULT", "proxy"),
            is_simulate=self._cfg.getboolean("DEFAULT", "simulate"),
        )

    def _init_trade_config(self) -> TradeConfig:
        """初始化交易配置"""
        return TradeConfig(
            coin=self._cfg.get("TRADE", "coin"),
            period=self._cfg.get("TRADE", "period"),
            lever=self._cfg.getfloat("TRADE", "lever"),
            ccy=self._cfg.get("TRADE", "ccy"),
            reserved=self._cfg.getfloat("TRADE", "reserved"),
            max_buy_chance=self._cfg.getint("TRADE", "max_buy_chance"),
            trade_timeperiod=self._cfg.getint("TRADE", "trade_timeperiod"),
        )

    def _init_log_config(self) -> LogConfig:
        """初始化日志配置"""
        level_str = self._cfg.get("LOG", "level")
        level = getattr(logging, level_str.upper())
        return LogConfig(filename=self._cfg.get("LOG", "filename"), level=level)

    def _init_apis(self) -> None:
        """初始化所有API接口"""
        flag = "1" if self.api_config.is_simulate else "0"

        self.accountAPI = okx.Account.AccountAPI(
            api_key=self.api_config.api_key,
            api_secret_key=self.api_config.secret_key,
            passphrase=self.api_config.passphrase,
            use_server_time=False,
            proxy=self.api_config.proxy,
            flag=flag,
        )

        self.tradeAPI = okx.Trade.TradeAPI(
            api_key=self.api_config.api_key,
            api_secret_key=self.api_config.secret_key,
            passphrase=self.api_config.passphrase,
            use_server_time=False,
            flag=flag,
            proxy=self.api_config.proxy,
        )

        self.publicDataAPI = okx.PublicData.PublicAPI(flag=flag, proxy=self.api_config.proxy)

        self.marketAPI = okx.MarketData.MarketAPI(flag=flag, proxy=self.api_config.proxy)

    def _init_logger(self) -> Logger:
        """初始化日志记录器"""
        logger = getLogger(__name__)
        logger.setLevel(self.log_config.level)

        # 文件处理器
        file_handler = logging.FileHandler(self.log_config.filename)
        file_handler.setLevel(self.log_config.level)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_config.level)

        # 格式化器
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] - %(message)s")
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        return logger

    def factor_int_param(self, param: str) -> int:
        """获取FACTOR部分的整型参数"""
        return self._cfg.getint("FACTOR", param)

    def print_cfg(self) -> None:
        """打印当前配置"""
        self.logger.info("=== API配置 ===")
        self.logger.info(f"API Key: {'*' * len(self.api_config.api_key)}")
        self.logger.info(f"Secret Key: {'*' * len(self.api_config.secret_key)}")
        self.logger.info(f"Passphrase: {'*' * len(self.api_config.passphrase)}")
        self.logger.info(f"Proxy: {self.api_config.proxy}")
        self.logger.info(f"模拟模式: {self.api_config.is_simulate}")

        self.logger.info("\n=== 交易配置 ===")
        self.logger.info(f"交易币种: {self.trade_config.coin}")
        self.logger.info(f"交易周期: {self.trade_config.period}")
        self.logger.info(f"杠杆倍数: {self.trade_config.lever}")
        self.logger.info(f"保证金币种: {self.trade_config.ccy}")
        self.logger.info(f"保留金额: {self.trade_config.reserved}")
        self.logger.info(f"最大买入次数: {self.trade_config.max_buy_chance}")
        self.logger.info(f"交易时间周期: {self.trade_config.trade_timeperiod}")

        self.logger.info("\n=== 日志配置 ===")
        self.logger.info(f"日志文件: {self.log_config.filename}")
        self.logger.info(f"日志级别: {self.log_config.level}")
