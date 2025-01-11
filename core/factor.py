from dataclasses import dataclass
import numpy as np


@dataclass
class Factor:
    rsi: np.ndarray
    ma_fast: np.ndarray
    ma_slow: np.ndarray
