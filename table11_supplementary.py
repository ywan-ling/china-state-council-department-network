# -*- coding: utf-8 -*-
"""表 11 的补充材料：各模式下全部部门的完整名单。

正文表 11 每类只列 4 个代表部门；本脚本输出全部部门。

排序：先按类别（Active → Independent → Collaborative → Low），
组内按发文总量降序、联合数降序；Rank 是组内序号。
"""
from __future__ import annotations

import pandas as pd

from common import corpus, output, typology


def main() -> None:
    data = corpus.load_corpus()
    frame = typology.classify(data.department_counts())

    rows = []
    for pattern in typology.PATTERNS:
        subset = frame[frame["Pattern"] == pattern].sort_values(
            ["Total", "Joint"], ascending=False
        )
        for rank, (_, row) in enumerate(subset.iterrows(), start=1):
            rows.append({
                "Regulation-making pattern": pattern,
                "Rank": rank,
                "Department": row["English name"],
                "Abbreviation": row["Abbreviation"],
                "Total Regulations": int(row["Total"]),
                "Jointly Issued Regulations": int(row["Joint"]),
                "Proportion of Jointly Issued Regulations (%)": round(float(row["Share"]), 2),
            })

    table = pd.DataFrame(rows)
    output.print_table(table, "表 11 补充材料  各模式全部部门")
    output.print_note(
        "共 %d 个部门。分类规则与正文表 10 相同（两个维度的中位数二分）；"
        "正文表 11 只列每类前 4 个。" % len(table)
    )
    output.save_table(table, "table11_supplementary")


if __name__ == "__main__":
    main()