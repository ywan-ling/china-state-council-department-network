# -*- coding: utf-8 -*-
"""两张网络图的绘制。

图 2（全期）：
  spring 布局，边是二次贝塞尔曲线、曲率随距离放大，节点 200-1500，
  四档配色，**全部节点**标注简称。

图 3（分期五面板）：
  2×3 网格，节点数 ≤6 时用星形布局，否则按度数分四层同心圆；
  节点大小按五期合并后的全局度数极差缩放，使各期可比；全部节点标注。

两张图的差别只在布局与曲率公式，配色、标注、图例规则是共用的。
"""
from __future__ import annotations

import math
import textwrap

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

import config


def _colour(degree: int) -> str:
    """按度数取节点颜色：≥20 红、10-19 橙、5-9 蓝、<5 青。"""
    for threshold, colour in config.DEGREE_TIERS:
        if degree >= threshold:
            return colour
    return config.DEGREE_TIERS[-1][1]


def _sizes(graph: nx.Graph, min_size: float, max_size: float,
           deg_min: float | None = None, deg_max: float | None = None) -> dict:
    """按度数的平方根缩放节点面积。

    用平方根而不是线性，是因为节点面积与半径平方成正比，
    直接线性缩放会让高度数节点大得离谱。
    deg_min / deg_max 可传入统一的极差（图 3 用五期合并的全局极差），
    这样各期节点大小可以直接比较。
    """
    degrees = dict(graph.degree())
    lo = min(degrees.values()) if deg_min is None else deg_min
    hi = max(degrees.values()) if deg_max is None else deg_max
    if hi == lo:
        return {n: min_size for n in graph.nodes()}
    return {
        n: min_size + (max_size - min_size) * math.sqrt((degrees[n] - lo) / (hi - lo))
        for n in graph.nodes()
    }


def _spring_positions(graph: nx.Graph) -> dict:
    """spring 布局 + 50 轮节点重叠微调。"""
    pos = nx.spring_layout(graph, k=2.0 / math.sqrt(graph.number_of_nodes()),
                           iterations=800, scale=15, seed=42, weight=None)
    nodes = list(graph.nodes())
    for _ in range(50):
        positions = np.array([pos[n] for n in nodes])
        diff = positions[:, None, :] - positions[None, :, :]
        distances = np.sqrt((diff ** 2).sum(-1))
        np.fill_diagonal(distances, np.inf)   # 自己与自己不算重叠
        too_close = distances < 1
        if not too_close.any():
            break
        for i, j in zip(*np.where(too_close)):
            vector = positions[i] - positions[j]
            norm = np.linalg.norm(vector)
            if norm > 0:
                adjustment = vector / norm * (0.8 - norm) / 2
                pos[nodes[i]] = pos[nodes[i]] + adjustment
                pos[nodes[j]] = pos[nodes[j]] - adjustment
    return pos


def _period_positions(graph: nx.Graph) -> dict:
    """分期图的布局。

    节点数 ≤6（第一期）：星形——度数最大者居中，其余均匀排在一个圆上；
    否则按度数把节点分成四层（10% / 20% / 40% / 30%），
    分别放在半径 1.5 / 3.5 / 6 / 8.5 的同心圆上，核心在外圈、边缘在外圈之外，
    一眼能看出核心—边缘结构。
    """
    nodes = list(graph.nodes())
    degree = dict(graph.degree())
    pos: dict = {}

    if len(nodes) <= 6:
        center = max(nodes, key=lambda n: degree[n])
        pos[center] = (0.0, 0.0)
        others = [n for n in nodes if n != center]
        if others:
            angles = np.linspace(math.pi / 2, math.pi / 2 + 2 * math.pi, len(others), endpoint=False)
            for n, a in zip(others, angles):
                pos[n] = (2.5 * math.cos(a), 2.5 * math.sin(a))
        return pos

    ordered = sorted(nodes, key=lambda n: degree[n], reverse=True)
    n = len(ordered)
    layers = {
        0: ordered[:max(1, int(n * 0.1))],
        1: ordered[max(1, int(n * 0.1)):max(2, int(n * 0.3))],
        2: ordered[max(2, int(n * 0.3)):max(3, int(n * 0.7))],
        3: ordered[max(3, int(n * 0.7)):],
    }
    radius = {0: 1.5, 1: 3.5, 2: 6.0, 3: 8.5}
    for layer, members in layers.items():
        if not members:
            continue
        angles = np.linspace(math.pi / 2, math.pi / 2 + 2 * math.pi, len(members), endpoint=False)
        for node, angle in zip(members, angles):
            pos[node] = (radius[layer] * math.cos(angle), radius[layer] * math.sin(angle))
    return pos


