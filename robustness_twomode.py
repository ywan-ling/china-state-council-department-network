# -*- coding: utf-8 -*-
"""两模（部门 × 规章）诊断：投影保留了什么、丢掉了什么。

背景
----
投影把一条 k 部门规章展开成 C(k,2) 条两两边，于是"共同署名"被当成
"双边关系"。审稿人关心的正是这一步损失了多少信息。本脚本用二部图对照：

  部门侧度数 = 参与的联合发文条数（即超边参与次数）
  规章侧度数 = 该规章的签字机构数
  投影侧度数 = 该部门的合作对象数（去重后的邻居数）

输出两部分：
  1. 每期的汇总：部门数、规章数、平均事件规模、候选对数、去重边数、
     膨胀倍数，以及"参与条数"与"合作对象数"两个排名的 Spearman 相关及 p 值；
  2. 全期的事件规模分布：k、事件数、候选对数及其占比。
"""
from __future__ import annotations

import math
from collections import Counter

import pandas as pd

from common import corpus, graphs, output
from common.stats import rank_correlation, format_p


def _twomode(bodies: list[list[str]]):
    """返回（部门参与条数, 事件规模分布）。"""
    participation: Counter = Counter()
    sizes: Counter = Counter()
    for members in bodies:
        unique = list(dict.fromkeys(members))
        sizes[len(unique)] += 1
        participation.update(unique)
    return participation, sizes


def main() -> None:
    data = corpus.load_corpus()

    blocks = [("All periods", data.bodies())]
    blocks += [(period, data.bodies(period)) for period in data.periods]

    rows = []
    for label, bodies in blocks:
        participation, sizes = _twomode(bodies)
        graph = graphs.build(bodies)

        candidate_pairs = sum(k * (k - 1) // 2 * n for k, n in sizes.items())
        ties = graph.number_of_edges()
        partners = {node: graph.degree(node) for node in graph.nodes()}

        rho, p = rank_correlation(dict(participation), partners)

        rows.append({
            "Period": label,
            "Departments": len(participation),
            "Regulations": len(bodies),
            "Mean event size": round(sum(k * n for k, n in sizes.items()) / len(bodies), 2),
            "Candidate pairs": candidate_pairs,
            "Distinct ties": ties,
            "Inflation": round(candidate_pairs / ties, 2) if ties else None,
            "Spearman (participation vs partners)":
                round(rho, 3) if not math.isnan(rho) else None,
            "p": format_p(p),
        })

    table = pd.DataFrame(rows)
    output.print_table(table, "两模诊断：参与条数 vs 合作对象数")
    output.print_note(
        "参与条数 = 该部门签过字的联合发文数（二部图度数）；"
        "合作对象数 = 投影网络中去重后的邻居数。"
        "膨胀倍数 = 候选对数 / 去重边数。"
        "p 为 Spearman 相关的双侧检验（t 近似，df = n-2），并列采用平均秩。"
    )
    output.save_table(table, "robustness_twomode")

    # ---- 全期事件规模分布 ------------------------------------------------
    _, sizes = _twomode(data.bodies())
    total_pairs = sum(k * (k - 1) // 2 * n for k, n in sizes.items())

    distribution = pd.DataFrame([
        {
            "Signatories (k)": k,
            "Events": sizes[k],
            "Candidate pairs": k * (k - 1) // 2 * sizes[k],
            "Share of pairs (%)": round(100 * (k * (k - 1) // 2 * sizes[k]) / total_pairs, 1),
        }
        for k in sorted(sizes)
    ])
    output.print_table(distribution, "全期事件规模分布")
    output.print_note(
        "k 是一条规章的签字机构数。最后几行（k ≥ 10）就是审稿人担心的超大事件，"
        "可对照 robustness_large_events.py 的剔除结果。"
    )
    output.save_table(distribution, "robustness_twomode_distribution")


if __name__ == "__main__":
    main()