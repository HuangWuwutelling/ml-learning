# Causal/08 Mediation 中介分析（CGSS 2023 真实数据）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `articles/causal/08_*.md`，从"从上网频繁到把互联网当主要信息源，中间发生了什么"切入，用 6 节点 DAG（07 的 5 节点 + 新增 M' = a285 互联网使用强度）演示 mediation 机制，**用 CGSS 2023 真实数据**跑 Baron & Kenny 1986 三步法，把 07 的总效应 +0.393 拆成 NDE（直接效应）+ NIE（间接效应），用 Sobel 1982 检验 + bootstrap CI 验证间接效应显著性。

**Architecture:** 单篇文章 + 1 张封面 + 2 张概念图（6 节点 DAG + 三步法路径系数对比）。数据完全复用 07 的 CGSS 2023 STATA .dta（47.6MB，gitignored）；新增 mediator 变量 `a285` 互联网使用强度（CGSS 现有题项"过去一年您对以下媒体的使用情况-互联网"，5 级 Likert）。脚本 `gen_cover_causal_08.py` 复用 07 的 `_try_load_cgss` 函数骨架（同 single-intersection mask 模式），新增三步回归 + Sobel + bootstrap CI。

**Tech Stack:** Markdown 文章 + matplotlib（封面与 2 张概念图）+ pandas（CGSS .dta loader，复用 07）+ numpy（OLS、Sobel）+ statsmodels（OLS 带 SE）。Python 系统版本（CLAUDE.md Quick Start 约定）。CJK 字体 `Microsoft YaHei, SimHei`。

**数据流优先级**（用户明确要求：**先跑出结果，再写文章**）：
- Task 1 写脚本 + 跑脚本 → 拿到真实数字（a / b / c_total / c' / IE / Sobel p / bootstrap CI）
- Task 2 用 Task 1 的真实数字写文章（不在文章里写死数字，全部从脚本输出抄）
- Task 3 更新 _local/plan.md

## Global Constraints

- **CLAUDE.md 写作规范**：hook first、每图加 caption、参考文献内联、无 em dash（——）、无"下一篇"链接、节标题口径递进、避免 AI 腔与拟人化总结
- **memory `publish-before-push-github`**：articles/ 仓库是独立 git 仓库，文章和图都 commit 到 articles 仓库；**不 push GitHub**；root repo 改动（plan.md）也只本地 commit
- **memory `article-editing-coherence-pass`**：通读+画论证线+审接缝，不孤立逐节改
- **数据复用**：CGSS 2023 STATA .dta 已在磁盘 `articles/causal/data/中国综合社会调查（2023）/CGSS2023.dta`（gitignored）。07 的 5737 baseline 样本 → 08 加入 a285 mask 后 n=5734（验证：spec section 4 已确认）
- **6 节点 DAG → CGSS 2023 变量映射**：

| DAG 节点 | CGSS 2023 | 编码 | 08 用法 |
|---------|-----------|------|---------|
| **X** 上网频率 | a3012 空闲时间上网频率 | high(1/2) vs low(3/4/5) | 同 07 |
| **M'** 互联网使用强度 | a285 互联网使用情况 | 5 级 Likert (1=从不→5=非常频繁) | **新增 mediator** |
| **Y** 信息依赖 | a29 最主要信息来源 | 互联网=5 vs 其他=1/2/3/4 | 同 07 |
| **Z** 用户特征 | a2 + a3a(转 age) | 性别 + 连续 | 同 07 |
| **W** 社会信任 | a33 总的来说大多数人可以信任 | 5 级 Likert | 同 07 |
| **M** 生活幸福 | a36 总的来说您觉得生活是否幸福 | 5 级 Likert | 标注但不调（07 collider） |

- **核心校验**：第二步 c_total 应**严格等于 07 Backdoor +0.393**。如果不等立即排查（mask 对齐、Z/W 编码、intercept 列）。
- **配色与字体**（继承 07）：`C_L1='#4A6FA5'` / `C_L2='#D67D3E'` / `C_X='#2E5C8A'` / `C_Y='#A23B3A'` / `C_M='#888888'` / `C_CUT='#8a3030'` / `BG='#F5F2EC'` / `INK='#2A2A2A'` / `SUB='#888888'`；字体 `'Microsoft YaHei', 'SimHei'`
- **生成规格**：封面 `(9, 3.83) dpi=100` 不带 `bbox_inches='tight'`；6 节点 DAG 图 `(9, 4.5) dpi=150` 带 `bbox_inches='tight'`；三步法对比图 `(9, 4.0) dpi=150` 带 `bbox_inches='tight'`
- **数据来源**（文中内联引用）：CGSS 2023 + CNNIC《第54次报告》2024-06 + Baron & Kenny 1986 + Sobel 1982 + Pearl 2001（边界）+ VanderWeele 2015（背景）+ MacKinnon et al. 2002（背景）

---

## File Structure

| 文件 | 职责 | 路径 |
|------|------|------|
| 文章全文 | 引言 + 5 节 + 参考文献 | `articles/causal/08_*.md`（文件名定稿时定，标题候选见 spec section 1） |
| 封面 + 概念图 + 实证图生成器 | CGSS data loader + 三步回归 + Sobel + bootstrap + matplotlib 出图 | `scripts/causal/gen_cover_causal_08.py` |
| CGSS 数据 | STATA .dta（47.6MB，已在磁盘，gitignored） | `articles/causal/data/中国综合社会调查（2023）/CGSS2023.dta` |
| 封面 PNG | 公众号 feed 缩略图 | `articles/causal/cover_causal_08.png`（脚本产出） |
| 6 节点 DAG PNG | 文章内插图 fig_dag6 | `articles/causal/fig_dag6_video.png`（脚本产出） |
| 三步法对比图 PNG | 文章内插图 fig_bk | `articles/causal/fig_mediation_bk.png`（脚本产出） |
| 计划状态文件 | 项目叙事状态 | `_local/plan.md`（gitignored） |

---

## Task 0: 验证 CGSS 2023 + a285 数据可读

**Files:**
- Verify: `articles/causal/data/中国综合社会调查（2023）/CGSS2023.dta`（已在磁盘，47.6MB STATA 文件）

