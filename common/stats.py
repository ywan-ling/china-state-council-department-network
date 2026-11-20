# -*- coding: utf-8 -*-
"""秩相关及其显著性检验。"""
from __future__ import annotations

import math
import warnings

from scipy.stats import spearmanr


def rank_correlation(a: dict, b: dict) -> tuple[float, float]:
    """两个排名的 Spearman 相关与双侧 p 值。

    只比较两边都有的键；并列用平均秩；样本少于 3 个时返回 (nan, nan)。
    """
    keys = [k for k in a if k in b]
    if len(keys) < 3:
        return float("nan"), float("nan")

    x = [a[k] for k in keys]
    y = [b[k] for k in keys]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")      # 并列时 scipy 会提示，这里不需要
        rho, p = spearmanr(x, y)
    return float(rho), float(p)


def format_p(p: float) -> str:
    """p 值的显示格式：小于 0.001 统一写 <0.001，无法计算写 —。"""
    if p is None or math.isnan(p):
        return "—"
    return "<0.001" if p < 0.001 else f"{p:.3f}"