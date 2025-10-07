import pandas as pd
import numpy as np
from core.config import Config
from core.kronos.model.kronos import Kronos, KronosTokenizer, KronosPredictor

configs = Config()

# 1. Load Model and Tokenizer
tokenizer = KronosTokenizer.from_pretrained(configs.infer_tokenizer_path)
model = Kronos.from_pretrained(configs.infer_predictor_path)

# 2. Instantiate Predictor
predictor = KronosPredictor(
    model, tokenizer, device=configs.device, max_context=configs.max_context
)


def infer_predict(dfs: list, tps: list):
    # 时间序列外推
    diff_tp = tps[0].iloc[1] - tps[0].iloc[0]
    last_dates = [tp.iloc[-1] for tp in tps]
    future_dates = [
        [last_date + (i + 1) * diff_tp for i in range(configs.predict_window)]
        for last_date in last_dates
    ]
    future_series = [
        pd.Series(future_date, dtype=tps[0]) for future_date in future_dates
    ]

    # 每个coin推理8次做平均
    k = 8
    idfs = [df for _ in range(k) for df in dfs]
    itps_x = [tp for _ in range(k) for tp in tps]
    itps_y = [fs for _ in range(k) for fs in future_series]

    pred_df = predictor.predict_batch(
        df_list=idfs,
        x_timestamp_list=itps_x,
        y_timestamp_list=itps_y,
        pred_len=configs.predict_window,
    )

    close_list = [df["close"].iloc[-1] for df in dfs]
    infer_return = []
    for idx in range(len(dfs)):
        rs = [pred_df[i + idx] for i in range(0, len(pred_df), len(dfs))]
        result = [df["close"].iloc[-1] for df in rs]
        result = sorted(result)

        n_avg = np.average(result)
        n_start = close_list[idx]
        count_gtn = sum(1 for x in result if x > n_start)
        up_precent = count_gtn / len(result)
        avg_precent = (n_avg - n_start) / n_start

        infer_return.append([up_precent, avg_precent])

    return infer_return
