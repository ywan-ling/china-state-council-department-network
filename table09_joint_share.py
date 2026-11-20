# -*- coding: utf-8 -*-
"""表 9：各期独立发文与联合发文的占比。

与表 2 同源：占比 = 该类条数 / 该期总数，保留两位小数。
合计行按条数加权（总单一/总合计），不是各期百分比的平均。
"""
from __future__ import annotations

import pandas as pd

from common import corpus, output


def main() -> None:
    data = corpus.load_corpus()
    counts = data.counts_by_period()

    table = pd.DataFrame({
        "Period": counts["Period"],
        "Total": counts["Total"],
        "Single-department (%)": (100 * counts["Single"] / counts["Total"]).round(2),
        "Jointly issued (%)": (100 * counts["Joint"] / counts["Total"]).round(2),
    })
    total = pd.DataFrame([{
        "Period": "Total",
        "Total": int(counts["Total"].sum()),
        "Single-department (%)": round(100 * counts["Single"].sum() / counts["Total"].sum(), 2),
        "Jointly issued (%)": round(100 * counts["Joint"].sum() / counts["Total"].sum(), 2),
    }])
    table = pd.concat([table, total], ignore_index=True)

    output.print_table(table, "表 9  独立与联合发文比例")
    output.print_note("占比以该期全部部门规章为分母；合计行按条数加权。")
    output.save_table(table, "table09_joint_share")


if __name__ == "__main__":
    main()
