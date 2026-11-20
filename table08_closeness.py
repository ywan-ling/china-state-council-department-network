# -*- coding: utf-8 -*-
"""表 8：各期接近中心性较高的部门。

规则：每期取前 20%，含截断值并列。
"""
from __future__ import annotations

import pandas as pd

from common import corpus, graphs, measures, output


def main() -> None:
    data = corpus.load_corpus()
    per_period = graphs.period_graphs(data)

    rows, blocks, means = [], [], []
    for period in data.periods:
        values = measures.centralities(per_period[period])["closeness"]
        selected = measures.select_top(values)
        for rank, (name, value) in enumerate(selected, start=1):
            rows.append({"Period": period, "Rank": rank, "Department": name,
                         "Abbreviation": data.abbr.get(name, name),
                         "Closeness": round(value, 4)})
        blocks.append((period, [(data.abbr.get(n, n), round(v, 4)) for n, v in selected]))
        means.append(sum(values.values()) / len(values))

    output.print_side_by_side(blocks)
    print("\n  各期接近中心性均值：" + "，".join(
        f"{p}={m:.2f}" for p, m in zip(data.periods, means)))
    output.print_note("每期前 20%，含截断值并列；在最大连通分量内计算。")
    output.save_table(pd.DataFrame(rows), "table08_closeness")


if __name__ == "__main__":
    main()
