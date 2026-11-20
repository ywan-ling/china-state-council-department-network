# -*- coding: utf-8 -*-
"""按顺序运行全部出表、出图脚本。

每个脚本都是独立的（可以单独 python tableXX.py），这里只是把它们串起来，
并在每段前打印分隔线，方便看终端输出。
"""
from __future__ import annotations

import importlib

SCRIPTS = [
    "table02_periods", "table04_full_network", "table05_periods",
    "table06_degree", "table07_betweenness", "table08_closeness",
    "table09_joint_share", "table10_typology", "table11_representative",
    "table11_supplementary", "figure03_full_network", "figure04_period_panels",
    "robustness_twomode", "robustness_large_events", "robustness_weighted"
]


def main() -> None:
    for name in SCRIPTS:
        print("\n" + "=" * 78)
        print(f"# {name}")
        print("=" * 78)
        importlib.import_module(name).main()


if __name__ == "__main__":
    main()
