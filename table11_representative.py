# -*- coding: utf-8 -*-
"""表 11：各模式下的代表部门。

代表部门先按表 10 的规则分类，再在每一类里按发文总量降序
取前 PER_PATTERN 个。分类和排序都由数据决定，换数据会自动更新。
部门名用 name mapping 里的英文全称，比例保留两位小数。
"""
from __future__ import annotations

import pandas as pd

from common import corpus, output, typology

# 每一类展示几个部门。这是排版决定（表格宽度），不是数据结果。
PER_PATTERN = 4


def main() -> None:
    data = corpus.load_corpus()
    frame = typology.classify(data.department_counts())

    rows = []
    for pattern in typology.PATTERNS:
        subset = frame[frame["Pattern"] == pattern].sort_values(
            ["Total", "Joint"], ascending=False).head(PER_PATTERN)
        for _, row in subset.iterrows():
            rows.append({
                "Regulation-making pattern": pattern,
                "Department": row["English name"],
                "Total Regulations": int(row["Total"]),
                "Jointly Issued Regulations": int(row["Joint"]),
                "Proportion of Jointly Issued Regulations (%)": round(float(row["Share"]), 2),
            })

    table = pd.DataFrame(rows)
    output.print_table(table, "表 11  各模式的代表部门")
    output.print_note("分类由表 10 的规则得出；每类按发文总量取前 %d 个，不是手工指定。"
                      % PER_PATTERN)
    output.save_table(table, "table11_representative")


if __name__ == "__main__":
    main()
