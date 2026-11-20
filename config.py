# -*- coding: utf-8 -*-
"""运行参数：文件位置、列名、绘图样式。
"""
from pathlib import Path

# --------------------------------------------------------------------------- #
# 输入文件
# --------------------------------------------------------------------------- #
DATA_DIR = Path("data")

SINGLE_FILE = DATA_DIR / "single_anon.xlsx"            # 单一部门规章
JOINT_FULL_FILE = DATA_DIR / "full period_anon.xlsx"   # 联合发文，机构名统一到 2025 年
JOINT_PHASED_FILE = DATA_DIR / "phased_anon.xlsx"      # 联合发文，机构名在各时期内统一
MAPPING_FILE = DATA_DIR / "name mapping_anon.xlsx"     # 部门 / 全称 / 简称（含别名行）

# --------------------------------------------------------------------------- #
# 列名（脱敏后已改为英文）
# --------------------------------------------------------------------------- #
# 三份规章表共用的列
COL_ID = "id"
COL_TITLE = "title"
COL_BODIES = "bodies"
COL_DATE = "date"
COL_PERIOD = "period"

# 只有对照表才有的两列（外加它的部门列）
COL_MAPPING_DEPT = "department"
COL_MAPPING_FULL = "full_name"
COL_MAPPING_ABBR = "abbreviation"

# --------------------------------------------------------------------------- #
# 绘图样式
# --------------------------------------------------------------------------- #
# 颜色依次为红、橙、蓝、青。
DEGREE_TIERS = [(20, "#e74c3c"), (10, "#f39c12"), (5, "#3498db"), (0, "#1abc9c")]

# 图例文字，与上面的四档一一对应
TIER_LABELS = ["High Connectivity (≥20)", "Medium-High (10-19)",
               "Medium (5-9)", "Low (<5)"]

# 图片保存分辨率。作图时用 300 dpi 屏幕预览，保存时用 600 dpi 满足印刷要求。
FIGURE_DPI = 600

# --------------------------------------------------------------------------- #
# 输出目录
# --------------------------------------------------------------------------- #
OUTPUT_DIR = Path("output")
TABLE_DIR = OUTPUT_DIR / "tables"
FIGURE_DIR = OUTPUT_DIR / "figures"

# 导入时建好目录，脚本里就不用重复写
for _d in (OUTPUT_DIR, TABLE_DIR, FIGURE_DIR):
    _d.mkdir(parents=True, exist_ok=True)