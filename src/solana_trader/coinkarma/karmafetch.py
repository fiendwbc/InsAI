"""
CoinKarma API 数据获取模块 - 获取加密货币指数数据
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, TypedDict

import requests

from dateutil import get_last_month_range
from descrypt import aes_decrypt_koma


# 类型定义
class PulseIndexPoint(TypedDict):
    time: str
    value: float


class LiqIndexPoint(TypedDict):
    time: str
    liq: Optional[float]
    value: Optional[float]


class LiqOverallPoint(TypedDict):
    time: str
    liq: Optional[float]
    value: Optional[float]


# 缓存目录
CACHE_DIR = "cache"


def _get_headers(token: str, device_id: str) -> Dict[str, str]:
    """
    构建 API 请求头

    Args:
        token: 认证令牌

    Returns:
        请求头字典
    """
    return {
        "accept": "text/*",
        "accept-language": "zh-CN,zh;q=0.9,ko;q=0.8,en;q=0.7,vi;q=0.6",
        "authorization": token,
        "content-type": "application/json",
        "priority": "u=1, i",
        "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "x-device-id": device_id,
        "Referer": "https://www.coinkarma.co/"
    }


def load_cache(key: str) -> Optional[List]:
    """
    从缓存文件加载数据

    Args:
        key: 缓存键（相对路径）

    Returns:
        缓存的数据，如果不存在返回 None
    """
    cache_path = os.path.join(CACHE_DIR, key)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载缓存失败 {cache_path}: {e}")
    return None


def save_cache(key: str, data: List):
    """
    保存数据到缓存文件

    Args:
        key: 缓存键（相对路径）
        data: 要缓存的数据
    """
    cache_path = os.path.join(CACHE_DIR, key)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存缓存失败 {cache_path}: {e}")


# ===============================
# Pulse Index APIs
# ===============================

def get_pulse_index(from_date: str, to_date: str, token: str, device_id: str) -> List[PulseIndexPoint]:
    """
    获取脉冲指数数据

    Args:
        from_date: 开始日期 (YYYY-MM-DD)
        to_date: 结束日期 (YYYY-MM-DD)
        token: 认证令牌

    Returns:
        脉冲指数数据点列表，按时间排序

    Raises:
        requests.RequestException: 请求失败
    """
    url = f"https://data.coinkarma.co/pulse-index?from={from_date}&to={to_date}"
    headers = _get_headers(token, device_id)

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # 解密数据
        dec_data = aes_decrypt_koma(response.text)

        # 转换为列表格式
        data: List[PulseIndexPoint] = [
            {"time": str(time), "value": float(value)}
            for time, value in dec_data.items()
        ]

        # 按时间排序
        data.sort(key=lambda x: x["time"])
        return data

    except requests.RequestException as e:
        print(f"请求失败: {e}")
        raise


def get_last_month_pulse_index(token: str, device_id: str) -> List[PulseIndexPoint]:
    """
    获取上个月的脉冲指数数据

    Args:
        token: 认证令牌

    Returns:
        脉冲指数数据点列表
    """
    today = datetime.now()
    date_range = get_last_month_range(today)
    return get_pulse_index(date_range["from"], date_range["to"], token, device_id)


# ===============================
# Liquidity Index APIs
# ===============================

def get_liq_index(
    symbol: str,
    from_date: str,
    to_date: str,
    token: str,
    device_id: str,
    cb: Optional[str] = None
) -> List[LiqIndexPoint]:
    """
    获取特定币种的流动性指数

    Args:
        symbol: 币种代码，例如 "btcusdt"
        from_date: 开始日期 (YYYY-MM-DD)
        to_date: 结束日期 (YYYY-MM-DD)
        token: 认证令牌
        cb: 可选的缓存破坏参数

    Returns:
        流动性指数数据点列表

    Raises:
        requests.RequestException: 请求失败
    """
    base = f"https://data.coinkarma.co/liq/{symbol}"
    url = f"{base}?from={from_date}&to={to_date}"
    if cb:
        url += f"&cb={cb}"

    headers = _get_headers(token,device_id)

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        dec_data = aes_decrypt_koma(response.text)

        data: List[LiqIndexPoint] = []
        for time, v in dec_data.items():
            point: LiqIndexPoint = {"time": str(time), "liq": None, "value": None}

            if isinstance(v, dict):
                point["liq"] = float(v["liq"]) if v.get("liq") is not None else None
                point["value"] = float(v["value"]) if v.get("value") is not None else None
            else:
                try:
                    num_val = float(v)
                    point["value"] = num_val if not (num_val != num_val) else None  # 检查 NaN
                except (ValueError, TypeError):
                    pass

            data.append(point)

        data.sort(key=lambda x: x["time"])
        return data

    except requests.RequestException as e:
        print(f"getLiqIndex 请求失败: {e}")
        raise


def get_liq_overall_index(
    from_date: str,
    to_date: str,
    token: str,
    device_id: str,
    cb: Optional[str] = None
) -> List[LiqOverallPoint]:
    """
    获取整体流动性指数

    Args:
        from_date: 开始日期 (YYYY-MM-DD)
        to_date: 结束日期 (YYYY-MM-DD)
        token: 认证令牌
        cb: 可选的缓存破坏参数

    Returns:
        整体流动性指数数据点列表

    Raises:
        requests.RequestException: 请求失败
    """
    base = "https://data.coinkarma.co/liq/overall"
    url = f"{base}?from={from_date}&to={to_date}"
    if cb:
        url += f"&cb={cb}"

    headers = _get_headers(token, device_id)

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        dec_data = aes_decrypt_koma(response.text)

        data: List[LiqOverallPoint] = []
        for time, v in dec_data.items():
            point: LiqOverallPoint = {"time": str(time), "liq": None, "value": None}

            if isinstance(v, dict):
                point["liq"] = float(v["liq"]) if v.get("liq") is not None else None
                point["value"] = float(v["value"]) if v.get("value") is not None else None
            else:
                try:
                    num_val = float(v)
                    point["value"] = num_val if not (num_val != num_val) else None
                except (ValueError, TypeError):
                    pass

            data.append(point)

        data.sort(key=lambda x: x["time"])
        return data

    except requests.RequestException as e:
        print(f"getLiqOverallIndex 请求失败: {e}")
        raise


# ===============================
# Cached day helpers
# ===============================

def get_pulse_index_day(date: str, token: str, device_id: str) -> List[PulseIndexPoint]:
    """
    获取指定日期的脉冲指数（带缓存）

    Args:
        date: 日期 (YYYY-MM-DD)
        token: 认证令牌

    Returns:
        脉冲指数数据点列表
    """
    key = f"pulse/{date}.json"
    cached = load_cache(key)
    if cached:
        return cached

    data = get_pulse_index(date, date, token, device_id)
    save_cache(key, data)
    return data


def get_liq_index_day(symbol: str, date: str, token: str) -> List[LiqIndexPoint]:
    """
    获取指定币种和日期的流动性指数（带缓存）

    Args:
        symbol: 币种代码
        date: 日期 (YYYY-MM-DD)
        token: 认证令牌

    Returns:
        流动性指数数据点列表
    """
    key = f"liq/{symbol}/{date}.json"
    cached = load_cache(key)
    if cached:
        return cached

    data = get_liq_index(symbol, date, date, token)
    save_cache(key, data)
    return data


def get_liq_overall_index_day(date: str, token: str) -> List[LiqOverallPoint]:
    """
    获取指定日期的整体流动性指数（带缓存）

    Args:
        date: 日期 (YYYY-MM-DD)
        token: 认证令牌

    Returns:
        整体流动性指数数据点列表
    """
    key = f"liq_overall/{date}.json"
    cached = load_cache(key)
    if cached:
        return cached

    data = get_liq_overall_index(date, date, token)
    save_cache(key, data)
    return data


if __name__ == "__main__":
    # 测试示例
    TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsImtpZCI6IjJZNHFPeEZWeHpDOEhxNG0iLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2VjdG55eG1ubHZvZnRqempjcXh4LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiIyYzI4MWIzMy0wODM1LTRhZmUtOTI3Yy04YmM3Y2Y0YjIwNDEiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzYyNDkxNzY4LCJpYXQiOjE3NjI0NzAxNjgsImVtYWlsIjoiZmllbmR3YmNAZ21haWwuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJnb29nbGUiLCJwcm92aWRlcnMiOlsiZ29vZ2xlIl19LCJ1c2VyX21ldGFkYXRhIjp7ImF2YXRhcl91cmwiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NMVDhBdlVLa2ZNSU40RVdRSW5UN1BZcTcwTENkbWsxdG9NOGJsQ09MZDFkNG42dWwzNT1zOTYtYyIsImVtYWlsIjoiZmllbmR3YmNAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZ1bGxfbmFtZSI6IkZ1Y2hlbiBXYW5nIiwiaXNzIjoiaHR0cHM6Ly9hY2NvdW50cy5nb29nbGUuY29tIiwibmFtZSI6IkZ1Y2hlbiBXYW5nIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jTFQ4QXZVS2tmTUlONEVXUUluVDdQWXE3MExDZG1rMXRvTThibENPTGQxZDRuNnVsMzU9czk2LWMiLCJwcm92aWRlcl9pZCI6IjEwOTkyMzA1Njk1NDgyMjIwNzcyOCIsInN1YiI6IjEwOTkyMzA1Njk1NDgyMjIwNzcyOCJ9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6Im9hdXRoIiwidGltZXN0YW1wIjoxNzYyMjQzOTI4fV0sInNlc3Npb25faWQiOiJhOTNkNjBlMS00NzE1LTQzODQtOTlkOC0wYjcwNGY2YWRhNmMiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.HaXsmpr9j22pIwsDt486YXonifNwEAS-BTpM1FjCXCI"
    DEVICE_ID = "8286013b4face8adef43bf93d1991ea5976c55e072a7ca3dfef9612caa54b93d"
    # 测试获取上个月的脉冲指数
    # data = get_last_month_pulse_index(TOKEN, DEVICE_ID)
    # print(f"获取到 {len(data)} 个数据点")

    # 测试获取特定币种的流动性指数
    btc_data = get_liq_index("btcusdt", "2025-11-01", "2025-11-06", TOKEN, DEVICE_ID)
    print(f"BTC 流动性指数: {len(btc_data)} 个数据点")