**Interfaces:**
- 与 07 baseline 一致的 mask 模式，验证 n=5734

- [ ] **Step 1: 确认 a285 变量分布**

```bash
cd "D:\Workspace\ml-learning" && python -c "
import pandas as pd
df = pd.read_stata('articles/causal/data/中国综合社会调查（2023）/CGSS2023.dta', convert_categoricals=False)
print('a285 (互联网使用强度):')
print(df['a285'].value_counts(dropna=False).sort_index())
print('n_valid:', df['a285'].notna().sum())
print('a285 vs X corr:', df[['a285','a3012']].dropna().corr().iloc[0,1])
"
```

预期：a285 取值 [-2.0, 1.0, 2.0, 3.0, 4.0, 5.0]（-3 不出现）；n_valid ≈ 6982；a285 vs X (a3012) corr ≈ -0.5 ~ -0.7（a285 越大=越频繁使用互联网；a3012 越小=越频繁上网。**注意方向相反**：a285 高 = 5 非常频繁，a3012 高 = 1 每天。编码方向相反，回归系数预期为负相关但显著）。

- [ ] **Step 2: 验证 6 节点 mask 交集 n=5734**

```bash
cd "D:\Workspace\ml-learning" && python -c "
import pandas as pd
df = pd.read_stata('articles/causal/data/中国综合社会调查（2023）/CGSS2023.dta', convert_categoricals=False)
x_mask = df['a3012'].isin([1.0,2.0,3.0,4.0,5.0])
y_mask = df['a29'].isin([1.0,2.0,3.0,4.0,5.0])
z_mask = df['a2'].isin([1.0,2.0]) & df['a3a'].between(1920,2005)
w_mask = df['a33'].isin([1.0,2.0,3.0,4.0,5.0])
m285_mask = df['a285'].isin([1.0,2.0,3.0,4.0,5.0])
valid = x_mask & y_mask & z_mask & w_mask & m285_mask
print(f'6-node valid n = {int(valid.sum())}')
print('预期 n=5734')
"
```

预期：n = 5734（spec section 4 已确认）。

- [ ] **Step 3: 提交验证结果**

```bash
cd "D:\Workspace\ml-learning" && git status --short
```

预期：无文件改动（仅打印验证结果）。如有意外改动，提交并解释原因。

---

## Task 1: 写图生成脚本 + 跑出真实数字（关键路径）

**Files:**
- Create: `scripts/causal/gen_cover_causal_08.py`

**Interfaces:**
- Consumes: `articles/causal/data/中国综合社会调查（2023）/CGSS2023.dta`（如不可用回退到 `_make_synthetic`）
- Produces: `articles/causal/cover_causal_08.png`（9×3.83 inch @ dpi100）、`articles/causal/fig_dag6_video.png`（9×4.5 inch @ dpi150）、`articles/causal/fig_mediation_bk.png`（9×4.0 inch @ dpi150）
- Prints to stdout: `n=...; a=...; b=...; c_total=...; c_prime=...; IE=...; SE_IE=...; Sobel_Z=...; Sobel_p=...; bootstrap_CI=[..., ...]; share_NDE=...; share_NIE=...`

- [ ] **Step 1: 新建 `scripts/causal/gen_cover_causal_08.py`**

完整脚本内容如下：

