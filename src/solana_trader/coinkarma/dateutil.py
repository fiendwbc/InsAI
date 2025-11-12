"""
日期工具模块 - 处理日期范围计算和格式化
"""
from datetime import datetime, timedelta
from typing import Dict


def get_last_month_range(date: datetime = None) -> Dict[str, str]:
    """
    获取上个月的日期范围

    Args:
        date: 指定日期，默认为当前日期

    Returns:
        包含 'from' 和 'to' 键的字典，值为 YYYY-MM-DD 格式的日期字符串
    """
    if date is None:
        date = datetime.now()

    to = format_date(date)

    # 获取上个月的年和月
    year = date.year
    month = date.month

    if month == 1:
        year -= 1
        month = 12
    else:
        month -= 1

    # 上个月的天数
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)

    last_day_of_month = (next_month - timedelta(days=1)).day

    # 如果今天的日大于上个月最大天数，就用上个月最后一天
    day = min(date.day, last_day_of_month)

    from_date = datetime(year, month, day)
    from_str = format_date(from_date)

    return {"from": from_str, "to": to}


def format_date(date: datetime) -> str:
    """
    格式化日期为 YYYY-MM-DD 格式

    Args:
        date: datetime 对象

    Returns:
        YYYY-MM-DD 格式的日期字符串
    """
    return date.strftime("%Y-%m-%d")


def test_full_year(year: int):
    """
    测试一年 365 天的日期范围计算

    Args:
        year: 要测试的年份
    """
    start = datetime(year, 1, 1)

    for i in range(365):
        current = start + timedelta(days=i)
        result = get_last_month_range(current)
        print(f"日期: {format_date(current)} | from: {result['from']} | to: {result['to']}")


if __name__ == "__main__":
    # 测试示例
    result = get_last_month_range()
    print(f"当前日期的上月范围: {result}")

    # 测试特定日期
    test_date = datetime(2024, 3, 31)
    result = get_last_month_range(test_date)
    print(f"2024-03-31 的上月范围: {result}")
