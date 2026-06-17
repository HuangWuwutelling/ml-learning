# 武汉新洲泡花碱厂调查通报科普文 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 写出环境科普系列第 7 篇文章 + 1 张封面 + 1 张链状对比图，更新 plan.md 和 CLAUDE.md，让姊妹篇（C8 案与武汉案）成为完整论证对。

**Architecture:** 沿用项目现有 env 系列结构 — `scripts/gen_cover_env_0N.py` 生成 900×383 封面，`scripts/gen_fig_*.py` 生成文章内插图，正文 markdown 引用 PNG，plan.md 和 CLAUDE.md 同步登记。本项目不是 git 仓库（per CLAUDE.md），所以无 commit 步骤；用"运行 → 验证产物"代替"测试 → commit"。

**Tech Stack:** Python 3.11.9 + matplotlib（已在 venv）、Microsoft YaHei 中文字体、Markdown 写作。

---

## 文件清单

| 类型 | 路径 | 职责 |
|------|------|------|
| 新建 | `scripts/gen_cover_env_07.py` | 封面生成（沿用 env_06 风格，主题改为"排除因果"） |
| 新建 | `scripts/gen_fig_chain_comparison.py` | 链状对比图（C8 链 vs 武汉链） |
| 新建 | `articles/env/07_工厂污染能否致病：科学能排除因果吗.md` | 正文 |
| 新建 | `articles/env/cover_env_07.png` | 封面（脚本产物） |
| 新建 | `articles/env/fig_env_07_chain.png` | 链状对比图（脚本产物） |
| 修改 | `plan.md` | env 第 7 篇状态登记 |
| 修改 | `CLAUDE.md` | 命令列表加 env_07 两条 |

---

### Task 1: 写封面生成脚本

**Files:**
- Create: `scripts/gen_cover_env_07.py`

- [ ] **Step 1: 创建脚本文件，写出完整代码**

参考 `scripts/gen_cover_env_06.py` 的结构（已经读过，900×383、dpi=100、no bbox_inches='tight'、Microsoft YaHei 字体、点状背景、6 链暗示），但视觉中心改为「问号变 X / 链条中断」以呼应"断链"主题：

