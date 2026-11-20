# -*- coding: utf-8 -*-
"""读取、清洗、机构名归一与机构计数。

三份规章表：
  single        单一部门规章，每行一个机构；
  joint_full    联合发文，机构名统一到 2025 年（用于全期网络）；
  joint_phased  联合发文，机构名在各时期内统一（用于分期网络）。

一份对照表：
  mapping       部门 / 全称 / 简称
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

import config

# 匹配任意空白：半角空格、制表符、全角空格 U+3000、不间断空格 U+00A0
_WS = re.compile(r"[\s\u3000\u00a0]+")


def split_bodies(cell: object) -> list[str]:
    """把"部门"单元格切成机构名列表。"""
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return []
    names = [p for p in _WS.split(str(cell).strip()) if p]
    return list(dict.fromkeys(names))


def _to_date(series: pd.Series) -> pd.Series:
    """把 Excel 的日期序列号（或日期字符串）统一转成日期。

    Excel 的序列号以 1899-12-30 为原点，1900 年闰年问题已含在原点里；
    已经是日期类型的列直接保留，解析失败的置为 NaT。
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_datetime(series, unit="D", origin="1899-12-30", errors="coerce")
    return pd.to_datetime(series, errors="coerce")


@dataclass
class Corpus:
    """三份规章表加一份机构对照表。"""

    single: pd.DataFrame
    joint_full: pd.DataFrame
    joint_phased: pd.DataFrame
    abbr: dict[str, str]      # 中文名 -> 简称
    english: dict[str, str]   # 中文名 -> 英文全称

    def __post_init__(self) -> None:
        """根据原始规章表和机构映射表，构建 Corpus 的派生属性。

        一、时期信息
            periods    按规章最早发布日期排列的时期列表
            last_year  全部规章中的最晚发布日期年份

        二、网络节点与简称索引
            nodes          全期联合发文网络的机构节点集合
            node_by_abbr   机构英文简称到规范名称的映射

        三、机构名称映射
            period_to_full  分期机构名称到全期规范名称的映射
        """

        # ---- 一、确定时期及语料时间范围 --------------------------------

        # 合并单独发文和分期联合发文中的时期、发布日期。
        dates = []
        for frame in (self.single, self.joint_phased):
            part = frame[[config.COL_PERIOD, config.COL_DATE]].copy()
            part[config.COL_PERIOD] = (
                part[config.COL_PERIOD].astype(str).str.strip()
            )
            part["_date"] = _to_date(part[config.COL_DATE])
            dates.append(part)

        combined = pd.concat(dates, ignore_index=True)

        # 按各时期最早发布日期排序，得到时间顺序。
        first_date = (
            combined.groupby(config.COL_PERIOD)["_date"]
            .min()
            .sort_values()
        )
        self.periods: list[str] = list(first_date.index)

        # 取得全部规章中的最晚年份。
        years = combined["_date"].dt.year.dropna()
        self.last_year: int = int(years.max()) if len(years) else 0

        # ---- 二、构建全期网络节点及简称索引 ----------------------------

        # 汇总全期联合发文中出现过的所有机构，并去重。
        self.nodes: set[str] = {
            name for bodies in self.bodies() for name in bodies
        }

        # 建立英文简称到机构规范名称的反向查询表。
        self.node_by_abbr: dict[str, str] = {}
        for name in self.nodes:
            code = self.abbr.get(name)
            if code:
                self.node_by_abbr.setdefault(code, name)

        # ---- 三、建立分期名称到全期名称的映射 --------------------------

        # 两份联合发文表按行对应。
        # 对同一行的机构名单逐个配对，统计每个分期名称对应的全期名称。
        votes: dict[str, Counter] = defaultdict(Counter)

        for f_cell, p_cell in zip(
                self.joint_full[config.COL_BODIES],
                self.joint_phased[config.COL_BODIES]
        ):
            f_names = split_bodies(f_cell)
            p_names = split_bodies(p_cell)

            # 两份名单的机构数量不一致时，跳过该行。
            if len(f_names) != len(p_names):
                continue

            # 按名单中的位置逐个建立名称对应关系并累计票数。
            for f_name, p_name in zip(f_names, p_names):
                votes[p_name][f_name] += 1

        # 每个分期名称采用票数最多的全期名称作为最终映射结果。
        self.period_to_full: dict[str, str] = {
            name: counter.most_common(1)[0][0]
            for name, counter in votes.items()
        }

    # ------------------------------------------------------------------ #
    # 时期与图标题
    # ------------------------------------------------------------------ #
    def period_labels(self) -> dict[str, str]:
        """图 3 每个面板的标题，如 (a) 1978-1988、(e) 2018-2025。

        字母按时期顺序编；"至今"换成数据里的最晚年份，所以换数据时标题
        会自动跟着变，不需要手工改。
        """
        labels = {}
        for index, period in enumerate(self.periods):
            text = period.replace("至今", f"-{self.last_year}" if self.last_year else "")
            labels[period] = f"({chr(97 + index)}) {text}"
        return labels

    # ------------------------------------------------------------------ #
    # 网络用的机构列表
    # ------------------------------------------------------------------ #
    def bodies(self, period: str | None = None) -> list[list[str]]:
        """返回联合发文的机构列表；指定时期时只取该期的规章。"""
        if period is None:
            frame = self.joint_full
        else:
            frame = self.joint_phased[
                self.joint_phased[config.COL_PERIOD].astype(str).str.strip() == period
            ]
        return [split_bodies(c) for c in frame[config.COL_BODIES]]

    # ------------------------------------------------------------------ #
    # 按时期统计的规章条数
    # ------------------------------------------------------------------ #
    def counts_by_period(self) -> pd.DataFrame:
        """按时期统计单一部门与联合发文的条数。

        时期顺序取自 self.periods；某个时期若只在一份表里出现，另一列补 0。
        """
        single = self.single.groupby(config.COL_PERIOD).size()
        joint = self.joint_phased.groupby(config.COL_PERIOD).size()
        frame = pd.DataFrame({
            "Period": self.periods,
            "Single": single.reindex(self.periods).fillna(0).astype(int).values,
            "Joint": joint.reindex(self.periods).fillna(0).astype(int).values,
        })
        frame["Total"] = frame["Single"] + frame["Joint"]
        return frame

    # ------------------------------------------------------------------ #
    # 机构名归一
    # ------------------------------------------------------------------ #
    def resolve(self, name: str) -> str | None:
        """把一个机构名归到全期网络的某个节点上，认不出则返回 None。"""
        if name in self.nodes:
            return name
        if name in self.period_to_full:
            return self.period_to_full[name]
        code = self.abbr.get(name)
        if code and code in self.node_by_abbr:
            return self.node_by_abbr[code]
        return None

    # ------------------------------------------------------------------ #
    # 部门级发文计数
    # ------------------------------------------------------------------ #
    def department_counts(self) -> pd.DataFrame:
        """统计每个部门的发文总量与联合发文数。

        计数规则：
          * 每条规章给它的每个签字机构各记 1 次"总量"；
          * 联合发文的再额外记 1 次"联合"；
          * 同一规章内若两个名称归到同一部门，只记 1 次。

        返回列：Department / Total / Joint / Share / Abbreviation / English name，
        按总量、联合数降序排列。
        """
        # 三个累加器：总量、联合数、未能归并的名称（最后打印提醒）
        totals: dict[str, int] = {}
        joint: dict[str, int] = {}
        unresolved: dict[str, int] = {}   # 认不出的名称 -> 条数，最后打印提醒

        # 单一部门规章：每行一个机构，只计入总量
        for cell in self.single[config.COL_BODIES]:
            names = split_bodies(cell)
            if len(names) != 1:
                continue  # 多机构行属数据异常，实际上不存在这种情况
            node = self.resolve(names[0])
            if node is None:
                unresolved[names[0]] = unresolved.get(names[0], 0) + 1
                continue
            totals[node] = totals.get(node, 0) + 1

        # 联合发文：每个签字机构各记一次总量与一次联合；同一规章内先去重
        for cell in self.joint_full[config.COL_BODIES]:
            seen: set[str] = set()
            for name in split_bodies(cell):
                node = self.resolve(name)
                if node is None:
                    unresolved[name] = unresolved.get(name, 0) + 1
                    continue
                if node in seen:
                    continue
                seen.add(node)
                totals[node] = totals.get(node, 0) + 1
                joint[node] = joint.get(node, 0) + 1

        # 组装成表：先按总量、再按联合数降序
        frame = pd.DataFrame(
            [(node, totals[node], joint.get(node, 0)) for node in totals],
            columns=["Department", "Total", "Joint"],
        ).sort_values(["Total", "Joint"], ascending=False).reset_index(drop=True)

        # 联合占比（百分比，两位小数）、简称与英文全称
        frame["Share"] = (100 * frame["Joint"] / frame["Total"]).round(2)
        frame["Abbreviation"] = [self.abbr.get(d, d) for d in frame["Department"]]
        frame["English name"] = [self.english.get(d, d) for d in frame["Department"]]

        # 未纳入分类的名称：说明分析单位与这些规章的去向
        if unresolved:
            top = sorted(unresolved.items(), key=lambda kv: -kv[1])[:8]
            print("  [说明] 类型学以参与联合发文的 %d 个部门为分析单位；"
                  "另有 %d 个名称从未出现在联合发文中（共 %d 条单一部门规章），"
                  "不在分类范围内。"
                  % (len(totals), len(unresolved), sum(unresolved.values())))
            print("         条数较多的名称：" + "，".join(f"{n}（{c} 条）" for n, c in top))
        return frame


