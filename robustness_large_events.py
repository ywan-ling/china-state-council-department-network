# -*- coding: utf-8 -*-
"""稳健性检验：剔除超大联合发文事件后，网络结构与中心性排名是否改变。

背景
----
一条由 k 个部门联合发布的规章，在投影时会产生 C(k,2) 条边。数据里有 7 条
规模 ≥10 的事件（最大 18 个部门），它们可能抬高密度、缩短路径、改变中心性。
本脚本用两种口径剔除后重算，与原始结果比较：

  drop >= 15  只剔除 18 部门那一条
  drop >= 10  剔除全部 7 条（10、10、10、10、12、14、18）

比较的内容：
  * 结构指标：节点、边、密度、平均路径长度（LCC）、平均聚类系数（LCC）
  * 排名一致性：度、中介、接近三个中心性与原始网络的 Spearman 相关及 p 值

口径与正文完全一致：密度用全图，路径与聚类用最大连通分量，中心性用
NetworkX 默认归一化。
"""
from __future__ import annotations

import math

import pandas as pd

from common import corpus, graphs, measures, output
from common.stats import rank_correlation, format_p


def _metrics(bodies: list[list[str]]):
    """建网并返回（结构指标, 三个中心性）。"""
    graph = graphs.build(bodies)
    return measures.structure(graph), measures.centralities(graph)


def _fmt(value, digits: int = 3) -> object:
    """浮点保留位数；nan 显示为 None，方便在表里看出"无法计算"。"""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return round(value, digits)


def main() -> None:
    data = corpus.load_corpus()

    # 全部时期 + 五个分期
    blocks = [("All periods", data.bodies())]
    blocks += [(period, data.bodies(period)) for period in data.periods]

    rows = []
    for label, bodies in blocks:
        base_stats, base_cent = _metrics(bodies)

        rows.append({
            "Period": label,
            "Scenario": "baseline",
            "Removed": 0,
            "Nodes": base_stats["n"],
            "Edges": base_stats["m"],
            "Density": _fmt(base_stats["density"], 3),
            "APL": _fmt(base_stats["apl"], 2),
            "ACC": _fmt(base_stats["acc"], 3),
            "rho degree": "—",
            "p degree": "—",
            "rho betweenness": "—",
            "p betweenness": "—",
            "rho closeness": "—",
            "p closeness": "—",
        })

        for threshold in (15, 10):
            kept = [members for members in bodies if len(members) < threshold]
            removed = len(bodies) - len(kept)

            # 该口径下没有可剔除的事件：跳过，避免打印与 baseline 完全相同的行
            if removed == 0:
                continue

            stats, cent = _metrics(kept)
            rho_d, p_d = rank_correlation(base_cent["degree"], cent["degree"])
            rho_b, p_b = rank_correlation(base_cent["betweenness"], cent["betweenness"])
            rho_c, p_c = rank_correlation(base_cent["closeness"], cent["closeness"])

            rows.append({
                "Period": label,
                "Scenario": f"drop >= {threshold}",
                "Removed": removed,
                "Nodes": stats["n"],
                "Edges": stats["m"],
                "Density": _fmt(stats["density"], 3),
                "APL": _fmt(stats["apl"], 2),
                "ACC": _fmt(stats["acc"], 3),
                "rho degree": _fmt(rho_d),
                "p degree": format_p(p_d),
                "rho betweenness": _fmt(rho_b),
                "p betweenness": format_p(p_b),
                "rho closeness": _fmt(rho_c),
                "p closeness": format_p(p_c),
            })

    table = pd.DataFrame(rows)
    output.print_table(table, "稳健性：剔除超大联合发文事件")
    output.print_note(
        "drop >= 15 只剔除 18 部门那一条；drop >= 10 剔除全部 7 条。"
        "rho 为与原始网络的三类中心性排名相关（只保留原网络中也存在的部门），"
        "p 为双侧检验（t 近似，df = n-2），并列采用平均秩。"
        "节点数下降说明有部门只出现在被剔除的事件里。"
    )
    output.save_table(table, "robustness_large_events")


if __name__ == "__main__":
    main()