```python
"""
Cover for article 07: 「工厂污染能否致病」——科学能排除因果吗
900x383px, dpi=100, no bbox_inches='tight'.

Theme: The 6-link forensic chain — same framework as env_06, but this time
the question mark is replaced by an X over the broken links. Sister piece
to the DuPont C-8 article (env_06).
"""
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.family'] = 'Microsoft YaHei'
plt.rcParams['axes.unicode_minus'] = False

np.random.seed(7)
fig, ax = plt.subplots(figsize=(9, 3.83))
fig.patch.set_facecolor('#f5f7fa')
ax.set_xlim(0, 9)
ax.set_ylim(0, 3.83)
ax.axis('off')

# ── Subtle dot background ──
for _ in range(200):
    x = np.random.uniform(0.2, 8.8)
    y = np.random.uniform(0.2, 3.6)
    ax.scatter(x, y, s=0.8, color='#4a525e',
               alpha=np.random.uniform(0.08, 0.25), linewidths=0, zorder=1)

# ── Factory silhouette (left) ──
factory_x = np.array([0.6, 0.6, 1.2, 1.2, 1.8, 1.8, 1.0, 0.6])
factory_y = np.array([0.8, 0.2, 0.2, 0.5, 0.5, 0.2, 0.2, 0.8])
ax.fill(factory_x, factory_y, color='#3b4049', alpha=0.7, zorder=2)
ax.fill([0.55, 1.85, 1.2], [0.85, 0.85, 1.1], color='#4a525e', alpha=0.6, zorder=2)
ax.plot([1.45, 1.45], [0.85, 1.5], color='#4a525e', lw=4, alpha=0.7, zorder=2)
ax.plot([1.55, 1.55], [0.85, 1.5], color='#4a525e', lw=4, alpha=0.7, zorder=2)
ax.fill([0.9, 1.05, 1.05, 0.9], [0.55, 0.55, 0.7, 0.7],
        color='#f59e0b', alpha=0.3, zorder=3)
# Smoke (darker, hinting at illegal emissions)
for sx, sy, ss in [(1.5, 1.65, 0.08), (1.55, 1.78, 0.06),
                   (1.48, 1.90, 0.04), (1.52, 2.00, 0.03)]:
    ax.add_patch(plt.Circle((sx, sy), ss, color='#1f2937', alpha=0.3, zorder=2))

# ── Human figure (right) ──
ax.fill([6.8, 6.8, 7.0, 7.2, 7.2], [0.5, 0.2, 0.2, 0.2, 0.5],
        color='#60a5fa', alpha=0.5, zorder=2)
ax.add_patch(plt.Circle((7.0, 0.7), 0.18, color='#60a5fa', alpha=0.5, zorder=2))
ax.plot([7.2, 7.6], [0.45, 0.55], color='#60a5fa', lw=2.5, alpha=0.4, zorder=2)

# ── The 6-link chain — links 4 and 5 are X'd (broken) ──
chain_x = np.linspace(2.2, 6.4, 6)
chain_y = 1.2 + 0.35 * np.sin(np.linspace(0, 2 * np.pi, 6))
link_labels = ['源', '途径', '受体', '暴露', '效应', '判定']
# 1-3 = strong (green shades), 4-5 = broken (red/orange), 6 = verdict
link_colors = ['#22c55e', '#22c55e', '#22c55e', '#ef4444', '#ef4444', '#f97316']

for i, (cx, cy) in enumerate(zip(chain_x, chain_y)):
    color = link_colors[i]
    ax.add_patch(plt.Circle((cx, cy), 0.16, color=color, alpha=0.4, zorder=3))
    ax.add_patch(plt.Circle((cx, cy), 0.07, color=color, alpha=0.7, zorder=4))
    ax.text(cx, cy - 0.3, link_labels[i], fontsize=4.5, color=color,
            ha='center', alpha=0.7, fontweight='bold')
    # Big X over broken links (positions 3 and 4 → labels 暴露 and 效应)
    if i in (3, 4):
        ax.plot([cx - 0.18, cx + 0.18], [cy + 0.18, cy - 0.18],
                color='#dc2626', lw=2.5, alpha=0.85, zorder=5)
        ax.plot([cx - 0.18, cx + 0.18], [cy - 0.18, cy + 0.18],
                color='#dc2626', lw=2.5, alpha=0.85, zorder=5)

# Links between dots — dashed for broken segments
for i in range(len(chain_x) - 1):
    if i >= 2:  # links 3-4 and 4-5 are dashed/red
        ax.plot(chain_x[i:i + 2], chain_y[i:i + 2],
                color='#dc2626', lw=0.8, alpha=0.45,
                linestyle='--', zorder=2)
    else:
        ax.plot(chain_x[i:i + 2], chain_y[i:i + 2],
                color='#6b7280', lw=0.8, alpha=0.4, zorder=2)

# Dotted lines to factory / from verdict to human (faded — chain didn't reach)
ax.plot([1.8, chain_x[0] - 0.1], [0.8, chain_y[0]],
        color='#22c55e', lw=1.0, alpha=0.4, linestyle=':', zorder=2)
ax.plot([chain_x[-1] + 0.1, 6.8], [chain_y[-1], 0.6],
        color='#f97316', lw=1.0, alpha=0.25, linestyle=':', zorder=2)

# ── Title (replaces the question mark of env_06) ──
ax.text(4.5, 3.30, '「工厂污染能否致病」', fontsize=13,
        color='#1f2328', ha='center', fontweight='bold', zorder=5)
ax.text(4.5, 2.85, '—— 科学能排除因果吗', fontsize=11,
        color='#3b4049', ha='center', fontweight='bold', zorder=5)
ax.text(4.5, 2.20, '同一套方法 · 反向结论 · C8 姊妹篇', fontsize=5.5,
        color='#6b7280', ha='center', alpha=0.75, fontweight='bold', zorder=5)

# ── Bottom tag ──
ax.text(4.5, 0.18, '武汉新洲  ·  6/12 调查通报  ·  链断在「暴露→效应」',
        fontsize=5.5, color='#9ca3af', ha='center', alpha=0.7,
        fontweight='bold', zorder=5)
ax.plot([1.0, 8.0], [0.30, 0.30], color='#d0d7de', lw=0.5, zorder=2)

# ── Save ──
import os
out = os.path.join(os.path.dirname(__file__), '..', 'articles', 'env',
                   'cover_env_07.png')
plt.savefig(out, dpi=100, facecolor='#f5f7fa')
print(f'Saved -> {out}')
```

