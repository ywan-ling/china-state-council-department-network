# -*- coding: utf-8 -*-
"""图 2：全期部门协作网络。

流程：
  1. 用全部联合发文构建网络（92 节点 / 756 边）；
  2. spring 布局 + 重叠微调；
  3. 曲线边、四档配色节点、全部节点标注简称；
  4. 右上角图例，16×12 英寸，300 dpi 作图、600 dpi 保存。
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")          # 无显示环境下必须用非交互后端
import matplotlib.pyplot as plt

from common import corpus, graphs, output, plotting


def main() -> None:
    data = corpus.load_corpus()
    graph = graphs.build(data.bodies())

    fig, ax = plt.subplots(figsize=(16, 12), dpi=300)
    fig.patch.set_facecolor("white")

    plotting.draw_full_network(graph, data.abbr, ax)

    ax.legend(handles=plotting.legend_handles(), loc="upper right",
              frameon=True, framealpha=0.95, facecolor="white",
              edgecolor="#d0d0d0", fontsize=10, labelcolor="#333333")
    plt.tight_layout()

    path = output.save_figure(fig, "figure03_full_network")
    plt.close(fig)

    print(f"图 3 已写入 {path}（{graph.number_of_nodes()} 个节点、"
          f"{graph.number_of_edges()} 条边）")


if __name__ == "__main__":
    main()
