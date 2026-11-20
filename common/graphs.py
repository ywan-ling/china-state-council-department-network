# -*- coding: utf-8 -*-
"""由规章构建部门网络。

投影规则：一条由 k 个机构联合发布的规章，在 k 个机构之间建立 C(k,2) 条无向边。
机构名在清洗阶段已去重，因此不会出现自环；网络是简单无向图，同一对机构
多次联合发布只保留一条边（需要保留次数时用 build_weighted）。

全期网络用 joint_full（名称统一到 2025 年）；分期网络用 joint_phased
（名称在各时期内统一），时期列表由数据算出。
"""
from __future__ import annotations

import itertools

import networkx as nx

from common.corpus import Corpus


def build(bodies: list[list[str]]) -> nx.Graph:
    """把机构列表投影成无向图。

    bodies 中每一项是一条规章的机构列表；组合函数生成两两配对。
    """
    graph = nx.Graph()
    for members in bodies:
        graph.add_nodes_from(members)
        graph.add_edges_from(itertools.combinations(members, 2))
    return graph


def build_weighted(bodies: list[list[str]]) -> nx.Graph:
    """加权版本：边的权重等于两机构共同发布过的规章数。

    正文的九张表都用不到权重，这里保留是为了做稳健性检验
    """
    graph = nx.Graph()
    for members in bodies:
        graph.add_nodes_from(members)
        for pair in itertools.combinations(members, 2):
            if graph.has_edge(*pair):
                graph[pair[0]][pair[1]]["weight"] += 1
            else:
                graph.add_edge(*pair, weight=1)
    return graph


def lcc(graph: nx.Graph) -> nx.Graph:
    """取最大连通分量（诱导子图）。

    路径长度、聚类系数与三类中心性都只在这个分量上有意义：
    孤立节点会让平均路径长度无定义，也会把聚类系数拉低。
    """
    if graph.number_of_nodes() == 0:
        return graph
    return graph.subgraph(max(nx.connected_components(graph), key=len)).copy()


def period_graphs(corpus: Corpus) -> dict[str, nx.Graph]:
    """按时期构建五个网络，键的顺序即时间顺序。"""
    return {period: build(corpus.bodies(period)) for period in corpus.periods}