import requests
import pandas as pd
import time
from datetime import datetime
from core.okx.retry import retry

BASE_URL = "https://www.okx.com/api/v5/market/history-candles"
BAR = "5m"
LIMIT = 300  # OKX 每次最多 100 条


@retry()
def fetch_candles(coin: str, after=""):
    """从 OKX 获取一分钟 K 线数据"""
    params = {
        "instId": coin,
        "bar": BAR,
        "limit": LIMIT,
    }
    if after:
        params["after"] = after
    resp = requests.get(BASE_URL, params=params)
    data = resp.json()
    if data["code"] != "0":
        raise Exception(f"API Error: {data}")

    return data["data"]


def get_okx_data(coin: str, number: int):
    all_data = []
    before = ""

    while len(all_data) < number:
        candles = fetch_candles(coin, before)
        if not candles:
            break
        all_data.extend(candles)
        # 下一次请求的 before 参数用当前最后一条的时间戳
        before = f"{candles[-1][0]}"
        # time.sleep(0.05)  # 防止请求过快被限流

    # 只保留 TOTAL 条
    all_data = all_data[:number]

    # OKX 返回的数据是按时间倒序，需要翻转
    all_data.reverse()

    # 解析数据
    rows = []
    for one_data in all_data:
        ts, o, h, l, c, vol, amt, *_ = one_data
        timestamp = datetime.utcfromtimestamp(int(ts) / 1000).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        rows.append(
            [timestamp, float(o), float(h), float(l), float(c), float(vol), float(amt)]
        )

    columns = ["timestamps", "open", "high", "low", "close", "volume", "amount"]
    df = pd.DataFrame(rows, columns=columns)
    df["timestamps"] = pd.to_datetime(df["timestamps"])
    return df
