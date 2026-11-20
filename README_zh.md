# 论文图表复现代码

[English](README.md) | **中文**

本仓库输出内容如下：

- 表格：Table 2、Table 4–11
- 图形：Figure 3（全期网络）、Figure 4（五期面板）
- 检验：加权网络、剔除超大事件、二模对照

输入数据：四个脱敏工作簿可从 figshare（DOI: 10.6084/m9.figshare.35072359）获取。

---

## 目录

1. [安装](#一安装)
2. [使用](#二使用)
3. [项目结构](#三项目结构)
4. [公共模块](#四公共模块)
5. [输入数据格式](#五输入数据格式)
6. [计算逻辑](#六计算逻辑)
7. [稳健性检验](#七稳健性检验)
8. [输出](#八输出)
9. [口径约定](#九口径约定)

---

## 一、安装

```bash
pip install -r requirements.txt
```

依赖：Python ≥ 3.9，pandas、NumPy、NetworkX、Matplotlib、openpyxl、SciPy。

---

## 二、使用

```bash
# 全部重算
python run_all.py

# 单跑一个脚本
python table05_periods.py
python figure04_period_panels.py
```

必须在 `coissuance/` 目录下运行，脚本通过 `import config` 读取路径与列名。

`run_all.py` 按固定顺序调用全部脚本，并在每段前打印分隔线；单个脚本都可独立运行。

---

## 三、项目结构

```
coissuance/
├── README.md / README_zh.md      本文档（英文 / 中文）
├── requirements.txt
├── config.py                     路径、列名、绘图样式（只有常量）
├── run_all.py                    顺序执行全部脚本
├── common/                       公共模块（见第四节）
├── table02_periods.py            Table 2   各期规章分布，含年均值
├── table04_full_network.py       Table 4   全期结构指标
├── table05_periods.py            Table 5   分期结构指标
├── table06_degree.py             Table 6   度中心性
├── table07_betweenness.py        Table 7   中介中心性
├── table08_closeness.py          Table 8   接近中心性
├── table09_joint_share.py        Table 9   独立与联合发文占比
├── table10_typology.py           Table 10  2×2 类型矩阵与切分点
├── table11_representative.py     Table 11  各类代表部门
├── table11_supplementary.py      Table 11  完整部门名单
├── figure03_full_network.py      Figure 3  全期网络图
├── figure04_period_panels.py     Figure 4  五期网络图
├── robustness_weighted.py        稳健性：二值 vs 加权
├── robustness_large_events.py    稳健性：剔除超大事件
├── robustness_twomode.py         稳健性：二模诊断
└── data/                         输入文件
```

每个出表脚本的结构相同：读取数据 → 计算 → 打印 → 写 CSV。出图脚本读取数据 → 计算布局 → 绘制 → 保存 PNG。

---

## 四、公共模块

| 模块 | 职责 | 主要函数 |
|---|---|---|
| `corpus.py` | 数据入口：读取、清洗、名称归一、按部门计数 | `split_bodies`、`Corpus.bodies`、`Corpus.counts_by_period`、`Corpus.resolve`、`Corpus.department_counts` |
| `graphs.py` | 建网：把一条规章的若干机构投影成网络 | `build`、`build_weighted`、`lcc`、`period_graphs` |
| `measures.py` | 结构指标、中心性、表格的入选规则 | `structure`、`centralities`、`select_top`、`select_above_mean_nonzero` |
| `typology.py` | 四类模式：按中位数二分 | `thresholds`、`classify` |
| `plotting.py` | 两张网络图的布局与绘制 | `draw_full_network`、`draw_period_network`、`global_degree_range`、`legend_handles` |
| `stats.py` | 秩相关及显著性 | `rank_correlation`、`format_p` |
| `output.py` | 写 CSV、保存图片、终端打印 | `save_table`、`save_figure`、`print_table`、`print_note`、`print_side_by_side` |

### 4.1 数据流

```
输入文件
   │
   ▼
corpus    读取、切分机构名、把名称归到网络节点、按部门计数
   │
   ├─► graphs     投影成网络 ──┬─► measures   指标与入选规则
   │                           └─► plotting   绘图
   │
   └─► typology   按中位数分类
```

### 4.2 名称归并

`Corpus.resolve()` 依次尝试三条路径：

1. 名称本身就是网络节点；
2. 名称出现在两个联合文件逐行对齐得到的“期内名 → 全期名”映射中；
3. 名称的简称与某个节点的简称相同。

三条均不中则返回 `None`，该规章在计数时跳过，终端会说明有多少名称与规章未进入分类。

---

## 五、输入数据格式

`data/` 下放四个 Excel 文件：

| 文件 | 内容 |
|---|---|
| `single_anon.xlsx` | 单一部门规章 |
| `full period_anon.xlsx` | 联合发文，机构名统一到 2025 年 |
| `phased_anon.xlsx` | 联合发文，各期内部名称统一 |
| `name mapping_anon.xlsx` | 机构对照表 |

规章表的列：

| 列 | 含义 |
|---|---|
| `id` | 序号 |
| `title` | 标题（带盐 SHA-256 哈希，不参与计算） |
| `bodies` | 发文机构，多个机构以空格分隔 |
| `date` | 发布时间 |
| `period` | 时期 |
| `body_count` | 机构数（仅联合表） |

对照表的列：`department`、`full_name`、`abbreviation`。

列名与文件名集中定义在 `config.py`，换数据时只改该文件。

---

## 六、计算逻辑

### 6.1 网络构建

一条由 k 个部门联合发布的规章，在 k 个部门之间建立 `C(k,2) = k(k−1)/2` 条无向边。

- 边为二值且已去重：同一对部门多次联合发布只保留一条边；
- 无自环：切分机构名时已去重；
- 全期网络使用 `full period`，分期网络使用 `phased`。

### 6.2 结构指标

| 指标 | 定义 | 计算范围 |
|---|---|---|
| 节点数 n | 节点个数 | 全图 |
| 边数 m | 边数 | 全图 |
| 密度 | `2m / (n(n−1))` | 全图 |
| 最大连通分量 LCC | 最大连通子图的节点数 | 全图 |
| 平均路径长度 APL | LCC 内所有可达节点对最短路径的平均 | LCC |
| 平均聚类系数 ACC | LCC 内各节点局部聚类系数的均值，度 < 2 计 0 | LCC |

### 6.3 中心性

三项中心性均在 LCC 内计算（n 为 LCC 节点数）：

| 指标 | 定义 |
|---|---|
| 度中心性 | `dᵢ / (n−1)` |
| 中介中心性 | `Σs≠t≠i σst(i)/σst`，按 `2/((n−1)(n−2))` 归一化 |
| 接近中心性 | `(n−1) / Σj≠i d(i,j)` |

LCC 之外的部门不赋予中心性数值，也不进入相应表格。

### 6.4 表格的入选规则

| 表 | 规则 |
|---|---|
| Table 6、Table 8 | 每期前 20%，`k = ⌈0.2n⌉`；第 k 名的数值为截断值，凡不低于它者全部入选 |
| Table 7 | 高于该期“非零中介中心性的均值”；若全为 0 则列出全部 |

### 6.5 类型学

两个维度：发文总量、联合发文占比。

- 每条规章给每个签字机构各计 1 次总量，联合发文的再计 1 次联合；
- 同一规章内两个名称归到同一部门时只计 1 次；
- 两个维度各自取中位数，等于中位数算“高”；
- 交叉得到四类：Active-Collaborative、Independent-Dominant、Collaborative-Participatory、Low-Participation。

Table 10 输出纯文字 2×2 矩阵，并把两个切分点及两侧部门数写入 `table10_thresholds.csv`；Table 11 每类列 4 个代表部门，完整名单由 `table11_supplementary.py` 输出。

---

## 七、稳健性检验

三项检验都不参与正文表格的计算，结果写入四个 CSV。

### 7.1 加权网络

以两部门共同发布规章的次数作为边权重重建网络。由于边权被解释为距离，路径类指标以该次数的倒数作为距离，使强关系更“近”；度以相邻边权之和替代。

比较方式：Spearman 秩相关（并列取平均秩，报告双侧 p 值）与入选名单的重叠程度。

### 7.2 剔除超大事件

分别剔除“仅最大的一条规章”与“全部签字机构达到十个及以上的规章”，重算结构指标与中心性排名，以显示绝对水平与排名在多大程度上依赖少数多部门规章。

### 7.3 二模诊断

将投影网络与“部门—规章”二模结构对照：

- 对每个部门比较其签过的联合发文条数与在投影网络中获得的互异合作对象数，求秩相关；
- 报告候选对数、去重后的边数、膨胀倍数；
- 报告规章规模的分布。

---

## 八、输出

表格写入 `output/tables/`：

| 文件 | 对应 |
|---|---|
| `table02_periods.csv` | Table 2 |
| `table04_full_network.csv` | Table 4 |
| `table05_periods.csv` | Table 5 |
| `table06_degree.csv` | Table 6 |
| `table07_betweenness.csv` | Table 7 |
| `table08_closeness.csv` | Table 8 |
| `table09_joint_share.csv` | Table 9 |
| `table10_thresholds.csv` | Table 10 的两个切分点 |
| `table11_representative.csv` | Table 11 |
| `table11_supplementary.csv` | Table 11 完整名单 |
| `robustness_weighted.csv` | 加权检验 |
| `robustness_large_events.csv` | 大事件检验 |
| `robustness_twomode.csv` | 二模诊断 |
| `robustness_twomode_distribution.csv` | 规章规模分布 |

图形写入 `output/figures/`：

| 文件                           | 对应       |
|------------------------------|----------|
| `figure03_full_network.png`  | Figure 3 |
| `figure04_period_panels.png` | Figure 4 |

CSV 使用 UTF-8 带 BOM，Excel 可直接打开；图片为 600 dpi、白底。

---

## 九、口径约定

| 项目 | 口径 |
|---|---|
| 节点数、边数、密度 | 全图 |
| 平均路径长度、聚类系数、三类中心性 | 最大连通分量 |
| 聚类系数 | 分量内均值，度 < 2 计 0 |
| 度中心性 | `d/(n−1)` |
| 中介中心性 | 按 `2/((n−1)(n−2))` 归一化 |
| 接近中心性 | `(n−1)/距离和` |
| Table 6 / 8 入选 | 前 20%，含截断值并列 |
| Table 7 入选 | 高于非零均值；全零则列出全部 |
| Table 2 / 9 计数 | 联合发文按条计一次 |
| Table 10 / 11 计数 | 每个签字机构各计一次，同一规章同一节点只计一次 |
