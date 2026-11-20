# Replication Code for the Paper

**English** | [中文](README_zh.md)

The repository outputs the following:

- Tables: Table 2, Table 4–11
- Figures: Figure 3 (full-period network), Figure 4 (five-period panels)
- Checks: weighted network, large-event exclusion, two-mode comparison

Input data: the four anonymized workbooks are available from figshare (DOI: 10.6084/m9.figshare.35072359).

---

## Contents

1. [Installation](#1-installation)
2. [Usage](#2-usage)
3. [Project structure](#3-project-structure)
4. [Common modules](#4-common-modules)
5. [Input data format](#5-input-data-format)
6. [Computation logic](#6-computation-logic)
7. [Robustness checks](#7-robustness-checks)
8. [Outputs](#8-outputs)
9. [Conventions](#9-conventions)

---

## 1. Installation

```bash
pip install -r requirements.txt
```

Requirements: Python ≥ 3.9, pandas, NumPy, NetworkX, Matplotlib, openpyxl, SciPy.

---

## 2. Usage

```bash
# recompute everything
python run_all.py

# or run a single script
python table05_periods.py
python figure04_period_panels.py
```

Run from inside `coissuance/`; the scripts read paths and column names through `import config`.

`run_all.py` calls every script in a fixed order and prints a separator before each block. Each script also runs on its own.

---

## 3. Project structure

```
coissuance/
├── README.md / README_zh.md      this document (English / Chinese)
├── requirements.txt
├── config.py                     paths, column names, plotting style (constants only)
├── run_all.py                    runs every script in order
├── common/                       shared modules (see section 4)
├── table02_periods.py            Table 2   regulations per period, with annual averages
├── table04_full_network.py       Table 4   full-period structure
├── table05_periods.py            Table 5   period structure
├── table06_degree.py             Table 6   degree centrality
├── table07_betweenness.py        Table 7   betweenness centrality
├── table08_closeness.py          Table 8   closeness centrality
├── table09_joint_share.py        Table 9   single vs joint shares
├── table10_typology.py           Table 10  2×2 typology matrix and cut-offs
├── table11_representative.py     Table 11  representative departments
├── table11_supplementary.py      Table 11  full department list
├── figure03_full_network.py      Figure 3  full-period network
├── figure04_period_panels.py     Figure 4  five-period panels
├── robustness_weighted.py        robustness: binary vs weighted
├── robustness_large_events.py    robustness: excluding large events
├── robustness_twomode.py         robustness: two-mode diagnostics
└── data/                         input files
```

Every table script follows the same pattern: read data → compute → print → write CSV. Every figure script reads data → compute layout → draw → save PNG.

---

## 4. Common modules

| Module | Responsibility | Main functions |
|---|---|---|
| `corpus.py` | data entry: reading, cleaning, name harmonization, department counts | `split_bodies`, `Corpus.bodies`, `Corpus.counts_by_period`, `Corpus.resolve`, `Corpus.department_counts` |
| `graphs.py` | network construction: project the bodies of a regulation into ties | `build`, `build_weighted`, `lcc`, `period_graphs` |
| `measures.py` | structural measures, centrality, selection rules | `structure`, `centralities`, `select_top`, `select_above_mean_nonzero` |
| `typology.py` | four regulation-making patterns by median split | `thresholds`, `classify` |
| `plotting.py` | layout and drawing of the two figures | `draw_full_network`, `draw_period_network`, `global_degree_range`, `legend_handles` |
| `stats.py` | rank correlation and significance | `rank_correlation`, `format_p` |
| `output.py` | CSV output, figure saving, aligned printing | `save_table`, `save_figure`, `print_table`, `print_note`, `print_side_by_side` |

### 4.1 Data flow

```
input files
   │
   ▼
corpus    read, split bodies, map names onto network nodes, count per department
   │
   ├─► graphs     project into a network ──┬─► measures   measures and selection rules
   │                                       └─► plotting   figures
   │
   └─► typology   classify at the medians
```

### 4.2 Name harmonization

`Corpus.resolve()` tries three routes in order:

1. the name is a network node itself;
2. the name appears in the period-to-full mapping built by aligning the two joint files row by row;
3. the name's abbreviation equals that of a node.

If none applies, the function returns `None`; the regulation is skipped in counting, and the terminal reports how many names and regulations were left out.

---

## 5. Input data format

Place four Excel workbooks in `data/`:

| File | Content |
|---|---|
| `single_anon.xlsx` | Regulations issued by a single department |
| `full period_anon.xlsx` | Jointly issued regulations, names standardized to 2025 |
| `phased_anon.xlsx` | Jointly issued regulations, names standardized within each period |
| `name mapping_anon.xlsx` | Institution lookup table |

Columns of the regulation tables:

| Column | Meaning |
|---|---|
| `id` | identifier |
| `title` | regulation title (salted SHA-256 hash; not used in any computation) |
| `bodies` | issuing bodies, separated by spaces |
| `date` | issue date |
| `period` | period label |
| `body_count` | number of bodies (joint tables only) |

Columns of the lookup table: `department`, `full_name`, `abbreviation`.

File names and column names are defined in `config.py`; changing the data requires editing that file only.

---

## 6. Computation logic

### 6.1 Network construction

A regulation jointly issued by k departments contributes `C(k,2) = k(k−1)/2` undirected ties.

- Ties are binary and deduplicated: repeated co-issuance by the same pair yields one edge;
- No self-loops: bodies are deduplicated when the field is split;
- The full-period network uses `full period`; period networks use `phased`.

### 6.2 Structural measures

| Measure | Definition | Computed on |
|---|---|---|
| Nodes n | node count | full graph |
| Ties m | edge count | full graph |
| Density | `2m / (n(n−1))` | full graph |
| Largest connected component (LCC) | number of nodes in the largest connected subgraph | full graph |
| Average path length (APL) | mean shortest-path length over reachable pairs within the LCC | LCC |
| Average clustering coefficient (ACC) | mean local clustering coefficient within the LCC, degree < 2 counted as 0 | LCC |

### 6.3 Centrality

All three measures are computed on the LCC (n = number of nodes in the LCC):

| Measure | Definition |
|---|---|
| Degree | `dᵢ / (n−1)` |
| Betweenness | `Σs≠t≠i σst(i)/σst`, normalized by `2/((n−1)(n−2))` |
| Closeness | `(n−1) / Σj≠i d(i,j)` |

Departments outside the LCC are not assigned centrality values and do not appear in the corresponding tables.

### 6.4 Selection rules for the tables

| Table | Rule |
|---|---|
| Table 6, Table 8 | top 20% per period, `k = ⌈0.2n⌉`; the k-th value is the cut-off and every node at or above it is listed |
| Table 7 | above the mean of the non-zero betweenness values in that period; if all are zero, all nodes are listed |

### 6.5 Typology

Two dimensions: the total number of regulations and the share of jointly issued regulations.

- each regulation adds one unit of total to every signatory; jointly issued regulations add one unit of joint;
- two names that resolve to the same department count once per regulation;
- each dimension is split at its median, and values equal to the median count as high;
- the cross-tabulation gives four patterns: Active-Collaborative, Independent-Dominant, Collaborative-Participatory, Low-Participation.

Table 10 outputs the text-only 2×2 matrix and writes the two cut-offs, together with the number of departments on each side, to `table10_thresholds.csv`. Table 11 lists four representative departments per pattern; the full list is produced by `table11_supplementary.py`.

---

## 7. Robustness checks

The three checks do not enter any table in the main text; their results are written to four CSV files.

### 7.1 Weighted network

The network is rebuilt with each edge weighted by the number of regulations the two departments co-issued. Because edge weights are interpreted as distances, path-based measures use the reciprocal of this count as the distance, so stronger ties are closer; degree is replaced by the sum of incident weights.

Binary and weighted results are compared by Spearman rank correlation (average ranks for ties, two-sided p-values) and by the overlap of the selected lists.

### 7.2 Large-event exclusion

All structural measures and centrality rankings are recomputed after removing, in turn, only the largest regulation and all regulations with ten or more signatories. This shows how far absolute levels and rankings rest on a small number of multi-department regulations.

### 7.3 Two-mode comparison

The projected network is compared with the underlying department–regulation two-mode structure:

- for each department, the number of joint regulations signed is correlated with the number of distinct partners obtained in the projected network;
- the number of candidate pairs, the number of deduplicated ties and the resulting inflation factor are reported;
- the distribution of regulation sizes is reported.

---

## 8. Outputs

Tables are written to `output/tables/`:

| File | Corresponds to |
|---|---|
| `table02_periods.csv` | Table 2 |
| `table04_full_network.csv` | Table 4 |
| `table05_periods.csv` | Table 5 |
| `table06_degree.csv` | Table 6 |
| `table07_betweenness.csv` | Table 7 |
| `table08_closeness.csv` | Table 8 |
| `table09_joint_share.csv` | Table 9 |
| `table10_thresholds.csv` | Table 10 cut-offs |
| `table11_representative.csv` | Table 11 |
| `table11_supplementary.csv` | Table 11 full list |
| `robustness_weighted.csv` | weighted check |
| `robustness_large_events.csv` | large-event check |
| `robustness_twomode.csv` | two-mode diagnostics |
| `robustness_twomode_distribution.csv` | regulation-size distribution |

Figures are written to `output/figures/`:

| File                         | Corresponds to |
|------------------------------|----------------|
| `figure03_full_network.png`  | Figure 3       |
| `figure04_period_panels.png` | Figure 4       |

CSV files are UTF-8 with BOM so that Excel opens them directly; figures are 600 dpi on a white background.

---

## 9. Conventions

| Item | Convention |
|---|---|
| Nodes, ties, density | full graph |
| APL, clustering, all three centralities | largest connected component |
| Clustering | mean within the LCC, degree < 2 counted as 0 |
| Degree centrality | `d/(n−1)` |
| Betweenness centrality | normalized by `2/((n−1)(n−2))` |
| Closeness centrality | `(n−1)` divided by the sum of distances |
| Table 6 / 8 selection | top 20%, ties at the cut-off included |
| Table 7 selection | above the non-zero mean; all nodes if all are zero |
| Table 2 / 9 counting | each jointly issued regulation counted once |
| Table 10 / 11 counting | each signatory counted once; a department counted once per regulation |