- [ ] **Step 2: 文件保存到正确路径**

完整代码已贴在 Step 1。直接落盘到 `scripts/gen_cover_env_07.py`。

---

### Task 2: 运行封面脚本，验证产物

**Files:**
- Reads: `scripts/gen_cover_env_07.py`
- Creates: `articles/env/cover_env_07.png`

- [ ] **Step 1: 在项目根目录运行脚本**

```bash
.venv/Scripts/python.exe scripts/gen_cover_env_07.py
```

预期输出：
```
Saved -> D:\Workspace\ml-learning\articles\env\cover_env_07.png
```

- [ ] **Step 2: 验证文件生成**

```bash
ls -la "articles/env/cover_env_07.png"
```

预期：文件存在，大小在 30-80KB 范围内（与 env_06 cover 同量级），无报错。

- [ ] **Step 3: 视觉抽查（可选）**

用图片查看器打开 `articles/env/cover_env_07.png`，确认：
- 6 个链节清晰可辨，2-4 节（暴露、效应）上有红色 X
- 标题「工厂污染能否致病」+「—— 科学能排除因果吗」居中可见
- 工厂-链-人 三个元素在画面上呈现从左到右的路径
- 底部署名行可见

---

### Task 3: 写链状对比图脚本

**Files:**
- Create: `scripts/gen_fig_chain_comparison.py`

- [ ] **Step 1: 创建脚本文件**

