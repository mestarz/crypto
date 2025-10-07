import os
import time
from pathlib import Path


class Config:
    """
    Configuration class for the entire project.
    """

    def __init__(self):
        config_path = Path(__file__).parent
        # =================================================================
        # 推理配置
        # =================================================================
        self.lookback_window = 256  # Number of past time steps for input.
        self.predict_window = 28  # Number of future time steps for prediction.
        self.max_context = 2048  # Maximum context length for the model.
        self.infer_predictor_path = f"{config_path}/kronos/model/weight/predictor"
        self.infer_tokenizer_path = f"{config_path}/kronos/model/weight/tokenizer"

        # =================================================================
        # 固定配置配置
        # =================================================================
        self.feature_list = ["open", "high", "low", "close", "vol", "amt"]
        self.time_feature_list = ["minute", "hour", "weekday", "day", "month"]
        self.adam_beta1 = 0.9
        self.adam_beta2 = 0.95
        self.adam_weight_decay = 0.1
        self.seed = int(time.time())  # Global random seed for reproducibility.
        self.accumulation_steps = 1

        self.device = "cpu"