```python
"""Generate cover + 2 figures for Causal Inference #08 (Mediation Analysis).

Cover (9 x 3.83, dpi=100) - WeChat public-account feed thumbnail only.
fig_dag6_video.png (9 x 4.5, dpi=150) - 6-node DAG topology (5 from 07 + M' = a285).
fig_mediation_bk.png (9 x 4.0, dpi=150) - Baron-Kenny 3-step path coefficients.

Data: CGSS 2023 (中国综合社会调查, 11326 样本 × 437 变量, STATA .dta).
变量映射（CGSS 2023 居民问卷）：
  X = a3012 空闲时间上网频率 (high=1/2 vs low=3/4/5)
  M' = a285 互联网使用强度 (5级 Likert)
  Y = a29 最主要信息来源 (互联网=5 vs 其他=1/2/3/4)
  Z = a2 性别 + a3a 出生年（age=2023-birthyr）
  W = a33 社会信任 (5级 Likert)
  M = a36 生活幸福 (5级 Likert, 07 collider, 仅标注不调整)
如果 CGSS .dta 文件不可用，回退到内置 _make_synthetic 兜底数据。
"""
import matplotlib.pyplot as plt
import numpy as np
import os

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'articles', 'causal')
DATA = os.path.join(OUT, 'data')
os.makedirs(OUT, exist_ok=True)

# Same palette as causal_00 through 07
C_L1 = '#4A6FA5'   # primary blue (Z)
C_L2 = '#D67D3E'   # accent orange (W)
C_X  = '#2E5C8A'   # dark blue (X: treatment)
C_Y  = '#A23B3A'   # dark red (Y: outcome)
C_M  = '#888888'   # gray (M: collider)
C_MP = '#5C8A6E'   # green (M': mediator) - NEW for 08
C_CUT = '#8a3030'  # backdoor path
BG   = '#F5F2EC'
INK  = '#2A2A2A'
SUB  = '#888888'

COVER_PATH = os.path.join(OUT, 'cover_causal_08.png')
FIG_DAG6_PATH = os.path.join(OUT, 'fig_dag6_video.png')
FIG_BK_PATH = os.path.join(OUT, 'fig_mediation_bk.png')

CGSS_DTA = os.path.join(DATA, '中国综合社会调查（2023）', 'CGSS2023.dta')


# ============================================================
# Data loading: CGSS 2023 (priority) or synthetic fallback
# ============================================================
def _try_load_cgss():
    """Load CGSS 2023 STATA. Return (X, Y, Z, W, M_prime) or None.

    Single-intersection mask pattern (fixes 07's data alignment bug).
    Returns None if data unavailable.
    """
    if not os.path.exists(CGSS_DTA):
        return None
    try:
        import pandas as pd
        df = pd.read_stata(CGSS_DTA, convert_categoricals=False)
    except Exception as e:
        print(f'[WARN] CGSS .dta load failed: {e}; falling back to synthetic data')
        return None

    # 6 masks
    x_mask = df['a3012'].isin([1.0, 2.0, 3.0, 4.0, 5.0])
    y_mask = df['a29'].isin([1.0, 2.0, 3.0, 4.0, 5.0])
    z_mask = df['a2'].isin([1.0, 2.0]) & df['a3a'].between(1920, 2005)
    w_mask = df['a33'].isin([1.0, 2.0, 3.0, 4.0, 5.0])
    m285_mask = df['a285'].isin([1.0, 2.0, 3.0, 4.0, 5.0])

    # Single intersection (CRITICAL: do not min-truncate after per-variable masks)
    valid = x_mask & y_mask & z_mask & w_mask & m285_mask
    n = int(valid.sum())
    if n < 100:
        print(f'[WARN] too few valid samples ({n}); falling back to synthetic')
        return None

    df_v = df.loc[valid].copy()
    X = df_v['a3012'].isin([1.0, 2.0]).astype(float).values  # high=1
    M_prime = df_v['a285'].astype(float).values  # 1-5 Likert
    Y = (df_v['a29'] == 5.0).astype(float).values  # internet=1
    gender = (df_v['a2'] == 1.0).astype(float).values  # 1=男
    age = (2023 - df_v['a3a']).astype(float).values
    Z = np.column_stack([gender, age])
    W = df_v['a33'].astype(float).values  # 1-5 Likert

    print(f'[OK] CGSS 2023 loaded: n={n}')
    print(f'  X high={X.mean():.3f}, Y internet={Y.mean():.3f}, M_prime mean={M_prime.mean():.3f}')
    print(f'  W mean={W.mean():.3f}, gender={gender.mean():.3f}, age mean={age.mean():.1f}')
    return X, Y, Z, W, M_prime


def _make_synthetic(n=5734, seed=42):
    """Synthetic fallback matching CGSS 2023 真实分布（基于 07 实测）。"""
    rng = np.random.default_rng(seed)
    X = rng.binomial(1, 0.71, n)  # 71% 高强度上网
    gender = rng.binomial(1, 0.46, n)
    age = rng.normal(53.5, 16.0, n).clip(18, 95)
    W = rng.normal(3.49, 1.0, n).clip(1, 5)
    # M' : 受 X 强烈正向影响
    M_prime = (3.0 + 1.2 * X - 0.005 * age + 0.05 * W + rng.normal(0, 0.8, n)).clip(1, 5)
    # Y : 受 X 直接 + M' 中介
    p = 1 / (1 + np.exp(-(0.5 * X + 0.6 * (M_prime - 3) / 2 - 0.4 * (age - 53.5) / 16 - 0.15 * (W - 3.49) - 1.0)))
    Y = (rng.random(n) < p).astype(float)
    Z = np.column_stack([gender, age])
    print(f'[FALLBACK] Using synthetic data: n={n}')
    return X, Y, Z, W, M_prime


def _load_data():
    result = _try_load_cgss()
    if result is None:
        return _make_synthetic()
    return result


# ============================================================
# OLS with intercept (matches 07 fix)
# ============================================================
def _ols_with_se(X, Y):
    """OLS regression: Y = X @ beta, return (beta, SE_beta, residuals).

    X should include the intercept column as X[:, 0] = 1.
    Returns beta, SE, residuals.
    """
    n, k = X.shape
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ Y
    resid = Y - X @ beta
    sigma2 = (resid @ resid) / (n - k)
    SE_beta = np.sqrt(np.diag(sigma2 * XtX_inv))
    return beta, SE_beta, resid


# ============================================================
# Baron & Kenny 3-step mediation
# ============================================================
def _estimate_mediation(X, Y, Z, W, M_prime):
    """Run 3-step mediation, return dict with all estimates.

    Step 1: M' ~ X + Z + W  -> a, SE_a
    Step 2: Y ~ X + Z + W   -> c_total (MUST equal 07 Backdoor +0.393)
    Step 3: Y ~ X + M' + Z + W -> c_prime (NDE), b (M' coefficient)

    Sobel test for indirect effect IE = a * b.
    """
    n = len(X)
    # Build design matrices (intercept + X + Z + W, optionally + M')
    ones = np.ones((n, 1))

    # Step 1: M' = a0 + a*X + aZ1*gender + aZ2*age + aW*W
    D1 = np.column_stack([ones, X, Z[:, 0], Z[:, 1], W])
    beta1, SE1, _ = _ols_with_se(D1, M_prime)
    a = beta1[1]
    SE_a = SE1[1]

    # Step 2: Y = c0 + c_total*X + cZ1*gender + cZ2*age + cW*W
    D2 = np.column_stack([ones, X, Z[:, 0], Z[:, 1], W])
    beta2, SE2, _ = _ols_with_se(D2, Y)
    c_total = beta2[1]
    SE_c_total = SE2[1]

    # Step 3: Y = c0' + c'*X + b*M' + bZ1*gender + bZ2*age + bW*W
    D3 = np.column_stack([ones, X, M_prime, Z[:, 0], Z[:, 1], W])
    beta3, SE3, _ = _ols_with_se(D3, Y)
    c_prime = beta3[1]
    b = beta3[2]
    SE_c_prime = SE3[1]
    SE_b = SE3[2]

    # Indirect effect + Sobel test
    IE = a * b
    SE_IE_sobel = np.sqrt(b**2 * SE_a**2 + a**2 * SE_b**2)
    sobel_Z = IE / SE_IE_sobel if SE_IE_sobel > 0 else 0.0
    # Two-sided p-value (normal approximation)
    from math import erf, sqrt
    sobel_p = 2 * (1 - 0.5 * (1 + erf(abs(sobel_Z) / sqrt(2))))

    # Bootstrap CI for IE
    rng = np.random.default_rng(42)
    B = 1000
    IE_boot = np.empty(B)
    for i in range(B):
        idx = rng.integers(0, n, n)
        Xb, Yb, Zb, Wb, Mb = X[idx], Y[idx], Z[idx], W[idx], M_prime[idx]
        D1b = np.column_stack([np.ones(n), Xb, Zb[:, 0], Zb[:, 1], Wb])
        D3b = np.column_stack([np.ones(n), Xb, Mb, Zb[:, 0], Zb[:, 1], Wb])
        b1 = np.linalg.lstsq(D1b, Mb, rcond=None)[0]
        b3 = np.linalg.lstsq(D3b, Yb, rcond=None)[0]
        IE_boot[i] = b1[1] * b3[2]
    IE_ci_low, IE_ci_high = np.percentile(IE_boot, [2.5, 97.5])

    # Shares
    share_NDE = c_prime / c_total if c_total != 0 else np.nan
    share_NIE = IE / c_total if c_total != 0 else np.nan

    return {
        'n': n,
        'a': a, 'SE_a': SE_a,
        'b': b, 'SE_b': SE_b,
        'c_total': c_total, 'SE_c_total': SE_c_total,
        'c_prime': c_prime, 'SE_c_prime': SE_c_prime,
        'IE': IE,
        'SE_IE_sobel': SE_IE_sobel,
        'sobel_Z': sobel_Z,
        'sobel_p': sobel_p,
        'IE_ci_low': IE_ci_low,
        'IE_ci_high': IE_ci_high,
        'share_NDE': share_NDE,
        'share_NIE': share_NIE,
    }


# ============================================================
# Figure 1: Cover (9 x 3.83, dpi=100)
# ============================================================
def make_cover(values):
    fig = plt.figure(figsize=(9, 3.83), dpi=100, facecolor=BG)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.1, 0.9, 1.4], left=0.04, right=0.98, top=0.85, bottom=0.10, wspace=0.20)

    # Left: 6-node DAG mini
    ax_dag = fig.add_subplot(gs[0, 0]); ax_dag.set_facecolor(BG); ax_dag.axis('off')
    ax_dag.set_xlim(0, 1); ax_dag.set_ylim(0, 1)
    # X, M', Y, Z, W, M (top to bottom roughly)
    nodes = {
        'X':   (0.10, 0.85, C_X, 'X\n上网频率'),
        "M'":  (0.55, 0.85, C_MP, "M'\n互联网使用"),
        'Y':   (1.00, 0.85, C_Y, 'Y\n互联网依赖'),
        'Z':   (0.10, 0.30, C_L1, 'Z\n性别/年龄'),
        'W':   (0.55, 0.30, C_L2, 'W\n社会信任'),
        'M':   (1.00, 0.30, C_M, 'M\n生活幸福'),
    }
    for name, (x, y, c, lab) in nodes.items():
        ax_dag.scatter([x], [y], s=900, c=c, edgecolors='white', linewidths=1.5, zorder=3)
        ax_dag.text(x, y, lab, ha='center', va='center', fontsize=7.5, color='white', zorder=4)
    # Edges
    def edge(xy1, xy2, c='black', style='-', lw=1.4, alpha=1.0, z=1):
        ax_dag.annotate('', xy=xy2, xytext=xy1,
                         arrowprops=dict(arrowstyle='->', color=c, lw=lw, ls=style, alpha=alpha), zorder=z)
    edge(nodes['X'][0:2],   nodes["M'"][0:2], 'black')
    edge(nodes["M'"][0:2],  nodes['Y'][0:2], 'black')
    edge(nodes['X'][0:2],   nodes['Y'][0:2], C_CUT, '--', 1.0, 0.5)
    edge((nodes['Z'][0], nodes['Z'][1]+0.05), (nodes['X'][0], nodes['X'][1]-0.05), C_L1, '--')
    edge((nodes['Z'][0], nodes['Z'][1]+0.05), (nodes["M'"][0], nodes["M'"][1]-0.05), C_L1, '--')
    edge((nodes['W'][0], nodes['W'][1]+0.05), (nodes['X'][0], nodes['X'][1]-0.05), C_L2, '--')
    edge((nodes['W'][0], nodes['W'][1]+0.05), (nodes["M'"][0], nodes["M'"][1]-0.05), C_L2, '--')
    # collider M
    edge((nodes['M'][0], nodes['M'][1]+0.05), (nodes['X'][0]+0.02, nodes['X'][1]-0.02), C_M, '-', 0.7)
    edge((nodes['M'][0], nodes['M'][1]+0.05), (nodes['Y'][0]-0.02, nodes['Y'][1]-0.02), C_M, '-', 0.7)
    ax_dag.text(0.55, 0.04, '6 节点 DAG：X→M\'→Y 主路径 + Z/W 后门', ha='center', fontsize=7.5, color=INK)

    # Middle: "+X%" callout
    ax_mid = fig.add_subplot(gs[0, 1]); ax_mid.set_facecolor(BG); ax_mid.axis('off')
    ax_mid.text(0.5, 0.78, '中间效应', ha='center', fontsize=12, color=INK)
    IE_pct = values['share_NIE'] * 100
    ax_mid.text(0.5, 0.55, f'{IE_pct:+.0f}%', ha='center', fontsize=36, color=C_MP, weight='bold')
    ax_mid.text(0.5, 0.32, '的因果效应\n走 a285 这条中介', ha='center', fontsize=9, color=INK)
    ax_mid.text(0.5, 0.10, f'间接效应 = {values["IE"]:+.3f}', ha='center', fontsize=8, color=SUB, style='italic')

    # Right: 4-bar (a / b / c_total / c')
    ax_bar = fig.add_subplot(gs[0, 2]); ax_bar.set_facecolor(BG)
    labels = ['a\n(X→M\')', 'b\n(M\'→Y)', 'c_total\n总效应', 'c\'\n直接效应']
    vals = [values['a'], values['b'], values['c_total'], values['c_prime']]
    colors = [C_X, C_MP, C_CUT, C_Y]
    bars = ax_bar.barh(labels, vals, color=colors, edgecolor='white', height=0.55)
    ax_bar.axvline(0, color=SUB, linewidth=0.6)
    ax_bar.set_xlim(min(min(vals), 0) - 0.1, max(max(vals), 0) + 0.1)
    for bar, v in zip(bars, vals):
        ax_bar.text(v + (0.01 if v >= 0 else -0.01), bar.get_y() + bar.get_height()/2,
                    f'{v:+.3f}', ha='left' if v >= 0 else 'right', va='center', fontsize=8, color=INK)
    ax_bar.set_xlabel('回归系数', fontsize=9)
    ax_bar.tick_params(axis='y', labelsize=8)
    ax_bar.tick_params(axis='x', labelsize=7)
    ax_bar.spines['top'].set_visible(False); ax_bar.spines['right'].set_visible(False)
    ax_bar.set_title('BK 三步法系数', fontsize=10, color=INK, pad=4)

    # Bottom title bar
    fig.text(0.5, 0.04,
             '把 0.39 拆开：直接效应 vs 间接效应（a285 互联网使用强度）',
             ha='center', fontsize=11, color=INK)
    fig.text(0.5, 0.005,
             'Mediation · Baron & Kenny 1986 三步法 + Sobel 检验 · CGSS 2023 n=5734',
             ha='center', fontsize=7.5, color=SUB, style='italic')

    plt.savefig(COVER_PATH, dpi=100, facecolor=BG)
    plt.close(fig)
    print(f'Cover saved: {COVER_PATH}')


# ============================================================
# Figure 2: 6-node DAG (9 x 4.5, dpi=150)
# ============================================================
def make_fig_dag6():
    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=150, facecolor=BG)
    ax.set_facecolor(BG); ax.axis('off')
    ax.set_xlim(0, 10); ax.set_ylim(0, 6)

    # Position 6 nodes
    pos = {
        'X':    (1.5, 3.0, C_X,  'X\n上网频率\na3012'),
        "M'":   (5.0, 3.0, C_MP, "M'\n互联网使用\na285"),
        'Y':    (8.5, 3.0, C_Y,  'Y\n互联网作为\n主要信息源\na29'),
        'Z':    (1.5, 5.0, C_L1, 'Z\n性别 + 年龄\na2 + a3a'),
        'W':    (5.0, 5.0, C_L2, 'W\n社会信任\na33'),
        'M':    (8.5, 5.0, C_M,  'M\n生活幸福\na36 (collider)'),
    }
    # Draw nodes
    for name, (x, y, c, lab) in pos.items():
        ax.scatter([x], [y], s=2400, c=c, edgecolors='white', linewidths=2, zorder=3)
        ax.text(x, y, lab, ha='center', va='center', fontsize=8, color='white', zorder=4, weight='bold')
    # Edges
    def edge(xy1, xy2, c='black', style='-', lw=1.6, alpha=1.0):
        ax.annotate('', xy=xy2, xytext=xy1,
                     arrowprops=dict(arrowstyle='->', color=c, lw=lw, ls=style, alpha=alpha), zorder=2)
    # Main path
    edge(pos['X'][0:2], pos["M'"][0:2], 'black', lw=2.2)
    edge(pos["M'"][0:2], pos['Y'][0:2], 'black', lw=2.2)
    # Direct X -> Y (smaller, red dashed)
    edge(pos['X'][0:2], pos['Y'][0:2], C_CUT, '--', 1.2, 0.7)
    # Backdoors from Z
    edge((pos['Z'][0], pos['Z'][1]-0.3), (pos['X'][0], pos['X'][1]+0.3), C_L1, '--', 1.4)
    edge((pos['Z'][0], pos['Z'][1]-0.3), (pos["M'"][0], pos["M'"][1]+0.3), C_L1, '--', 1.4)
    edge((pos['Z'][0], pos['Z'][1]-0.3), (pos['Y'][0], pos['Y'][1]+0.3), C_L1, '--', 1.4)
    # Backdoors from W
    edge((pos['W'][0], pos['W'][1]-0.3), (pos['X'][0]+0.3, pos['X'][1]+0.3), C_L2, '--', 1.4)
    edge((pos['W'][0], pos['W'][1]-0.3), (pos["M'"][0], pos["M'"][1]+0.3), C_L2, '--', 1.4)
    edge((pos['W'][0], pos['W'][1]-0.3), (pos['Y'][0]-0.3, pos['Y'][1]+0.3), C_L2, '--', 1.4)
    # Collider M
    edge((pos['M'][0], pos['M'][1]-0.3), (pos['X'][0]+0.3, pos['X'][1]+0.2), C_M, '-', 1.0, 0.7)
    edge((pos['M'][0], pos['M'][1]-0.3), (pos['Y'][0]-0.3, pos['Y'][1]+0.2), C_M, '-', 1.0, 0.7)

    # Legend
    legend_items = [
        ('黑色实线', '主路径（X→M\'→Y）', 'black', '-'),
        ('深红虚线', 'X→Y 直接路径', C_CUT, '--'),
        ('蓝色虚线', 'Z 后门（已控制）', C_L1, '--'),
        ('橙色虚线', 'W 后门（已控制）', C_L2, '--'),
        ('灰色实线', 'Collider M (07 标注)', C_M, '-'),
    ]
    for i, (label, desc, c, style) in enumerate(legend_items):
        y = 0.5 - i * 0.18
        ax.plot([0.5], [y], marker='None', linestyle=style, color=c, lw=2)
        ax.text(1.2, y, f'{label} {desc}', va='center', fontsize=8, color=INK)

    ax.set_title('6 节点 DAG（X / M\' / Y / Z / W / M）', fontsize=11, color=INK, pad=8)
    plt.tight_layout()
    plt.savefig(FIG_DAG6_PATH, dpi=150, facecolor=BG, bbox_inches='tight')
    plt.close(fig)
    print(f'6-node DAG figure saved: {FIG_DAG6_PATH}')


# ============================================================
# Figure 3: BK 3-step path coefficient comparison (9 x 4.0, dpi=150)
# ============================================================
def make_fig_mediation_bk(values):
    fig, ax = plt.subplots(figsize=(9, 4.0), dpi=150, facecolor=BG)
    ax.set_facecolor(BG)

    # 4 vertical bars: a, b, c_total, c_prime
    labels = ['a\n(X→M\')', 'b\n(M\'→Y)', 'c_total\n(总效应)', "c'\n(直接效应)"]
    vals = [values['a'], values['b'], values['c_total'], values['c_prime']]
    SEs = [values['SE_a'], values['SE_b'], values['SE_c_total'], values['SE_c_prime']]
    colors = [C_X, C_MP, C_CUT, C_Y]

    x = np.arange(len(labels))
    bars = ax.bar(x, vals, color=colors, edgecolor='white', width=0.55, yerr=SEs,
                  error_kw={'linewidth': 1.2, 'ecolor': SUB, 'capsize': 4})
    ax.axhline(0, color=SUB, linewidth=0.6, linestyle='-')

    # Annotate values on bars
    for bar, v, se in zip(bars, vals, SEs):
        h = bar.get_height()
        offset = 0.015 if h >= 0 else -0.025
        ax.text(bar.get_x() + bar.get_width()/2, h + offset,
                f'{v:+.3f}\n(±{se:.3f})',
                ha='center', va='bottom' if h >= 0 else 'top',
                fontsize=8.5, color=INK)

    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9.5)
    ax.set_ylabel('OLS 回归系数', fontsize=10)
    ax.set_title(f'BK 三步法路径系数 · 间接效应 IE = a × b = {values["IE"]:+.3f} (Sobel p={values["sobel_p"]:.4f})',
                 fontsize=10.5, color=INK, pad=10)
    ax.tick_params(axis='y', labelsize=9)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.set_ylim(min(min(vals) - 0.1, -0.05), max(max(vals) + 0.15, 0.5))

    # Footer annotation
    ax.text(0.5, -0.18,
            f'NDE 占比 = {values["share_NDE"]*100:.1f}% · NIE 占比 = {values["share_NIE"]*100:.1f}% · bootstrap 95% CI = [{values["IE_ci_low"]:+.3f}, {values["IE_ci_high"]:+.3f}]',
            transform=ax.transAxes, ha='center', fontsize=8.5, color=SUB, style='italic')
    plt.tight_layout()
    plt.savefig(FIG_BK_PATH, dpi=150, facecolor=BG, bbox_inches='tight')
    plt.close(fig)
    print(f'Mediation BK figure saved: {FIG_BK_PATH}')


if __name__ == '__main__':
    X, Y, Z, W, M_prime = _load_data()
    values = _estimate_mediation(X, Y, Z, W, M_prime)

    # Print all numbers for Task 2 (article writing)
    print('\n=== Mediation Analysis Results ===')
    print(f'n                  = {values["n"]}')
    print(f'a  (X→M\')         = {values["a"]:+.4f}  (SE={values["SE_a"]:.4f})')
    print(f'b  (M\'→Y)         = {values["b"]:+.4f}  (SE={values["SE_b"]:.4f})')
    print(f'c_total (总效应)   = {values["c_total"]:+.4f}  (SE={values["SE_c_total"]:.4f})')
    print(f'c_prime (直接效应) = {values["c_prime"]:+.4f}  (SE={values["SE_c_prime"]:.4f})')
    print(f'IE (间接效应 a×b)  = {values["IE"]:+.4f}')
    print(f'Sobel Z           = {values["sobel_Z"]:+.4f}')
    print(f'Sobel p           = {values["sobel_p"]:.6f}')
    print(f'bootstrap 95% CI  = [{values["IE_ci_low"]:+.4f}, {values["IE_ci_high"]:+.4f}]')
    print(f'NDE 占比          = {values["share_NDE"]*100:.2f}%')
    print(f'NIE 占比          = {values["share_NIE"]*100:.2f}%')
    print('===================================\n')

    # **Sanity check**: c_total should equal 07 Backdoor +0.393
    expected_c_total = 0.393
    if abs(values['c_total'] - expected_c_total) > 0.005:
        print(f'[FAIL] c_total = {values["c_total"]:+.4f} ≠ expected {expected_c_total}')
        print('       This means Step 2 regression differs from 07 Backdoor.')
        print('       Check: mask alignment, Z/W encoding, intercept column.')
    else:
        print(f'[PASS] c_total = {values["c_total"]:+.4f} ≈ 07 Backdoor {expected_c_total} ✓')

    make_cover(values)
    make_fig_dag6()
    make_fig_mediation_bk(values)
    print('Done.')
```

