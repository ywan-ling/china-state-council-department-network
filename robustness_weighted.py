# -*- coding: utf-8 -*-
"""稳健性检验：二值网络 vs 加权网络（对应表 6、7、8 的三个中心性）。

用途
----
论文的主体网络是二值的：两个机构只要共同发布过规章就连一条边，
不论合作 1 次还是 10 次。本脚本用合作次数作权重重算三个中心性，
再与二值结果比较：

  * Spearman 秩相关：两个排名的一致性（1 表示完全一致），并给出双侧 p 值；
  * 前 20% 名单重叠：按每张表的入选规则各取一次，看交集多少。

关键实现细节
------------
NetworkX 里 weight 表示"距离"，数值越大越远。合作次数是"越强越近"，
所以加权中介与加权接近必须先取倒数 1/w 作为距离，否则等于让算法偏好弱关系。
加权度（强度）直接用权重求和，不涉及路径，不需要取倒数。

输出
----
终端打印一张表，并写 output/tables/robustness_weighted.csv。
"""
from __future__ import annotations

import math

import networkx as nx
import pandas as pd

from common import corpus, graphs, measures, output
from common.stats import rank_correlation, format_p


def _weighted_metrics(graph: nx.Graph) -> dict:
    """在最大连通分量上计算加权指标。

    返回三个字典：strength（加权度）、betweenness（加权中介）、
    closeness（加权接近）。节点名与二值版本完全相同，可以直接比排名。
    """
    core = graphs.lcc(graph)

    # 合作次数 -> 距离：次数越多，距离越短
    for _, _, data in core.edges(data=True):
        data["distance"] = 1.0 / data["weight"]

    strength = {
        node: sum(d["weight"] for _, _, d in core.edges(node, data=True))
        for node in core.nodes()
    }
    return {
        "strength": strength,
        "betweenness": nx.betweenness_centrality(core, weight="distance", normalized=True),
        "closeness": nx.closeness_centrality(core, distance="distance"),
    }


def _overlap(binary: dict, weighted: dict, rule: str) -> tuple[int, int]:
    """两份名单的重叠，返回 (交集个数, 二值名单大小)。

    rule="top"  用前 20%（表 6、表 8 的规则）
    rule="mean" 用高于非零均值（表 7 的规则）
    """
    select = measures.select_top if rule == "top" else measures.select_above_mean_nonzero
    top_binary = {name for name, _ in select(binary)}
    top_weighted = {name for name, _ in select(weighted)}
    return len(top_binary & top_weighted), len(top_binary)


def main() -> None:
    data = corpus.load_corpus()

    rows = []
    for period in data.periods:
        bodies = data.bodies(period)

        # 二值版本：与表 6-8 完全相同的口径
        binary_graph = graphs.build(bodies)
        binary = measures.centralities(binary_graph)

        # 加权版本：拓扑相同，边多了合作次数
        weighted_graph = graphs.build_weighted(bodies)
        weighted = _weighted_metrics(weighted_graph)

        # 描述性信息：多少条边是重复合作
        core = graphs.lcc(weighted_graph)
        repeats = sum(1 for _, _, d in core.edges(data=True) if d["weight"] > 1)

        rho_degree, p_degree = rank_correlation(binary["degree"], weighted["strength"])
        rho_between, p_between = rank_correlation(binary["betweenness"], weighted["betweenness"])
        rho_close, p_close = rank_correlation(binary["closeness"], weighted["closeness"])

        overlap_degree = _overlap(binary["degree"], weighted["strength"], "top")
        overlap_between = _overlap(binary["betweenness"], weighted["betweenness"], "mean")
        overlap_close = _overlap(binary["closeness"], weighted["closeness"], "top")

        rows.append({
            "Period": period,
            "Nodes": core.number_of_nodes(),
            "Edges": core.number_of_edges(),
            "Repeat edges": repeats,
            "Repeat share (%)": round(100 * repeats / core.number_of_edges(), 1)
                                if core.number_of_edges() else 0.0,
            "Spearman degree": round(rho_degree, 3) if not math.isnan(rho_degree) else None,
            "p degree": format_p(p_degree),
            "Spearman betweenness": round(rho_between, 3) if not math.isnan(rho_between) else None,
            "p betweenness": format_p(p_between),
            "Spearman closeness": round(rho_close, 3) if not math.isnan(rho_close) else None,
            "p closeness": format_p(p_close),
            "Overlap degree": f"{overlap_degree[0]}/{overlap_degree[1]}",
            "Overlap betweenness": f"{overlap_between[0]}/{overlap_between[1]}",
            "Overlap closeness": f"{overlap_close[0]}/{overlap_close[1]}",
        })

    table = pd.DataFrame(rows)
    output.print_table(table, "稳健性：二值网络 vs 加权网络")
    output.print_note(
        "加权网络的拓扑与二值网络完全相同，区别只在边的权重（共同发布次数）；"
        "加权中介与加权接近按距离 = 1/权重计算。"
        "p 为 Spearman 相关的双侧检验（t 近似，df = n-2），并列采用平均秩。"
        "P1 只有 5 个节点、无重复合作，各指标全部并列，故相关系数无法计算（—）。"
    )
    output.save_table(table, "robustness_weighted")


if __name__ == "__main__":
    main()