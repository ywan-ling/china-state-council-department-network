# -*- coding: utf-8 -*-
"""图 3：五个时期的部门协作网络（2×3 面板）。

流程：
  1. 按数据里的时期列表逐期建网；
  2. 算五期合并的全局度数极差，让各期节点大小可比；
  3. 2×3 面板，前五格画网络，第六格放图例；
  4. 每格的全部节点都标注简称，标题形如 (a) 1978-1988。
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import corpus, graphs, output, plotting


def main() -> None:
    data = corpus.load_corpus()
    per_period = graphs.period_graphs(data)

    fig, axes = plt.subplots(2, 3, figsize=(22, 14), dpi=300)
    fig.patch.set_facecolor("white")
    axes = axes.flatten()

    # 全局极差：所有时期的节点放在同一尺度上比较
    degree_range = plotting.global_degree_range([per_period[p] for p in data.periods])
    labels = data.period_labels()

    for idx, period in enumerate(data.periods):
        plotting.draw_period_network(per_period[period], data.abbr, axes[idx],
                                     title=labels[period],
                                     degree_range=degree_range)

    # 第六格只放图例，不画网络
    axes[5].legend(handles=plotting.legend_handles(), loc="center",
                   frameon=True, framealpha=0.95, facecolor="white",
                   edgecolor="#d0d0d0", fontsize=14, labelcolor="#333333",
                   handlelength=2, handletextpad=1.2, labelspacing=1.5)
    axes[5].axis("off")

    plt.subplots_adjust(left=0.04, right=0.96, top=0.94, bottom=0.05,
                        wspace=0.25, hspace=0.35)

    path = output.save_figure(fig, "figure04_period_panels")
    plt.close(fig)

    print(f"图 4 已写入 {path}")
    for period in data.periods:
        g = per_period[period]
        print(f"  {period:<11} 节点 {g.number_of_nodes():>3}  边 {g.number_of_edges():>4}")


if __name__ == "__main__":
    main()
