# -*- coding: utf-8 -*-
"""四类规章制定模式（表 10、表 11）。

两个维度：
  发文总量      该机构签字的全部规章数（单一 + 联合各计一次）
  联合发文占比  联合发文数 / 发文总量

两个维度各自取**本语料的中位数**作高/低分界，交叉后得到四类。
"""
from __future__ import annotations

import pandas as pd

# 四个类别的英文名，按"高—高、高—低、低—高、低—低"的顺序排列，
# 仅用于排序与输出，不参与判定。
PATTERNS = ["Active-Collaborative", "Independent-Dominant",
            "Collaborative-Participatory", "Low-Participation"]


def thresholds(frame: pd.DataFrame) -> tuple[float, float]:
    """返回两个维度的切分点：发文总量中位数、联合占比中位数。

    frame 需含 Total 与 Share 两列（department_counts 的输出）。
    """
    return float(frame["Total"].median()), float(frame["Share"].median())


def classify(frame: pd.DataFrame) -> pd.DataFrame:
    """按两个中位数把部门分成四类，新增 Pattern 列。

    判定规则没有例外：
      * 等于中位数算"高"；
      * 联合占比 0% 与 100% 都能正常归类；
      * 四个分支互斥且穷尽。
    """
    total_cut, share_cut = thresholds(frame)

    def label(row) -> str:
        high_total = row["Total"] >= total_cut
        high_share = row["Share"] >= share_cut
        if high_total and high_share:
            return "Active-Collaborative"
        if high_total and not high_share:
            return "Independent-Dominant"
        if not high_total and high_share:
            return "Collaborative-Participatory"
        return "Low-Participation"

    out = frame.copy()
    out["Pattern"] = out.apply(label, axis=1)
    return out
