# backend/stats_utils.py
"""
统计计算工具函数（统一定义，避免代码重复）
用于 OpenDigger 数据分析
"""
import math
from typing import List, Dict, Any, Optional


def mean(values: List[float]) -> float:
    """
    计算平均值
    
    Args:
        values: 数值列表
    Returns:
        平均值，空列表返回 0.0
    """
    return sum(values) / len(values) if values else 0.0


def std_population(values: List[float]) -> float:
    """
    计算总体标准差（Population Standard Deviation）
    
    Args:
        values: 数值列表
    Returns:
        标准差，空列表返回 0.0
    """
    if not values:
        return 0.0
    m = mean(values)
    variance = sum((x - m) ** 2 for x in values) / len(values)
    return math.sqrt(variance)


def tail_n_values(
    records: List[Dict[str, Any]], 
    n: int = 12,
    month_key: str = "month",
    value_key: str = "count"
) -> List[float]:
    """
    从月度记录中提取最近 n 个月的数值
    
    Args:
        records: 记录列表，格式如 [{"month": "2024-01", "count": 123}, ...]
        n: 取最近多少个月，默认 12
        month_key: 月份字段名，默认 "month"
        value_key: 数值字段名，默认 "count"
    Returns:
        数值列表
    """
    if not records:
        return []
    
    # 按月份排序
    sorted_records = sorted(records, key=lambda r: r.get(month_key, ""))
    
    # 取最后 n 条
    tail = sorted_records[-n:]
    
    # 提取数值，过滤 None
    values = []
    for r in tail:
        val = r.get(value_key)
        if val is not None:
            try:
                values.append(float(val))
            except (ValueError, TypeError):
                continue
    
    return values


def calculate_health_score(
    openrank_norm: float,
    activity_norm: float,
    stability_norm: float,
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    计算项目健康度得分
    
    Args:
        openrank_norm: 归一化的 OpenRank 值 (0-1)
        activity_norm: 归一化的活跃度值 (0-1)
        stability_norm: 归一化的稳定性值 (0-1)，值越高越稳定
        weights: 权重配置，默认 {"openrank": 0.5, "activity": 0.3, "stability": 0.2}
    Returns:
        健康度得分 (0-1)
    """
    if weights is None:
        weights = {"openrank": 0.5, "activity": 0.3, "stability": 0.2}
    
    score = (
        weights["openrank"] * openrank_norm +
        weights["activity"] * activity_norm +
        weights["stability"] * stability_norm
    )
    return round(score, 4)