```python
"""
Figure for article 07: C-8 chain vs Wuhan chain (same framework, two directions).

Output: articles/env/fig_env_07_chain.png
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.join(os.path.dirname(__file__), '..', 'articles', 'env',
                   'fig_env_07_chain.png')

# ── Layout ──
fig, ax = plt.subplots(figsize=(11, 4.6))
fig.patch.set_facecolor('white')

# Header bar
ax.add_patch(mpatches.Rectangle((0, 4.0), 11, 0.6, facecolor='#1f2937',
                                edgecolor='none', zorder=1))
ax.text(5.5, 4.30, '同一套 6 环节框架，两个方向',
        fontsize=13, color='white', ha='center', va='center',
        fontweight='bold', zorder=2)

# Common link labels
labels = ['源', '途径', '受体', '暴露', '效应', '判定']
n = len(labels)
x_positions = np.linspace(0.7, 10.3, n)
y_c8 = 2.6
y_wuhan = 1.0
box_w, box_h = 1.4, 0.55


def draw_link(ax, x, y, label, color, broken=False, broken_reason=None):
    """Draw one link box + optional X over it."""
    face = color if not broken else '#fee2e2'
    edge = color if not broken else '#dc2626'
    ax.add_patch(mpatches.FancyBboxPatch(
        (x - box_w / 2, y - box_h / 2), box_w, box_h,
        boxstyle='round,pad=0.02', facecolor=face, edgecolor=edge,
        linewidth=1.6, zorder=2))
    ax.text(x, y, label, fontsize=11, color=('#1f2937' if not broken else '#7f1d1d'),
            ha='center', va='center', fontweight='bold', zorder=3)
    if broken:
        ax.plot([x - box_w / 2 + 0.05, x + box_w / 2 - 0.05],
                [y - box_h / 2 + 0.05, y + box_h / 2 - 0.05],
                color='#dc2626', lw=2.0, alpha=0.85, zorder=4)
        ax.plot([x - box_w / 2 + 0.05, x + box_w / 2 - 0.05],
                [y + box_h / 2 - 0.05, y - box_h / 2 + 0.05],
                color='#dc2626', lw=2.0, alpha=0.85, zorder=4)
    if broken_reason:
        ax.text(x, y - 0.45, broken_reason, fontsize=7.5,
                color='#7f1d1d', ha='center', va='top', zorder=3,
                fontweight='bold')


def draw_arrows(ax, y, x_positions, color, broken_from=None):
    """Draw arrows between boxes; red-dashed after broken_from."""
    for i in range(len(x_positions) - 1):
        x1 = x_positions[i] + box_w / 2
        x2 = x_positions[i + 1] - box_w / 2
        c = color if broken_from is None or i < broken_from else '#dc2626'
        ls = '-' if broken_from is None or i < broken_from else '--'
        ax.annotate('', xy=(x2, y), xytext=(x1, y),
                    arrowprops=dict(arrowstyle='->', color=c,
                                    lw=1.4, linestyle=ls, alpha=0.7),
                    zorder=2)


# ── C-8 chain (all green) ──
ax.text(0.2, y_c8, '杜邦 C-8：', fontsize=12, color='#15803d',
        ha='left', va='center', fontweight='bold', zorder=3)
for i, (x, lab) in enumerate(zip(x_positions, labels)):
    draw_link(ax, x, y_c8, lab, '#bbf7d0', broken=False)
draw_arrows(ax, y_c8, x_positions, '#15803d')
# Verdict
verdict_x = x_positions[-1] + 1.3
ax.annotate('', xy=(verdict_x, y_c8), xytext=(x_positions[-1] + box_w / 2, y_c8),
            arrowprops=dict(arrowstyle='->', color='#15803d', lw=1.6, alpha=0.8),
            zorder=2)
ax.add_patch(mpatches.FancyBboxPatch(
    (verdict_x - 0.5, y_c8 - 0.32), 1.6, 0.64,
    boxstyle='round,pad=0.02', facecolor='#15803d',
    edgecolor='#15803d', linewidth=1.4, zorder=2))
ax.text(verdict_x + 0.3, y_c8, '可能关联', fontsize=11, color='white',
        ha='center', va='center', fontweight='bold', zorder=3)

# ── Wuhan chain (broken at links 3 and 4) ──
ax.text(0.2, y_wuhan, '武汉案：', fontsize=12, color='#b91c1c',
        ha='left', va='center', fontweight='bold', zorder=3)
broken_reasons = {
    3: '环境本底基本达标',
    4: '标化率 < 武汉 < 全国',
}
for i, (x, lab) in enumerate(zip(x_positions, labels)):
    is_broken = i in broken_reasons
    draw_link(ax, x, y_wuhan, lab, '#bbf7d0' if not is_broken else '#fecaca',
              broken=is_broken,
              broken_reason=broken_reasons.get(i))
draw_arrows(ax, y_wuhan, x_positions, '#15803d', broken_from=2)
# Verdict
ax.annotate('', xy=(verdict_x, y_wuhan), xytext=(x_positions[-1] + box_w / 2, y_wuhan),
            arrowprops=dict(arrowstyle='->', color='#15803d', lw=1.6, alpha=0.8),
            zorder=2)
ax.add_patch(mpatches.FancyBboxPatch(
    (verdict_x - 0.5, y_wuhan - 0.32), 1.6, 0.64,
    boxstyle='round,pad=0.02', facecolor='#b91c1c',
    edgecolor='#b91c1c', linewidth=1.4, zorder=2))
ax.text(verdict_x + 0.3, y_wuhan, '无因果', fontsize=11, color='white',
        ha='center', va='center', fontweight='bold', zorder=3)

# ── Divider ──
ax.plot([0.2, 10.8], [1.85, 1.85], color='#d0d7de', lw=0.5, zorder=1)
ax.text(5.5, 1.85, '同一方法 · 不同证据 · 不同方向', fontsize=8.5,
        color='#6b7280', ha='center', va='center',
        bbox=dict(boxstyle='round,pad=0.25', facecolor='white',
                  edgecolor='#d0d7de', lw=0.5), zorder=3)

# ── Axis off / limits ──
ax.set_xlim(0, 11)
ax.set_ylim(0.4, 4.7)
ax.axis('off')

plt.tight_layout()
plt.savefig(OUT, dpi=120, bbox_inches='tight', facecolor='white')
print(f'Saved -> {OUT}')
```

- [ ] **Step 2: 文件保存到正确路径**

完整代码已贴在 Step 1。直接落盘到 `scripts/gen_fig_chain_comparison.py`。

---

### Task 4: 运行链状对比图脚本，验证产物

**Files:**
- Reads: `scripts/gen_fig_chain_comparison.py`
- Creates: `articles/env/fig_env_07_chain.png`

- [ ] **Step 1: 运行脚本**

```bash
.venv/Scripts/python.exe scripts/gen_fig_chain_comparison.py
```

预期输出：
```
Saved -> D:\Workspace\ml-learning\articles\env\fig_env_07_chain.png
```

- [ ] **Step 2: 验证文件**

```bash
ls -la "articles/env/fig_env_07_chain.png"
```

预期：文件存在，大小在 30-80KB 范围内。

- [ ] **Step 3: 视觉抽查**