- [ ] **Step 2: 跑脚本生成三张图 + 输出真实数字**

```bash
cd "D:\Workspace\ml-learning" && python scripts/causal/gen_cover_causal_08.py
```

预期：终端打印类似如下（**数字以实测为准**，脚本会原样输出）：

```
[OK] CGSS 2023 loaded: n=5734
  X high=0.710, Y internet=0.679, M_prime mean=3.XXX
  W mean=3.490, gender=0.462, age mean=53.5

=== Mediation Analysis Results ===
n                  = 5734
a  (X→M')         = -X.XXXX  (SE=X.XXXX)
b  (M'→Y)         = +X.XXXX  (SE=X.XXXX)
c_total (总效应)   = +0.393X  (SE=0.0XXX)
c_prime (直接效应) = +X.XXXX  (SE=0.0XXX)
IE (间接效应 a×b)  = +X.XXXX
Sobel Z           = +X.XXXX
Sobel p           = 0.000000
bootstrap 95% CI  = [+X.XXXX, +X.XXXX]
NDE 占比          = XX.XX%
NIE 占比          = XX.XX%
===================================

[PASS] c_total = +0.393X ≈ 07 Backdoor 0.393 ✓

Cover saved: ...
6-node DAG figure saved: ...
Mediation BK figure saved: ...
Done.
```

