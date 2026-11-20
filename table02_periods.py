# -*- coding: utf-8 -*-
"""表 2：各期部门规章的分布。

在原有三列（单一、联合、合计）之外，增加两列年均值：
  Annual Total Regulations            合计 / 时期年数
  Annual Jointly Issued Regulations   联合 / 时期年数
"""
from __future__ import annotations

import re
from datetime import date

import pandas as pd

from common import corpus, output

# 各期的起止边界（年月）
PERIOD_BOUNDARIES = {
    "1978-1988": ("1978-12", "1988-03"),
    "1988-1998": ("1988-03", "1998-03"),
    "1998-2008": ("1998-03", "2008-03"),
    "2008-2018": ("2008-03", "2018-03"),
    "2018至今": ("2018-03", "2025-12"),
}


def _period_years(period: str, last_year: int) -> float:
    """把时期换算成年数。

    优先用 PERIOD_BOUNDARIES；若时期被改名（例如 "2018至今" 改成 "2018-2025"），
    则从标签里取年份兜底，避免改名后直接报错。
    """
    if period in PERIOD_BOUNDARIES:
        start, end = PERIOD_BOUNDARIES[period]
    else:
        matched = re.fullmatch(r"(\d{4})-(\d{4})", period)
        if matched:
            start, end = f"{matched.group(1)}-01", f"{matched.group(2)}-01"
        else:
            matched = re.match(r"(\d{4})", period)
            if not matched or not last_year:
                raise ValueError(
                    f"无法确定时期 {period!r} 的年数，请在 PERIOD_BOUNDARIES 中补充边界。"
                )
            start, end = f"{matched.group(1)}-01", f"{last_year}-12"

    y1, m1 = (int(x) for x in start.split("-"))
    y2, m2 = (int(x) for x in end.split("-"))
    days = (date(y2, m2, 1) - date(y1, m1, 1)).days
    return days / 365.25          # 用平均年长，闰年不影响口径


def main() -> None:
    data = corpus.load_corpus()
    counts = data.counts_by_period()

    # 每个时期对应的年数
    years = {period: _period_years(period, data.last_year) for period in counts["Period"]}

    counts["Annual Total Regulations"] = (
        counts["Total"] / counts["Period"].map(years)
    ).round(2)
    counts["Annual Jointly Issued Regulations"] = (
        counts["Joint"] / counts["Period"].map(years)
    ).round(2)

    # 合计行：条数求和，年均值按"总条数 / 总年数"算（不是各期年均值的平均）
    total_years = sum(years.values())
    total = pd.DataFrame([{
        "Period": "Total",
        "Single": int(counts["Single"].sum()),
        "Joint": int(counts["Joint"].sum()),
        "Total": int(counts["Total"].sum()),
        "Annual Total Regulations": round(counts["Total"].sum() / total_years, 2),
        "Annual Jointly Issued Regulations": round(counts["Joint"].sum() / total_years, 2),
    }])

    table = pd.concat([counts, total], ignore_index=True)

    output.print_table(table, "表 2  各期部门规章分布")
    output.print_note(
        "联合发文按条计一次；年均值的分母为时期长度（"
        + "、".join(f"{p.replace('至今', '-2025')} {y:.2f} 年" for p, y in years.items())
        + f"），合计按 {total_years:.2f} 年计。"
    )
    output.save_table(table, "table02_periods")


if __name__ == "__main__":
    main()