def load_corpus(data_dir: Path | str | None = None) -> Corpus:
    """读取四个输入文件，返回 Corpus。"""
    base = Path(data_dir) if data_dir is not None else config.DATA_DIR
    paths = {
        "single": base / config.SINGLE_FILE.name,
        "full": base / config.JOINT_FULL_FILE.name,
        "phased": base / config.JOINT_PHASED_FILE.name,
        "mapping": base / config.MAPPING_FILE.name,
    }

    missing = [str(p) for p in paths.values() if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "缺少输入文件：\n  " + "\n  ".join(missing) + "\n请放入 data/ 目录。"
        )

    # 对照表：中文名 -> 英文全称、中文名 -> 简称
    mapping = pd.read_excel(paths["mapping"])
    abbr = {
        str(row[config.COL_MAPPING_DEPT]).strip(): str(row[config.COL_MAPPING_ABBR]).strip()
        for _, row in mapping.iterrows()
        if pd.notna(row[config.COL_MAPPING_DEPT]) and pd.notna(row.get(config.COL_MAPPING_ABBR))
    }
    english = {
        str(row[config.COL_MAPPING_DEPT]).strip(): str(row[config.COL_MAPPING_FULL]).strip()
        for _, row in mapping.iterrows()
        if pd.notna(row[config.COL_MAPPING_DEPT]) and config.COL_MAPPING_FULL in mapping.columns
    }

    frames = {
        "single": pd.read_excel(paths["single"]),
        "full": pd.read_excel(paths["full"]),
        "phased": pd.read_excel(paths["phased"]),
    }
    # 统一去掉「阶段」两端的空白，避免分组与筛选因空格对不上
    for frame in frames.values():
        if config.COL_PERIOD in frame.columns:
            frame[config.COL_PERIOD] = frame[config.COL_PERIOD].astype(str).str.strip()

    return Corpus(
        single=frames["single"],
        joint_full=frames["full"],
        joint_phased=frames["phased"],
        abbr=abbr,
        english=english,
    )