**关键检查**：
1. `[PASS] c_total ≈ 07 Backdoor 0.393` 必须出现
2. Sobel p < 0.05（间接效应显著）
3. bootstrap CI 不含 0
4. NDE + NIE 应近似 = c_total（拆解恒等式）

- [ ] **Step 3: 视觉检查三张图**

打开 `articles/causal/cover_causal_08.png`、`fig_dag6_video.png`、`fig_mediation_bk.png`，确认：
- **封面**：左侧 6 节点 DAG 清晰可读；中间 "+XX%" callout 大字；右侧 4-bar 横图（a / b / c_total / c'）；底部标题 + 副标题
- **fig_dag6**：6 个节点位置（X 左中 / M' 中中 / Y 右中 / Z/W/M 上排）；主路径（黑色粗实线）+ 后门（蓝色/橙色虚线）+ collider M（灰色实线）；底部 legend 5 项
- **fig_bk**：4 个竖柱（a / b / c_total / c'）+ 误差棒；柱顶数值 + SE；标题包含 IE 与 Sobel p；底部 NDE/NIE 占比 + bootstrap CI
- CJK 字体显示正常（无方框）

任何一项不符，回去调整 Step 1 的脚本重跑。

- [ ] **Step 4: 提交到 articles 仓库**

```bash
cd "D:\Workspace\ml-learning\articles" && git add "scripts/causal/gen_cover_causal_08.py" "causal/cover_causal_08.png" "causal/fig_dag6_video.png" "causal/fig_mediation_bk.png" && git commit -m "art(causal/08): 封面 + 6 节点 DAG + BK 三步法——CGSS 2023 实证拆解总效应"
```