def _curved_edges(ax, graph: nx.Graph, pos: dict, bend_num: float, bend_den: float,
                  scale_by_distance: bool = False) -> None:
    """把每条边画成二次贝塞尔曲线。

    曲率 = bend_num / (1 + bend_den × 边长)。控制点取在中点沿法线方向偏移，
    所以边都是弯的，密集区域不会糊成一片。
    scale_by_distance 控制偏移量是否随边长放大：
      图 2 为 True（长边弯得更明显），图 3 为 False（长短边弯曲程度一致）。
    """
    for u, v in graph.edges():
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        dist = math.hypot(dx, dy)
        if dist > 0:
            bend = bend_num / (1 + dist * bend_den)
            if scale_by_distance:
                bend *= dist
            cx, cy = mx - dy / dist * bend, my + dx / dist * bend
        else:
            cx, cy = mx, my
        t = np.linspace(0, 1, 50)   # 每条边取 50 个点，足够平滑
        bx = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * cx + t ** 2 * x2
        by = (1 - t) ** 2 * y1 + 2 * (1 - t) * t * cy + t ** 2 * y2
        ax.plot(bx, by, color="#b0b0b0", linewidth=0.8, alpha=0.4, zorder=1)


def _labels(ax, graph: nx.Graph, pos: dict, abbr: dict, sizes: dict) -> None:
    """标注全部节点。"""
    for n in graph.nodes():
        x, y = pos[n]
        radius = math.sqrt(sizes[n] / math.pi)
        text = str(abbr[n])
        degree = graph.degree(n)

        if degree >= 10:
            if len(text) == 4:
                wrapped = text[:2] + "\n" + text[2:]
            elif len(text) > 4:
                wrapped = textwrap.fill(text, width=3)
            else:
                wrapped = text
            longest = max(len(line) for line in wrapped.split("\n"))
            # 字号按节点半径与最长行估算，再夹在 10-14 之间
            fontsize = max(10, min(14, (radius * 2 * 0.5) / max(longest, 1)))
            ax.text(x, y, wrapped, ha="center", va="center", fontsize=fontsize,
                    color="white", fontweight="bold", zorder=4, alpha=0.9)
        else:
            ax.text(x + radius * 0.02, y, text, ha="left", va="center", fontsize=10,
                    color="#333333", fontweight="normal", zorder=4, alpha=0.8)


def _draw(graph: nx.Graph, abbr: dict, ax, pos: dict, sizes: dict,
          bend_num: float, bend_den: float, scale_by_distance: bool = False) -> None:
    """画一张网络的边、节点与标签。

    缺简称会直接报错，而不是回退成中文名。
    """
    missing = [n for n in graph.nodes() if n not in abbr]
    if missing:
        raise KeyError(f"以下机构缺少简称：{missing}")

    ax.set_facecolor("white")
    _curved_edges(ax, graph, pos, bend_num, bend_den, scale_by_distance)

    collection = nx.draw_networkx_nodes(
        graph, pos, ax=ax, node_size=[sizes[n] for n in graph.nodes()],
        node_color=[_colour(graph.degree(n)) for n in graph.nodes()],
        alpha=0.9, linewidths=1, edgecolors="white",
    )
    collection.set_zorder(3)
    _labels(ax, graph, pos, abbr, sizes)
    ax.axis("off")


def draw_full_network(graph: nx.Graph, abbr: dict, ax) -> None:
    """图 2：全期网络。spring 布局，边曲率随距离放大。"""
    pos = _spring_positions(graph)
    _draw(graph, abbr, ax, pos, _sizes(graph, 200, 1500), 0.3, 0.3, scale_by_distance=True)


def global_degree_range(graphs: list[nx.Graph]) -> tuple[int, int]:
    """五期合并后的度数极差，供图 3 统一节点大小。"""
    values = [d for g in graphs for _, d in g.degree()]
    return min(values), max(values)


def draw_period_network(graph: nx.Graph, abbr: dict, ax, title: str,
                        degree_range: tuple[int, int]) -> None:
    """图 3 的一个面板：星形或同心圆布局，节点大小按全局极差缩放。"""
    pos = _period_positions(graph)
    sizes = _sizes(graph, 200, 1200, deg_min=degree_range[0], deg_max=degree_range[1])
    _draw(graph, abbr, ax, pos, sizes, 0.8, 0.15)
    ax.set_title(title, loc="center", fontsize=16, pad=15)


def legend_handles() -> list:
    """四档颜色的图例句柄，图 2 与图 3 共用。"""
    return [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=colour,
                   markersize=size, label=text)
        for (_, colour), size, text in zip(config.DEGREE_TIERS, (14, 11, 9, 7), config.TIER_LABELS)
    ]
