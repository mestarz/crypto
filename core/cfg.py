import os
import configparser
import logging
from dataclasses import dataclass
from configparser import ConfigParser
from logging import Logger, getLogger
from core.api_service import APIService

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
    is_simulate: bool
    api_debug: bool


@dataclass
class TradeConfig:
    """交易相关配置"""

    coin: str
    period: str
    lever: float
    ccy: str
    reserved: float
    order_wait: int
    max_buy_chance: int
    trade_timeperiod: int


@dataclass
class LogConfig:
    """日志配置"""

    filename: str
    level: int


@dataclass
class FactorConfig:
    """FACTOR 配置"""

    rsi_timeperiod: int
    ma_fast_timeperiod: int
    ma_slow_timeperiod: int
    rsi_down: int
    rsi_up: int


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
        self.factor_config = self._init_factor_config()
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
            api_key=self._cfg.get("OKX", "apikey", fallback="default_api_key"),
            secret_key=self._cfg.get("OKX", "secretkey", fallback="default_secret_key"),
            passphrase=self._cfg.get("OKX", "passphrase", fallback="default_passphrase"),
            proxy=self._cfg.get("DEFAULT", "proxy", fallback=""),
            is_simulate=self._cfg.getboolean("DEFAULT", "simulate", fallback=True),
            api_debug=self._cfg.getboolean("DEFAULT", "api_debug", fallback=True),
        )

    def _init_trade_config(self) -> TradeConfig:
        """初始化交易配置"""
        return TradeConfig(
            coin=self._cfg.get("TRADE", "coin", fallback="BTC"),
            period=self._cfg.get("TRADE", "period", fallback="1m"),
            lever=self._cfg.getfloat("TRADE", "lever", fallback=1.0),
            ccy=self._cfg.get("TRADE", "ccy", fallback="USDT"),
            reserved=self._cfg.getfloat("TRADE", "reserved", fallback=100.0),
            order_wait=self._cfg.getint("TRADE", "order_wait", fallback=30),
            max_buy_chance=self._cfg.getint("TRADE", "max_buy_chance", fallback=5),
            trade_timeperiod=self._cfg.getint("TRADE", "trade_timeperiod", fallback=14),
        )

    def _init_log_config(self) -> LogConfig:
        """初始化日志配置"""
        level_str = self._cfg.get("LOG", "level")
        level = getattr(logging, level_str.upper())
        return LogConfig(filename=self._cfg.get("LOG", "filename"), level=level)

    def _init_factor_config(self) -> FactorConfig:
        """初始化FACTOR配置"""
        return FactorConfig(
            rsi_timeperiod=self._cfg.getint("FACTOR", "rsi_timeperiod", fallback=14),
            ma_fast_timeperiod=self._cfg.getint("FACTOR", "ma_fast_timeperiod", fallback=6),
            ma_slow_timeperiod=self._cfg.getint("FACTOR", "ma_slow_timeperiod", fallback=14),
            rsi_down=self._cfg.getint("FACTOR", "rsi_down", fallback=30),
            rsi_up=self._cfg.getint("FACTOR", "rsi_up", fallback=70),
        )

    def _init_apis(self) -> None:
        """初始化所有API接口"""
        flag = "1" if self.api_config.is_simulate else "0"

        _accountAPI = okx.Account.AccountAPI(
            api_key=self.api_config.api_key,
            api_secret_key=self.api_config.secret_key,
            passphrase=self.api_config.passphrase,
            use_server_time=False,
            proxy=self.api_config.proxy,
            flag=flag,
            debug=self.api_config.api_debug,
        )

        _tradeAPI = okx.Trade.TradeAPI(
            api_key=self.api_config.api_key,
            api_secret_key=self.api_config.secret_key,
            passphrase=self.api_config.passphrase,
            use_server_time=False,
            flag=flag,
            proxy=self.api_config.proxy,
            debug=self.api_config.api_debug,
        )

        _publicDataAPI = okx.PublicData.PublicAPI(
            flag=flag, proxy=self.api_config.proxy, debug=self.api_config.api_debug
        )

        _marketAPI = okx.MarketData.MarketAPI(
            flag=flag, proxy=self.api_config.proxy, debug=self.api_config.api_debug
        )
        self.api = APIService(_accountAPI, _marketAPI, _tradeAPI, _publicDataAPI)

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

    def print_cfg(self) -> None:
        """打印当前配置"""
        self.logger.info("=== API配置 ===")
        self.logger.info(f"API Key: {'*' * len(self.api_config.api_key)}")
        self.logger.info(f"Secret Key: {'*' * len(self.api_config.secret_key)}")
        self.logger.info(f"Passphrase: {'*' * len(self.api_config.passphrase)}")
        self.logger.info(f"Proxy: {self.api_config.proxy}")
        self.logger.info(f"模拟模式: {self.api_config.is_simulate}")
        self.logger.info(f"API Debug: {self.api_config.api_debug}")

        self.logger.info("\n=== 交易配置 ===")
        self.logger.info(f"交易币种: {self.trade_config.coin}")
        self.logger.info(f"交易周期: {self.trade_config.period}")
        self.logger.info(f"杠杆倍数: {self.trade_config.lever}")
        self.logger.info(f"保证金币种: {self.trade_config.ccy}")
        self.logger.info(f"保留金额: {self.trade_config.reserved}")
        self.logger.info(f"订单等待时间: {self.trade_config.order_wait}")
        self.logger.info(f"最大买入次数: {self.trade_config.max_buy_chance}")
        self.logger.info(f"交易时间周期: {self.trade_config.trade_timeperiod}")

        self.logger.info("\n=== 日志配置 ===")
        self.logger.info(f"日志文件: {self.log_config.filename}")
        self.logger.info(f"日志级别: {self.log_config.level}")

        self.logger.info("\n=== FACTOR配置 ===")
        self.logger.info(f"RSI 时间周期: {self.factor_config.rsi_timeperiod}")
        self.logger.info(f"MA 快速时间周期: {self.factor_config.ma_fast_timeperiod}")
        self.logger.info(f"MA 慢速时间周期: {self.factor_config.ma_slow_timeperiod}")
        self.logger.info(f"RSI 下限: {self.factor_config.rsi_down}")
        self.logger.info(f"RSI 上限: {self.factor_config.rsi_up}")