预期：1 个 commit 包含 4 个文件改动（脚本 + 3 张新图）。**.dta 数据文件不 commit**（gitignored）。

---

## Task 2: 写文章 08_*.md（用 Task 1 真实数字）

**Files:**
- Create: `articles/causal/08_*.md`（文件名按 spec section 1 候选标题定稿）

**Interfaces:**
- Consumes: Task 1 终端输出的全部数字（a / b / c_total / c' / IE / Sobel / bootstrap CI / NDE 占比 / NIE 占比）
- 引用 3 张图：`cover_causal_08.png` / `fig_dag6_video.png` / `fig_mediation_bk.png`

- [ ] **Step 1: 从 Task 1 输出抄录数字到 spec 草稿区**

打开 `docs/superpowers/specs/2026-09-05-causal-08-mediation-design.md`，把 Task 1 输出的数字填到 section 6（与 07 数字的横向对比表）的预期值列。**文章里所有数字必须以 Task 1 输出为准，不能在文章里"理论猜值"**。

- [ ] **Step 2: 起标题（spec section 1 候选 A/B/C）**

候选 A：「沉迷归因（二）：把 0.39 拆开，直接效应和间接效应谁更大？」
候选 B：「上网的人到底是怎么把互联网当主要信息源的？Mediation 拆解」
候选 C：「从上网频繁到互联网依赖，中间经历了什么？」

