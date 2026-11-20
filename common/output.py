# -*- coding: utf-8 -*-
"""结果输出：写 CSV、打印表格。

所有脚本共用这里的四个函数，保证输出位置、编码、小数位一致：
  save_table      写 output/tables/*.csv（UTF-8 带 BOM，Excel 直接打开不乱码）
  save_figure     写 output/figures/*.png（白底、tight bbox、600 dpi）
  print_table     终端打印对齐表格，可直接粘进 Word
  print_note      打印表注
  print_side_by_side  把多期结果并排打印（表 6-8 用）
"""
from __future__ import annotations

from itertools import zip_longest
from pathlib import Path

import pandas as pd

import config


def save_table(frame: pd.DataFrame, name: str) -> Path:
    """把表格写成 output/tables/<name>.csv。

    utf-8-sig 会写入 BOM，Excel 打开中文不会乱码。
    """
    path = config.TABLE_DIR / f"{name}.csv"
    frame.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def save_figure(fig, name: str, dpi: int | None = None) -> Path:
    """把图写成 output/figures/<name>.png。

    bbox_inches="tight" 去掉多余白边；facecolor 固定白色，避免透明背景
    在 Word 里显示成黑底。
    """
    path = config.FIGURE_DIR / f"{name}.png"
    fig.savefig(path, dpi=dpi or config.FIGURE_DPI, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    return path


def print_table(frame: pd.DataFrame, title: str = "") -> None:
    """打印对齐的表格。index=False，因为表格的第一列通常就是标签列。"""
    if title:
        print(f"\n=== {title} ===")
    print(frame.to_string(index=False))


def print_note(text: str) -> None:
    """打印一行表注，说明口径或阈值来源。"""
    print(f"\n[注] {text}")


def print_side_by_side(blocks, width: int = 24) -> None:
    """把多期结果并排打印成一张表。

    blocks 是若干个 (标题, [(部门, 数值), ...])。各期人数不同，
    所以用 zip_longest 按最长的一列补齐，短的那期右侧留空。
    """
    columns = []
    for title, rows in blocks:
        column = [title.center(width)]
        column += [f"{name:<14}{value:>7}" for name, value in rows]
        columns.append(column)
    for line in zip_longest(*columns, fillvalue=""):
        print("  ".join(cell.ljust(width) for cell in line).rstrip())
