# -*- coding: utf-8 -*-
"""表 4：全期网络的结构指标。

六个指标都由 measures.structure() 一次算出：
  节点数、边数、密度在全图上算；
  最大连通分量、平均路径长度、平均聚类系数中，后两个在该分量上算。
"""
from __future__ import annotations

import pandas as pd

from common import corpus, graphs, measures, output


def main() -> None:
    data = corpus.load_corpus()
    graph = graphs.build(data.bodies())      # 全部 258 条联合发文
    stats = measures.structure(graph)

    table = pd.DataFrame({
        "Measure": ["Network size (nodes)", "Number of ties", "Network density",
                    "Largest connected component", "Average path length",
                    "Average clustering coefficient"],
        "Value": [stats["n"], stats["m"], round(stats["density"], 4), stats["lcc"],
                  round(stats["apl"], 4), round(stats["acc"], 4)],
    })
    output.print_table(table, "表 4  全期网络结构")
    output.print_note("密度用全图；平均路径长度与聚类系数用最大连通分量，"
                      "度小于 2 的节点在聚类系数中计 0。")
    output.save_table(table, "table04_full_network")


if __name__ == "__main__":
    main()