打开 PNG，确认：
- 上下两条 6 节链条并排
- 杜邦链全绿、武汉链在 4-5 节（暴露、效应）有红色 X
- 两条链末端都有 verdict 框（"可能关联"绿、"无因果"红）
- 断裂原因小字在 X 下方可见

---

### Task 5: 写正文 markdown

**Files:**
- Create: `articles/env/07_工厂污染能否致病：科学能排除因果吗.md`

- [ ] **Step 1: 创建正文文件**

按 spec 6 节大纲落笔（引言 + 一 + 二 + 三 + 四 + 五），参考 env_06 的写作风格（叙事驱动、引用具体数字、避免矩阵、避免「——」破折号、章节开头用「> **【截图 N】**」标记插图位置、末尾有「*生成图: ...*」指向 PNG）。

```markdown
# 「工厂污染能否致病」——科学能排除因果吗

> **【引言】**
>
> 上篇文章留下了一个悬念：武汉新洲黄土坡村 585 人、累计 65 例癌症、一家 1986 年投产至今没拿到排污许可证的泡花碱厂，科学能不能给这件事一个结论？
>
> 2026 年 5 月 18 日媒体曝光后，武汉于次日组建了 220 余名环境监测、35 人流行病学、360 余工作人员参与的联合调查组。6 月 12 日，通报发布：村民患癌与企业排污不存在关联，企业违法事实清楚、已被彻底关停，多名公职人员被问责。
>
> 这次文章不评价调查做对了什么或做错了什么。我们只看一件事：科学是怎么把链条走断的。同一套「源 → 途径 → 受体 → 暴露评估 → 健康效应 → 因果判定」六环节框架，上次讲杜邦案时它在每一环都站住了；这次在武汉案上，它在中间两环走不下去。这就是答案。

> **【图 1】** 同一套 6 环节框架，两个方向
> 上：杜邦 C-8 案（杜邦是合法排污 + 内部掩盖）。6 节全绿，末端标"可能关联"。
> 下：武汉新洲案（违法排污 + 明目张胆）。前 3 节绿，第 4-5 节标红 X，末端标"无因果"。
> 红色 X 的下方小字分别是「环境本底基本达标」「标化率 < 武汉 < 全国」。
> *生成图: articles/env/fig_env_07_chain.png*

---

## 一、链的两端：源很清楚，受体很清楚

为什么这次调查能下结论？两个前提条件缺一不可：源端的违法事实必须扎实，受体端的病例数据必须扎实。

源端在通报里写得很清楚。这家 1986 年投产的泡花碱厂，四十年来没有排污许可证，逾期拒不整改，被责令停产后偷偷生产。2014 到 2015 年在没办建设审批手续的情况下违法搭建了约 800 平方米的厂棚。2019 到 2023 年还存在非法倾倒、填埋工业固体废物的行为，2017 年就因固废违法处置被罚过 20 万元。

受体端也扎实。1986 年至今 40 年里，户籍人口 585 人的村庄累计确诊癌症及白血病病例 65 例。调查组对村民做了全覆盖健康流调。

把这两端单独拎出来看，信号都不弱。源端甚至比杜邦案更"亮"：杜邦的排放当年是合法排污，靠的是内部文件掩盖；本案是公开违法，连排污许可证都没有。如果只看这两端，按"工厂脏、村民病"的直觉，结论应该很自然。

问题不出在两端。问题出在中间。

---

## 二、链断在"暴露评估"

上篇文章讲杜邦案时，重点是科学委员会怎么用五个模型（AERMOD 模拟大气扩散、PRZM-3 模拟土壤入渗、MODFLOW 模拟地下水输移、BreZo 模拟河流取水、药代模型模拟体内蓄积）串联起来，重建了每位居民过去 50 年的摄入剂量。这是 C-8 案能站住的关键一环。

武汉案的调查组没有、也不需要做这种个体剂量重建。原因是受体端的信号不够强去倒推源。

他们改走一条更直接的路线：把环境本底测一遍，看污染物有没有"穿透"到居民能接触到的介质。结果是：

- 厂区周边地下水指标符合国家标准
- 所有农用地土壤指标 100% 达标
- 仅厂区南侧雨水沟水体碱性超标、邻近水塘化学需氧量超标
- 针对网传"厂区物料含放射性物质、诱发白血病"的说法，检测证实相关物质放射性为当地天然本底水平，未发现人工放射性核素

地下水、土壤这两个居民最直接接触的介质都达标了。这是一个关键判断：排放基本没"穿透"到村民的暴露路径上。这是链条的第一道裂口。

---

## 三、链断在"健康效应"

第二道裂口更关键。

65 例 / 40 年 / 585 人。粗看这个数字确实吓人。

但是做流行病学的人都知道，看绝对数字没有意义，必须标准化以后再比。调查组给出的统计结果是：年龄标准化后，这个地方的癌症年均发病率**低于武汉市平均水平**，也**低于全国平均水平**，不属于癌症高发区域。

怎么判断"这么多病例是不是和工厂有关"？至少有三条独立的证据线：

**时间分布**。2015 年后病例增多，乍看像是近年污染加剧的证据。但同期全国癌症发病率都在上升，这是人口老龄化、检出率提高、医疗诊断能力进步共同作用的结果，不是哪家工厂能解释的单一现象。

**空间分布**。病例不集中在厂区下风向或下游的居民组里。如果真是污染致病，应该能看到离厂越近、风险越高的梯度；这种梯度在这份流调里看不到。

**类型分布**。环境因素致癌通常会留下"瘤谱指纹"：某种或某几种癌症显著高发。本案没有看到与特定环境暴露相关的瘤谱特征。

这就是上篇文章讲过的"剂量-反应关系"反过来用。C-8 案是暴露越高、风险越高的清晰阶梯；本案找不到这个阶梯，统计上不存在关联。

---

## 四、违法 ≠ 致病

通报里同时下了两个结论：

- **法律结论**：企业违法（无证、偷排、违建、非法倾倒），责令关停、限期拆除违法建筑、追究刑事责任，多名公职人员被问责。
- **科学结论**：村民患癌与企业排污无因果关系。

一个事件，可以同时成立两个事实。工厂脏，是真的；工厂的脏没传导到村民的健康上，也是真的。

这才是这个案例最反直觉、也最有科普价值的一点。我们日常的语言习惯里，"污染"和"致病"是绑定的。一家工厂违法排污，周边村民又集中患癌，"工厂导致癌症"听起来几乎是显然的推断。但这个推断跨越了两个完全不同的判断：

- **环境法意义上的"违法"**：看企业有没有取得许可、有没有按证排污、有没有处置固废。判的是行为对不对。
- **健康学意义上的"致病"**：看污染物有没有进入人体、剂量够不够大、有没有引发可识别的疾病模式。判的是生物学上的因果链。

杜邦案是"源洁（合法排污）但链通"——所有环节都符合科学意义上的因果判定；武汉案是"源脏（违法排污）但链断"——源端够脏，链却在中间断了。

再次说明，环境法的"违法"和健康学的"致病"是两套独立的判断。

---

## 五、结语：工具是中性的

回到文章开头的那个问题：科学能不能排除因果？

答案是能。武汉案给我们看了一个完整的样本：源端事实清楚，受体端数据扎实，中间两环走不下去，结论站得住。这套结论的可信度，不是来自对工厂的同情，也不是来自对调查组的信任，而是来自"任何一方都可以重做这套核查"的开放性。

把"无因果"说成"工厂清白"是把科学简化了。把"无因果"说成"调查有黑幕"也是把科学简化了。

科学只能说到证据能支撑的程度。这是上篇文章留下的遗产，这次只是把它从"建链"那一面翻到了"断链"这一面。

---

## 参考文献

[1] 武汉市联合调查组，《关于新洲区昌盛泡花碱厂相关问题的调查通报》，2026 年 6 月 12 日。

[2] 杜邦C8污染案：科学如何论证工厂与健康的因果链，本系列第 6 篇。
```

