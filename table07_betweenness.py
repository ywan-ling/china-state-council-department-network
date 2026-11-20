# -*- coding: utf-8 -*-
"""表 7：各期中介中心性较高的部门。

规则：阈值取该期"非零中介中心性的均值"，高于阈值者列出；
      第一期三个节点构成三角形、全部为 0，此时列出全部节点。
"""
from __future__ import annotations

import pandas as pd

from common import corpus, graphs, measures, output


def main() -> None:
    data = corpus.load_corpus()
    per_period = graphs.period_graphs(data)

    rows, blocks = [], []
    for period in data.periods:
        values = measures.centralities(per_period[period])["betweenness"]
        selected = measures.select_above_mean_nonzero(values)
        for rank, (name, value) in enumerate(selected, start=1):
            rows.append({"Period": period, "Rank": rank, "Department": name,
                         "Abbreviation": data.abbr.get(name, name),
                         "Betweenness": round(value, 4)})
        blocks.append((period, [(data.abbr.get(n, n), round(v, 4)) for n, v in selected]))

    output.print_side_by_side(blocks)
    output.print_note("阈值为该期非零中介中心性的均值；数值按 1/((n-1)(n-2)) 归一化。")
    output.save_table(pd.DataFrame(rows), "table07_betweenness")


if __name__ == "__main__":
    main()
