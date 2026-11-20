# -*- coding: utf-8 -*-
"""结构指标、中心性与表 6-8 的入选规则。

计算范围（论文 3.3/3.4 节）：
  节点数、边数、密度             -> 全图
  平均路径长度、聚类系数、三类中心性 -> 最大连通分量
  聚类系数对度小于 2 的节点计 0

入选规则（表 6-8 列出哪些部门）：
  表 6、表 8  每期前 20%，含截断值处的并列
  表 7        高于该期"非零中介中心性的均值"；若全为 0 则列出全部
"""
from __future__ import annotations

import math

import networkx as nx

from common.graphs import lcc


def structure(graph: nx.Graph) -> dict:
    """返回表 4 / 表 5 需要的六个结构指标。

    n、m、density 在全图上算；lcc 是最大连通分量的节点数；
    apl 与 acc 在该分量上算，因为全图含孤立点时两者都没有意义。
    """
    n, m = graph.number_of_nodes(), graph.number_of_edges()
    core = lcc(graph)
    return {
        "n": n,
        "m": m,
        # 无向简单图的密度：实际边数 / 可能边数
        "density": 2 * m / (n * (n - 1)) if n > 1 else 0.0,
        "lcc": core.number_of_nodes(),
        "apl": nx.average_shortest_path_length(core) if core.number_of_nodes() > 1 else 0.0,
        "acc": nx.average_clustering(core) if core.number_of_nodes() > 1 else 0.0,
    }


def centralities(graph: nx.Graph) -> dict:
    """度、中介、接近三类中心性，均在该图的最大连通分量上计算。

    三个指标都用 NetworkX 的默认归一化。
    """
    core = lcc(graph)
    return {
        "degree": nx.degree_centrality(core),
        "betweenness": nx.betweenness_centrality(core, normalized=True),
        "closeness": nx.closeness_centrality(core),
    }


# --------------------------------------------------------------------------- #
# 表 6-8 的入选规则
# --------------------------------------------------------------------------- #
def select_top(values: dict, share: float = 0.20) -> list[tuple[str, float]]:
    """取前 20%，含截断值处的并列。

    做法：k = ceil(0.2n)，按数值降序排，第 k 名的数值即截断值，
    凡不低于它的节点全部入选。因此并列时入选人数会略多于 20%。
    """
    ranked = sorted(values.items(), key=lambda kv: -kv[1])
    if not ranked:
        return []
    k = max(1, math.ceil(share * len(ranked)))
    cutoff = ranked[k - 1][1]
    return [(name, value) for name, value in ranked if value >= cutoff - 1e-12]


def select_above_mean_nonzero(values: dict) -> list[tuple[str, float]]:
    """取高于"非零中介中心性均值"的节点（表 7 的规则）。"""
    nonzero = [v for v in values.values() if v > 0]
    if not nonzero:
        return sorted(values.items(), key=lambda kv: -kv[1])
    threshold = sum(nonzero) / len(nonzero)
    return sorted(((k, v) for k, v in values.items() if v > threshold), key=lambda kv: -kv[1])