**默认选 C**（机制问句钩子，与 spec 一致）。如果 Task 1 数字特别显著或反直觉，可在写作时微调。

- [ ] **Step 3: 起草 5 节正文**

文件结构：

```markdown
# [定稿标题]

> [引言 blockquote：2-3 句话，包含 CNNIC 数据 + 机制问句 + 总效应数字 0.393]

<div align="center"><img src="cover_causal_08.png" alt="封面" width="700"></div>
<p align="center" style="color:#656d76;font-size:14px;margin-top:2px;">[封面 caption：用 Task 1 实测数字替换占位]</p>

## 一、两组互联网依赖差多少？

- 高强度上网组 vs 低频组：互联网作为主要信息源比例对比（用 Task 1 输出的 X high mean 反推）
- 朴素差距：约 0.69
- 引出机制问句：从这个差距到 0.39（剥离 confounder 后）再到 X.XX（拆出 mediator 后），中间发生了什么？

## 二、机制假说：X → a285 互联网使用强度 → Y

- 6 节点 DAG 介绍（图1）
- 解释 a285 为什么是 mediator：X 增 → 互联网使用强度增 → 互联网作为信息源更合理
- 与 07 的 collider M (a36) 对比：M 是 X 和 Y 的共同结果（collider），M' 是 X 的下游 + Y 的上游（mediator）
- a285 vs a3012 语义差别：行为频率 vs 整体感受

## 三、Baron & Kenny 三步法：把总效应拆开

- 三步回归模型 + 三组系数含义（c_total / a / c' / b）
- 间接效应 IE = a × b
- Sobel 检验公式：SE_IE = sqrt(b²·SE_a² + a²·SE_b²)
- 与 07 PSM 角色对比：07 剥离 confounder 看 X→Y 的真实大小；08 把真实大小再拆成直接 + 间接

## 四、CGSS 2023 实证拆解（n=5734）

- **第一步**：M' ~ X + Z + W → a 值（**用 Task 1 输出**），解释高强度上网者互联网使用强度差异
- **第二步**：Y ~ X + Z + W → c_total ≈ +0.393（**应等于 07 Backdoor，文章核心校验点**）
- **第三步**：Y ~ X + M' + Z + W → c'（直接）+ b（间接路径系数）
- **间接效应 IE = a × b** + Sobel Z 值 + p 值（**全部用 Task 1 输出**）
- **bootstrap 95% CI**（**用 Task 1 输出**）
- **NDE 占比 / NIE 占比**（**用 Task 1 输出**）
- 拆解占比图（图3）

## 五、机制答案 + 边界

- 机制答案：直接给答"中间发生了什么"
- 边界 1：a285 是否真的是 mediator（partial vs full mediator 讨论）
- 边界 2：CGSS 横截面 → 无法验证 X→M' 与 M'→Y 的时序（Pearl 2001 因果定义讨论）
- 边界 3：a285 不一定是唯一 mediator，可能还有未测量的路径
- 回到机制问句收尾

## 参考文献

1. Baron, R. M. & Kenny, D. A. (1986). The Moderator-Mediator Variable Distinction in Social Psychological Research. *Journal of Personality and Social Psychology*, 51(6), 1173-1182.
2. Sobel, M. E. (1982). Asymptotic Confidence Intervals for Indirect Effects in Structural Equation Models. *Sociological Methodology*, 13, 290-312.
3. Pearl, J. (2001). Direct and Indirect Effects. *Proceedings of UAI*, 411-420.
4. VanderWeele, T. J. (2015). *Explanation in Causal Inference: Methods for Mediation and Interaction*. Oxford University Press.
5. MacKinnon, D. P., Lockwood, C. M., Hoffman, J. M., West, S. G. & Sheets, V. (2002). A Comparison of Methods to Test Mediation and Other Intervening Variable Effects. *Psychological Methods*, 7(1), 83-104.
6. 中国综合社会调查项目组 (2023). 《中国综合社会调查（CGSS）2023 年居民问卷》.
7. CNNIC (2024). 《第54次中国网络发展状况统计报告》.
```

