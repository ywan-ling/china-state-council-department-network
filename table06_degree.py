# -*- coding: utf-8 -*-
"""表 6：各期度中心性较高的部门。

规则：每期取前 20%（k = ceil(0.2n)），凡不低于第 k 名者全部列出，
      因此并列时人数会略多于 20%。
"""
from __future__ import annotations

import pandas as pd

from common import corpus, graphs, measures, output


def main() -> None:
    data = corpus.load_corpus()
    per_period = graphs.period_graphs(data)

    rows, blocks = [], []
    for period in data.periods:
        values = measures.centralities(per_period[period])["degree"]
        selected = measures.select_top(values)          # 前 20%，含并列
        for rank, (name, value) in enumerate(selected, start=1):
            rows.append({"Period": period, "Rank": rank, "Department": name,
                         "Abbreviation": data.abbr.get(name, name),
                         "Degree centrality": round(value, 4)})
        # 并排打印时用简称，宽度稳定
        blocks.append((period, [(data.abbr.get(n, n), round(v, 4)) for n, v in selected]))

    output.print_side_by_side(blocks)
    output.print_note("每期前 20%，含截断值并列；度中心性 = 度数 /(n-1)。")
    output.save_table(pd.DataFrame(rows), "table06_degree")


if __name__ == "__main__":
    main()
