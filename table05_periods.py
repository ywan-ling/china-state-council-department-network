# -*- coding: utf-8 -*-
"""表 5：五个时期的网络结构指标。

第一行是各期联合发文条数（来自 counts_by_period 的 Joint 列），
其后依次是节点、边、密度、最大连通分量、平均路径长度、平均聚类系数。
时期顺序取自数据。
"""
from __future__ import annotations

import pandas as pd

from common import corpus, graphs, measures, output

LABELS = ["Jointly Issued Regulations", "Network Size (Number of Nodes)",
          "Number of Ties", "Network Density", "Largest Connected Component (LCC)",
          "Average Path Length (APL)", "Average Clustering Coefficient (ACC)"]


def main() -> None:
    data = corpus.load_corpus()
    per_period = graphs.period_graphs(data)
    counts = data.counts_by_period().set_index("Period")

    columns = {}
    for period in data.periods:
        s = measures.structure(per_period[period])
        # 顺序必须与 LABELS 一一对应
        columns[period] = [int(counts.loc[period, "Joint"]), s["n"], s["m"],
                           round(s["density"], 4), s["lcc"],
                           round(s["apl"], 4), round(s["acc"], 4)]

    table = pd.DataFrame({"Measure": LABELS, **columns})
    output.print_table(table, "表 5  分期网络结构")
    output.print_note("密度用全图；平均路径长度与聚类系数用最大连通分量。")
    output.save_table(table, "table05_periods")


if __name__ == "__main__":
    main()