- [ ] **Step 2: 验证文件结构**

```bash
wc -l "articles/env/07_工厂污染能否致病：科学能排除因果吗.md"
```

预期：约 80-110 行。

- [ ] **Step 3: 自查清单**

打开文件，确认：
- 标题在第一行（`# 「工厂污染能否致病」——科学能排除因果吗`）
- 引言 + 5 节正文（## 一、二、三、四、五）+ 参考文献
- 引用了 1 张图（fig_env_07_chain.png）
- 提到封面 PNG 在 CLAUDE.md 命令列表里登记（这一步在 Task 7）
- 字数 ≈ 2400（中文按字符计）
- 全文未出现「——」破折号（用逗号/句号/冒号替代）
- 第 4 节明确写出"违法 ≠ 致病"是核心反直觉点

---

### Task 6: 更新 plan.md

**Files:**
- Modify: `plan.md`

- [ ] **Step 1: 找到 env 表格位置**

在 `plan.md` 第 53-62 行附近（env 系列表），第 6 行下面插入第 7 行。

- [ ] **Step 2: 在表格里插入第 7 行**

把现有：

```markdown
| ✅ 06 | 杜邦 C-8 污染案：科学如何论证工厂与健康的因果链 | 以杜邦PFOA污染案为样本，拆解"源→途径→受体→健康效应→因果判定"的环境法医学论证链条 | ✅ **已发** |
| ⚡ | 07 电镀厂酸雾：从工艺产污到大气扩散与沉降 | 模型已跑通（`models/electroplating_acid_mist.py`），5 图。核心发现：单级洗涤塔下铬酸雾排放超标 4.6 倍；酸化贡献远小于酸雨。 | 📝 草稿 |
| ⚡ | 08 电镀厂铬（Cr(VI)）：大气沉降与健康风险 | 模型已跑通（`models/electroplating_cr.py`），5 图 + 文。核心发现：达标排放下 200m 处吸入癌风险约 3.1×10⁻⁶（Very Low），吸入主导但绝对风险可接受。 | 📝 草稿 |
```