**重要**：每节标题口径递进（现象 → 假说 → 方法 → 实证 → 含义），与 spec section 2 一致。

- [ ] **Step 4: 通读全文审接缝**

按 `article-editing-coherence-pass` memory 走：先通读、画论证线、检查接缝。重点检查：
- 论证线：现象差距 → 6 节点 DAG → BK 三步法 → 拆解数字 → 机制答案 + 边界
- 称谓统一：引言用"互联网作为主要信息源"；正文中"互联网使用强度"或"a285"是技术语（与 CGSS 变量名一致）；CGSS 数据用"上网"（混合 PC + 手机），蓝皮书用"短视频时长"
- 术语统一：mediator、indirect effect、direct effect、BK、Sobel 在首次出现时给中英括注
- 数字与 Task 1 输出严格一致（不允许在文章里"修正"或"圆整"任务输出）
- 内联引用 vs 参考文献对应
- 无 em dash（——）
- 无"**下一篇**"链接（第五节末尾用"……下一篇讲..."作为概念预告不算"下一篇"链接）
- 每图 caption 完整（封面 caption + 图1 caption + 图2 caption + 图3 caption）

任何接缝问题在 articles 仓库本地修改。

- [ ] **Step 5: 提交到 articles 仓库**

```bash
cd "D:\Workspace\ml-learning\articles" && git add "causal/08_*.md" && git commit -m "draft(causal/08): [定稿标题]——6 节点 DAG + CGSS 2023 BK 三步法实证拆解"
```

预期：1 个 commit 包含 1 个文件改动。

---

## Task 3: 更新 _local/plan.md 状态

**Files:**
- Modify: `_local/plan.md`（gitignored，本地唯一事实源）

- [ ] **Step 1: 定位 causal/07 行附近**

```bash
cd "D:\Workspace\ml-learning" && grep -n "^| 07 \|^| 08 " _local/plan.md
```

预期：07 行存在，08 行不存在。

- [ ] **Step 2: 在 07 行后插入 08 行**

```
| 08 | [定稿标题] | DAG 因果图、6 节点 DAG（X 上网频率 a3012 / M' 互联网使用强度 a285 / Y 信息依赖 a29 / Z 性别年龄 a2+a3a / W 社会信任 a33 / M 生活幸福 a36 标注 collider）、Mediation 中介分析、Baron & Kenny 1986 三步法、Sobel 1982 检验 + bootstrap CI、CGSS 2023（n=5734，复用 07 数据） | 通用 | 📝 草稿（2026-09-06 spec 完成 + 实证数字：a=.../b=.../c_total=.../c_prime=.../IE=.../Sobel p=...；待用户手动真实发布） |
```

将 `...` 替换为 Task 1 实测数字。

- [ ] **Step 3: 提交到 root repo**

```bash
cd "D:\Workspace\ml-learning" && git add _local/plan.md && git commit -m "chore(plan): 因果线 #08 状态登记——Mediation 实证完成，待手动真实发布"
```

预期：1 个 commit 包含 1 个文件改动。**注意**：`_local/` 是 gitignored。如果 commit 报"nothing to commit"或"pathspec ... did not match"，先 `git ls-files _local/plan.md` 检查它是否被跟踪；若没跟踪，跳过此 commit。

---

## Verification

执行完 Task 0-3 后做总验证：

1. **CGSS 数据可读 + n=5734**（Task 0）：
   ```bash
   cd "D:\Workspace\ml-learning" && python -c "
   import pandas as pd
   df = pd.read_stata('articles/causal/data/中国综合社会调查（2023）/CGSS2023.dta', convert_categoricals=False)
   x = df['a3012'].isin([1.0,2.0,3.0,4.0,5.0])
   y = df['a29'].isin([1.0,2.0,3.0,4.0,5.0])
   z = df['a2'].isin([1.0,2.0]) & df['a3a'].between(1920,2005)
   w = df['a33'].isin([1.0,2.0,3.0,4.0,5.0])
   m = df['a285'].isin([1.0,2.0,3.0,4.0,5.0])
   print('6-node valid n =', int((x & y & z & w & m).sum()))
   "
   ```
   预期：n = 5734

2. **第二步 c_total ≈ 07 Backdoor +0.393**（Task 1 sanity check）：
   ```bash
   cd "D:\Workspace\ml-learning" && python scripts/causal/gen_cover_causal_08.py 2>&1 | grep "PASS\|FAIL"
   ```
   预期：`[PASS] c_total = +0.39XX ≈ 07 Backdoor 0.393 ✓`

3. **Sobel p < 0.05**（间接效应显著）：
   ```bash
   cd "D:\Workspace\ml-learning" && python scripts/causal/gen_cover_causal_08.py 2>&1 | grep "Sobel p"
   ```
   预期：p < 0.05（实际更可能 < 0.001）

4. **articles 仓库最终状态**（不 push）：
   ```bash
   cd "D:\Workspace\ml-learning\articles" && git log --oneline -4 && echo "---" && git status --short
   ```
   预期：最近 2 个 commit 是 Task 1（art: 封面+DAG+BK）和 Task 2（draft: 文章）。`git status --short` 对 `causal/` 目录应是干净的（.dta 不跟踪）。

5. **图片与文章引用对得上**：
   ```bash
   cd "D:\Workspace\ml-learning\articles" && grep -E "cover_causal_08|fig_dag6_video|fig_mediation_bk" "causal/08_*.md"
   ```
   预期：3 行引用，对应 Task 1 产出的 3 张图。

6. **文章无 em dash、无"下一篇"链接**：
   ```bash
   cd "D:\Workspace\ml-learning\articles" && grep -E "——|\*\*下一篇\*\*" "causal/08_*.md" || echo "PASS: 无 em dash / 无下一篇"
   ```
   预期：PASS。

7. **5 节标题与 spec 一致**：
   ```bash
   cd "D:\Workspace\ml-learning\articles" && grep -E "^## " "causal/08_*.md"
   ```
   预期：5 节标题与 spec section 2 的 5 节骨架对齐。
