# -*- coding: utf-8 -*-
"""附录 A：机构英文全称与简称对照表。

对照表原有三列：中文名、英文全称、简称。附录只保留英文全称与简称，
去掉中文名之后，同一机构会因别名行、简称行而重复出现，所以去重。
输出 output/tables/appendix_abbreviations.csv，按英文全称排序。
"""
from __future__ import annotations

import pandas as pd

import config
from common import output


def main() -> None:
    mapping = pd.read_excel(config.MAPPING_FILE, dtype=str)

    table = (
        mapping[[config.COL_MAPPING_FULL, config.COL_MAPPING_ABBR]]
        .apply(lambda column: column.str.strip())   # 去掉首尾空格，避免同一名称算成两行
        .dropna()                                   # 丢掉缺英文名或简称的行
        .drop_duplicates()                          # 去掉中文名之后出现的重复组合
        .sort_values(config.COL_MAPPING_FULL, kind="stable")
        .reset_index(drop=True)
    )

    output.print_table(table, "附录：机构英文全称与简称")
    path = output.save_table(table, "appendix_abbreviations")
    print(f"\n原始 {len(mapping)} 行，去重后 {len(table)} 行，已写入 {path}")


if __name__ == "__main__":
    main()