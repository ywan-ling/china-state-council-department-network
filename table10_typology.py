# -*- coding: utf-8 -*-
"""表 10：规章制定模式的 2×2 矩阵。

论文里的表 10 是纯文字的矩阵（行=发文总量高/低，列=联合占比高/低），不含数字。
两个维度的切分点取本语料的中位数，由 typology.thresholds() 算出。

本脚本输出两样东西：
  1. 两个切分点及其两侧的部门数（终端打印，并存为 table10_thresholds.csv）；
  2. 纯文字的 2×2 矩阵。

部门明细在 table11_supplementary.py 里。
"""
from __future__ import annotations

import pandas as pd

from common import corpus, output, typology


def main() -> None:
    data = corpus.load_corpus()
    counts = data.department_counts()
    total_cut, share_cut = typology.thresholds(counts)

    # ---- 一、切分点：中位数及两侧的部门数 --------------------------------
    thresholds = pd.DataFrame([
        {
            "Dimension": "Total regulations",
            "Median": total_cut,
            "Departments >= median": int((counts["Total"] >= total_cut).sum()),
            "Departments < median": int((counts["Total"] < total_cut).sum()),
        },
        {
            "Dimension": "Jointly issued (%)",
            "Median": share_cut,
            "Departments >= median": int((counts["Share"] >= share_cut).sum()),
            "Departments < median": int((counts["Share"] < share_cut).sum()),
        },
    ])
    output.print_table(thresholds, "表 10 的两个切分点（中位数）")
    output.save_table(thresholds, "table10_thresholds")

    # ---- 二、纯文字的 2×2 矩阵 ------------------------------------------
    matrix = pd.DataFrame(
        [["High", "Active-Collaborative", "Independent-Dominant"],
         ["Low", "Collaborative-Participatory", "Low-Participation"]],
        columns=["Total Number of Departmental Regulations",
                 "High co-issuance proportion", "Low co-issuance proportion"],
    )
    output.print_table(matrix, "表 10  规章制定模式（文字矩阵）")
    output.print_note("切分点取本语料中位数：发文总量 %.1f 条，联合占比 %.2f%%；"
                      "等于中位数算高。" % (total_cut, share_cut))


if __name__ == "__main__":
    main()