中的 07 行替换为本案的实际行：

| 07 | 工厂污染能否致病：科学能排除因果吗 | 武汉新洲泡花碱厂调查通报为素材，C8 案的姊妹篇：用同一套 6 环节框架反向拆解"科学如何否定因果"，讲违法事实扎实但暴露-效应两环断裂的论证结构 | ✅ **已发** |

⚠️ 注意：原 plan.md 里"07 电镀厂酸雾"已经是草稿状态。在 C8 姊妹篇插入之后，电镀酸雾变成 08、电镀铬变成 09——但**这次只插入 07 一行，不重排原有编号**。理由是电镀两篇是模型线（带代码），C8 姊妹篇是纯科普线（无代码），属于不同子线，编号可以不严格连续。

- [ ] **Step 3: 同步更新第 53 行附近的"环境工程线"小标题说明**

把 `### 环境工程线 (`articles/env/`)` 段下方的简介行（如有）补一句姊妹篇说明。如果该段没有简介句，跳过此步。

---

### Task 7: 更新 CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: 找到 `gen_cover_env_0N.py` 命令块**

在 `CLAUDE.md` 的 `### Environmental Model → Article` 小节里，找到 `python scripts/gen_cover_env_0N.py` 这一行附近（应该有"environmental articles → articles/env/"的注释）。

- [ ] **Step 2: 在合适位置补两行**

在环境 cover/fig 命令列表下补：

```bash
python scripts/gen_cover_env_07.py        # 链断点封面（C8 姊妹篇） → articles/env/cover_env_07.png
python scripts/gen_fig_chain_comparison.py # 同一套框架两个方向对比图 → articles/env/fig_env_07_chain.png
```

具体插入位置以现有 `gen_cover_env_06.py` 行后为佳，保持 06 → 07 的相邻顺序。

- [ ] **Step 3: 验证 CLAUDE.md 没有破坏既有结构**

```bash
grep -c "^### " CLAUDE.md
```

预期：与修改前数量一致（如果原来是 12 个 `### `，现在还是 12 个）。

---

## 自审检查表

| 检查项 | 状态 |
|--------|------|
| 占位符（TBD/TODO/待定/类似 X 步骤） | ✅ 无 |
| 文件路径精确 | ✅ 全是 `scripts/...` / `articles/env/...` / `plan.md` / `CLAUDE.md` |
| 完整代码 | ✅ 封面脚本 + 链状对比图脚本都给了完整代码 |
| 验证步骤具体 | ✅ `ls -la`、`wc -l` 命令 + 预期输出 |
| YAGNI | ✅ 没有给文章加多余功能（无 RAG、无交互、无部署） |
| 与 spec 一致 | ✅ 标题/字数分配/图/语气/边界全部对齐 |
| 项目无 git 仓库 | ✅ 计划中无 commit 步骤（per CLAUDE.md "Is a git repository: false"） |
| 项目无测试 | ✅ 计划中无 pytest 步骤（per CLAUDE.md "No test suite"） |
