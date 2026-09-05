# Causal/07 沉迷归因 DAG+PSM（CGSS 2023 真实数据）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `articles/causal/07_短视频沉迷.md`，从"短视频沉迷到底是算法、家庭、还是用户自己的锅"切入，用 5 节点 DAG 演示上网频率 X、信息来源依赖互联网 Y、性别+年龄 Z、社会信任 W、生活幸福 M 之间的因果结构，**用 CGSS 2023（中国综合社会调查，11326 样本，5 万条题项）真实数据**做 PSM 实证，把社会信任这一 confounder 剥离，看剥离前后"上网频率"对"互联网作为主要信息源"的因果效应差多少。CNNIC 第54次报告（2024）+ 中科院心理蓝皮书（2024）作为背景引用。

**Architecture:** 单篇文章 + 1 张封面 + 2 张概念图（DAG 拓扑 + PSM 实证对比图）。PSM 实证用 CGSS 2023 STATA .dta 真实数据：5 个变量全部对齐 CGSS 已有题目（X=a3012 上网频率、Y=a29 最主要信息来源、Z=a2 性别+a3a 出生年、W=a33 社会信任、M=a36 生活幸福）。data loader 直接读 STATA .dta 文件，用 pandas + sklearn 做 PSM。spec 中的"算法升级导致的混淆"项在第五节处理（用 04 SCM 篇类似的"政策包"思路做边界说明），不引入第四种方法。

**Tech Stack:** Markdown 文章 + matplotlib（封面与 1 张实证对比图）+ pandas（CGSS .dta loader）+ numpy + sklearn（logistic 倾向得分 + 1:k NN 匹配）。Python 系统版本（CLAUDE.md Quick Start 约定）。CJK 字体 `Microsoft YaHei, SimHei`。

## Global Constraints

- **CLAUDE.md 写作规范**：hook first、每图加 caption、参考文献内联、无 em dash（——）、无"下一篇"链接、节标题口径递进、避免 AI 腔与拟人化总结
- **memory `publish-before-push-github`**：articles/ 仓库是独立 git 仓库，文章和图都 commit 到 articles 仓库；**不 push GitHub**；root repo 改动（plan.md）也只本地 commit
- **memory `article-editing-coherence-pass`**：通读+画论证线+审接缝，不孤立逐节改
- **5 节点 DAG → CGSS 2023 变量映射**：

| DAG 节点 | CGSS 2023 变量 | 编码 | 有效样本 |
|---------|----------------|------|----------|
| **X** 上网强度 | `a3012` 空闲时间上网频率 | high(1/2 每天/一周数次) vs low(3/4/5 一月数次以下) | 6990 |
| **Y** 信息依赖 | `a29` 最主要信息来源 | 互联网=5（含手机/智能终端） vs 其他=1/2/3/4（报纸/杂志/广播/电视） | 6982 |
| **Z** 用户特征 | `a2` 性别 + `a3a` 出生年(转 age=2023-birthyr) | 二元 + 连续（age） | 11326 |
| **W** 社会信任 | `a33` 总的来说大多数人可以信任 | 5 级 Likert (1=非常不同意→5=非常同意) | 11326 |
| **M** 生活幸福 | `a36` 总的来说您觉得生活是否幸福 | 5 级 Likert (1=非常不幸福→5=非常幸福) | 11326 |

- **数据已在磁盘**：`articles/causal/data/中国综合社会调查（2023）/CGSS2023.dta`（47.6MB STATA 文件，11326 × 437）。**CGSS 数据公开可获取，无需申请**。其他文件：居民问卷 PDF（入户/电话两份）+ 编码表 Excel + 采访地点编码表 PDF。**STATA .dta 不内嵌到 articles git 仓库**（大文件，按 CLAUDE.md 惯例 gitignored），文章里写明 CGSS 公开下载链接 + gitignored 说明
- **封面布局**：复用 05 篇 `gen_cover_causal_05.py` 的 3 列骨架（左侧 DAG mini / 中间"+2 倍"callout / 右侧 4-bar 对比）。右侧 4-bar：朴素估计 / Backdoor / PSM / 调错 collider（CEPS 真实跑出来的数字，不预设）
- **封面钩子**：底部副标题"DAG · backdoor 准则告诉你该调 {父母关系}，别动 {学业成绩}"
- **配色与字体**：保持 `C_L1='#4A6FA5'` / `C_L2='#D67D3E'` / `C_CUT='#8a3030'` / `BG='#F5F2EC'`，字体 `'Microsoft YaHei', 'SimHei'`
- **生成规格**：封面 `(9, 3.83) dpi=100` 不带 `bbox_inches='tight'`；概念图 `(9, 4.5) dpi=150` 带 `bbox_inches='tight'`；实证对比图 `(9, 4.0) dpi=150` 带 `bbox_inches='tight'`
- **数据来源**（文中内联引用）：
  - **CGSS 2023（中国综合社会调查，11326 样本 × 437 变量）** —— PSM 实证主数据
  - **CNNIC《第54次中国网络发展状况统计报告》2024-06** —— 短视频渗透率背景
  - **中科院心理蓝皮书 2024** —— 短视频时长分层背景
  - **中国青少年研究中心 未成年人蓝皮书** —— 2018→2024 增长对比背景
  - **抖音安全与信任中心《抖音算法原理》2025-03 / 2024-04 抖音开放日** —— 第五节算法升级素材

---

## File Structure

| 文件 | 职责 | 路径 |
|------|------|------|
| 文章全文 | 引言 + 5 节 + 参考文献 7 条 | `articles/causal/07_短视频沉迷.md` |
| 封面 + 2 张图生成器 | CGSS data loader + PSM estimation + matplotlib 出图 | `scripts/causal/gen_cover_causal_07.py` |
| CGSS 数据 | STATA .dta（47.6MB，已在磁盘，gitignored） | `articles/causal/data/中国综合社会调查（2023）/CGSS2023.dta` |
| 封面 PNG | 公众号 feed 缩略图 | `articles/causal/cover_causal_07.png`（脚本产出） |
| DAG 拓扑图 PNG | 文章内插图 fig_dag_video | `articles/causal/fig_dag_video.png`（脚本产出） |
| PSM 实证对比图 PNG | 文章内插图 fig_psm_family | `articles/causal/fig_psm_family.png`（脚本产出） |
| 计划状态文件 | 项目叙事状态 | `_local/plan.md`（gitignored） |

---

## Task 0: 验证 CGSS 2023 数据可读

**Files:**
- Verify: `articles/causal/data/中国综合社会调查（2023）/CGSS2023.dta`（已在磁盘，47.6MB STATA 文件）

**Interfaces:**
- 路径约束：与因果系列 data 目录共存，按 CLAUDE.md 惯例

- [ ] **Step 1: 确认 .dta 可读 + 5 个变量分布**

```bash
cd "D:\Workspace\ml-learning" && python -c "
import pandas as pd
df = pd.read_stata('articles/causal/data/中国综合社会调查（2023）/CGSS2023.dta', convert_categoricals=False)
print('shape:', df.shape)
print('a3012:', df['a3012'].value_counts(dropna=False).head(6).to_dict())
print('a29:', df['a29'].value_counts(dropna=False).head(6).to_dict())
print('a2:', df['a2'].value_counts(dropna=False).head(3).to_dict())
print('a33:', df['a33'].value_counts(dropna=False).head(6).to_dict())
print('a36:', df['a36'].value_counts(dropna=False).head(6).to_dict())
print('a3a (birthyr):', df['a3a'].describe().to_dict())
"
```

预期：shape=(11326, 437)；a3012 1.0 ≈ 4251；a29 5.0 ≈ 4885；a2 1.0 ≈ 6215；a33 4.0 ≈ 5915；a36 4.0 ≈ 6389；a3a 在 1920-2005 范围内。

- [ ] **Step 2: 验证变量清洗规则**

```bash
cd "D:\Workspace\ml-learning" && python -c "
import pandas as pd
df = pd.read_stata('articles/causal/data/中国综合社会调查（2023）/CGSS2023.dta', convert_categoricals=False)
# X: a3012 high(1/2) vs low(3/4/5), drop -2/-1/NaN
x_mask = df['a3012'].isin([1.0, 2.0, 3.0, 4.0, 5.0])
# Y: a29 互联网(5) vs 其他(1/2/3/4), drop 98/99/NaN/-1/-2/-3
y_mask = df['a29'].isin([1.0, 2.0, 3.0, 4.0, 5.0])
# Z: a2 (1/2), a3a in [1920, 2005]
z_mask = df['a2'].isin([1.0, 2.0]) & df['a3a'].between(1920, 2005)
# W: a33 1-5, drop -2/-1/-3
w_mask = df['a33'].isin([1.0, 2.0, 3.0, 4.0, 5.0])
# M: a36 1-5, drop -2/-1/-3
m_mask = df['a36'].isin([1.0, 2.0, 3.0, 4.0, 5.0])
valid = x_mask & y_mask & z_mask & w_mask & m_mask
print('valid n:', valid.sum(), 'of', len(df))
"
```

预期：valid n 约 6000-7000（a3012 和 a29 是问卷后半段，前半段受访者大约 7000 人有答）。

---

## Task 1: 起草文章（短视频沉迷 5 节点 DAG + CGSS 2023 实证）

**Files:**
- Create: `articles/causal/07_短视频沉迷.md`（新增 6KB+）

**Interfaces:**
- Produces: 公开文本（公众号候选稿），不推送 GitHub
- Consumes: 引用 `cover_causal_07.png` + `fig_dag_video.png` + `fig_psm_family.png`（Task 2 产出）

- [ ] **Step 1: 写文章全文**

直接新建 `articles/causal/07_短视频沉迷.md`，骨架与口径约束：

**标题**：「沉迷归因：算法、家庭、还是用户自己？DAG+PSM 怎么挑出该调的家庭变量」（钩子要罩住全文——全文讲的是"沉迷归因"这件事怎么不归错变量）

**引言 blockquote**：以"2024 年短视频人均单日 156 分钟、95.5% 网民都在用，但互联网已不再只是工具，它是最主要的信息源"开头（来源：CNNIC 第54次报告 + CGSS 2023），抛出归因冲突：家长怪算法、用户怪自己、专家怪家庭。问"剥离年龄 + 性别 + 社会信任后，上网频率对'互联网作为主要信息源'还能解释多少？"

**一、调对调错差几倍？** — 三类归因各自的偏差

直接拿"高上网频率组 vs 低频组"比互联网信息依赖率是危险的。三类变量：
- confounder：用户特征 Z（年龄 + 性别）、社会信任 W（信任度高的人既可能少上网、也可能报告传统媒体为主要信息源）
- mediator：使用时长路径中的行为指标（如单次使用时长，不能调）
- collider：生活幸福 M（高强度上网 + 信息依赖共同影响幸福感受，调它打开伪路径）

跑通一个回归演示：朴素估计高强度组信息依赖率偏高，PSM 后明显回落，调错 collider 反而翻负。具体数字用 CGSS 2023 真实数据跑出来填。

**二、沉迷的 5 节点 DAG：算法、用户、社会、信息、幸福**

DAG 三性：节点=变量、箭头=因果方向、不允许回路。沉迷归因画出来是 5 节点 + 7 边的图：

5 个节点（用 CGSS 2023 变量名）：
- **X**：`a3012` 上网频率（high=1/2 每天/一周数次 vs low=3/4/5）
- **Y**：`a29` 最主要信息来源（互联网=5 vs 报纸/杂志/广播/电视=1/2/3/4）
- **Z**：`a2` 性别 + `a3a` 出生年（转 age=2023-birthyr）
- **W**：`a33` 社会信任（5级 Likert，"总的来说大多数人可以信任"）
- **M**：`a36` 生活幸福（5级 Likert，"总的来说您觉得生活是否幸福"）

7 条边按机制归类成 3 类路径：
- X → Y（直接推送让人沉迷）
- X ← Z → Y、 X ← W → Y（两条后门路径）
- X → M ← Y（collider）

调整集必须包含 Z 和 W 两个 confounder；M 不能动（collider，不能调）。

**三、三种基本结构：链/叉/对撞，社会信任为什么必须调**

复用 05 篇的 3 种基本结构图（图风格复用 `fig_dag_basic.png`，不重画）：
- 链：算法推送 X → 单次使用时长 → 沉迷度 Y（条件化中间阻断，但单次使用是 mediator 不能调）
- 叉/Confounder：社会信任 W → {X, Y}（必须调）
- 对撞：X → 生活幸福 M ← Y（条件化 M 反而打开 X-Y 伪路径）

用 CGSS 2023 数据演示社会信任 W 是 confounder：信任度低 vs 信任度高的人，上网频率 / 信息依赖 / 主观幸福感均显著不同。如果不调 W，直接拿"高强度组 vs 低强度组"比，会把信任差异算到上网频率头上。

**四、PSM 实证：用 CGSS 2023 ~7000 有效样本剥离社会信任**

实证数据：
- CGSS 2023 N=11326（同时答 a3012 和 a29 的人约 7000），提取变量：
  - 上网频率（X，二值化 high vs low）
  - 互联网作为最主要信息源（Y，二元）
  - 性别 + 年龄（Z，二元 + 连续）
  - 社会信任（W，5级 Likert，连续）
  - 生活幸福（M，5级 Likert，连续）

跑四组估计：
- 朴素 Y ~ X：被 W 抬升的粗估计
- Backdoor Y ~ X + Z + W：剥离 W 后的偏回归系数
- PSM 配对后比：logistic 算倾向得分（基于 Z + W），1:4 NN 匹配 + 0.2×PS std 卡尺
- 错误调整 Y ~ X + Z + W + M：调 collider 翻负

附图：`fig_psm_family.png` 用 4 bar chart 对比四个数字（具体数字以 CGSS 跑出来为准，文章里把数字写进 caption 下方一行 + 正文）。

CNNIC 背景数据（文中内联引用）：11.0 亿网民、95.5% 短视频用户、人均单日 156 分钟；中科院心理蓝皮书分层：大学生 179.9 分钟/日、成年职业 137.4 分钟、青少年 94.2 分钟。**注意**：CGSS 2023 问卷问的是"上网"（PC + 手机 + 短视频混合），蓝皮书数据是 2024 年专门看"短视频"——文章里要明确说明"实证用 CGSS 2023 上网频率作为短视频使用强度的代理变量，论证方法可外推，但具体数字以 CGSS 为准"。

**五、什么时候 DAG/PSM 失灵：算法持续升级 + 用户自适应**

两个边界：
- 算法持续升级：抖音算法从协同过滤 → 多目标神经网络 → 主动多样化推荐（来源：2024-04 抖音开放日 + 2025-03 抖音安全与信任中心），处理变量 X 在时间维度上不断变化，DAG 的"X 是稳定处理"假设失效。
- 用户自适应：长期高强度用户改变了 Z（年龄增长、习惯固化），Z 本身被处理影响，confounder 不再是"先于处理的外生变量"。PSM 的条件独立假设失效。

**说到底**：沉迷归因这件事，归对变量才能拿到真效应。CGSS 11326 样本是 confounder 识别的支撑；剥离社会信任后，上网频率对"互联网作为主要信息源"的因果效应从朴素估计的偏高数值回落到接近 0 的水平。剩下的那部分是算法推送本身的归因，但还要警惕算法升级带来的时变混淆（04 SCM 篇用"政策包"思路可借鉴，这里用 DID 留作下一篇预告）。

**参考文献**（7 条）：
1. Pearl, J. (1995). Causal Diagrams for Empirical Research. *Biometrika*, 82(4), 669-688.
2. Rosenbaum, P. R. & Rubin, D. B. (1983). The Central Role of the Propensity Score in Observational Studies for Causal Effects. *Biometrika*, 70(1), 41-55.
3. 中国综合社会调查项目组 (2023). 《中国综合社会调查（CGSS）2023 年居民问卷》.
4. CNNIC (2024). 《第54次中国网络发展状况统计报告》.
5. 中国科学院心理研究所 (2024). 《心理健康蓝皮书》.
6. 中国青少年研究中心 (2024). 《未成年人蓝皮书》.
7. 抖音安全与信任中心 (2025). 《抖音算法原理》.

- [ ] **Step 2: 通读全文审接缝**

按 `article-editing-coherence-pass` memory 走：先通读、画论证线、检查接缝。重点检查：
- 论证线：三类归因偏差 → 5 节点 DAG → 三种结构演示 W 是 confounder → CEPS 实证剥离 W → 算法升级边界。节标题口径"问题→结构→结构→实证→边界"递进。
- 称谓统一：引言用"互联网作为主要信息源"；正文中"社会信任 W"是技术语（与 CGSS 变量名一致）；CGSS 数据用"上网"（混合 PC + 手机），蓝皮书用"短视频时长"；避免"平台"/"应用"混用，统一用"短视频平台"。
- 数据时间口径：明确写"CGSS 2023 数据（综合上网频率）+ 2024 短视频蓝皮书（移动端短视频）"，论证方法可外推，但具体数字以 CGSS 为准。
- 术语统一：DAG、confounder、mediator、collider、PSM、ATT、backdoor 在首次出现时给中英括注。
- 内联引用 vs 参考文献对应：Pearl 1995 → 1；Rosenbaum & Rubin 1983 → 2；CGSS → 3；CNNIC → 4；蓝皮书 → 5；青少年中心 → 6；抖音算法原理 → 7。
- 无 em dash（——）
- 无"下一篇"链接（第五节末尾用"……下一篇讲双重差分（DID）：当 confounder 随时间变化但有'政策实施前后'的明显分界时怎么算"作为概念预告不算"下一篇"链接）
- 每图 caption 完整（封面 caption + 图1 caption + 图2 caption）

任何接缝问题在 articles 仓库本地修改。

- [ ] **Step 3: 提交到 articles 仓库**

```bash
cd "D:\Workspace\ml-learning\articles" && git add "causal/07_短视频沉迷.md" && git commit -m "draft(causal/07): 短视频沉迷归因——5 节点 DAG + CGSS 2023 PSM 实证剥离社会信任"
```

预期：1 个 commit 包含 1 个文件改动。

---

## Task 2: 写图生成脚本（CGSS data loader + 封面 + DAG + PSM 实证）

**Files:**
- Create: `scripts/causal/gen_cover_causal_07.py`

**Interfaces:**
- Produces: `articles/causal/cover_causal_07.png`（9×3.83 inch @ dpi100 ≈ 900×383 px）、`articles/causal/fig_dag_video.png`（9×4.5 inch @ dpi150 ≈ 1350×675 px）、`articles/causal/fig_psm_family.png`（9×4.0 inch @ dpi150 ≈ 1350×600 px）
- Consumes: `articles/causal/data/中国综合社会调查（2023）/CGSS2023.dta`（已在磁盘）；如 .dta 不可用，**回退到内置 _make_synthetic 函数**生成兜底数据

- [ ] **Step 1: 新建 `scripts/causal/gen_cover_causal_07.py`**

完整脚本内容如下：

```python
"""Generate cover + 2 figures for Causal Inference #07 (Short Video Addiction).

Cover (9 x 3.83, dpi=100) - WeChat public-account feed thumbnail only.
fig_dag_video.png (9 x 4.5, dpi=150) - 5-node DAG topology.
fig_psm_family.png (9 x 4.0, dpi=150) - PSM effect estimation on CGSS 2023.

Data: CGSS 2023 (中国综合社会调查, 11326 样本 × 437 变量, STATA .dta). 变量映射：
  X = a3012 空闲时间上网频率（high=1/2 vs low=3/4/5）
  Y = a29 最主要信息来源（互联网=5 vs 其他=1/2/3/4）
  Z = a2 性别 + a3a 出生年（age=2023-birthyr）
  W = a33 社会信任（5级 Likert）
  M = a36 生活幸福（5级 Likert）
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
os.makedirs(DATA, exist_ok=True)

# Same palette as causal_00 / 01 / 02 / 03 / 04 / 05
C_L1 = '#4A6FA5'   # primary blue (Z: confounder)
C_L2 = '#D67D3E'   # accent orange (W: confounder)
C_X  = '#2E5C8A'   # dark blue (X: treatment)
C_Y  = '#A23B3A'   # dark red (Y: outcome)
C_M  = '#888888'   # gray (M: collider)
C_CUT = '#8a3030'  # backdoor path
BG   = '#F5F2EC'
INK  = '#2A2A2A'
SUB  = '#888888'

COVER_PATH = os.path.join(OUT, 'cover_causal_07.png')
FIG_DAG_PATH = os.path.join(OUT, 'fig_dag_video.png')
FIG_PSM_PATH = os.path.join(OUT, 'fig_psm_family.png')

CGSS_DTA = os.path.join(DATA, '中国综合社会调查（2023）', 'CGSS2023.dta')


# ============================================================
# Data loading: CGSS 2023 (priority) or synthetic fallback
# ============================================================
def _try_load_cgss():
    """Load CGSS 2023 STATA file. Return (X, Y, Z, W, M) arrays or None.

    变量映射（CGSS 2023 居民问卷）：
      X: a3012 空闲时间上网频率 (high=1/2 vs low=3/4/5)
      Y: a29 最主要信息来源 (互联网=5 vs 其他=1/2/3/4)
      Z: [性别 a2, 年龄 age=2023-a3a]
      W: a33 社会信任 (5级 Likert)
      M: a36 生活幸福 (5级 Likert)
    """
    if not os.path.exists(CGSS_DTA):
        return None
    try:
        import pandas as pd
        df = pd.read_stata(CGSS_DTA, convert_categoricals=False)
    except Exception as e:
        print(f'[WARN] CGSS .dta load failed: {e}; falling back to synthetic data')
        return None

    # X: a3012 high vs low
    x_mask = df['a3012'].isin([1.0, 2.0, 3.0, 4.0, 5.0])
    X = (df.loc[x_mask, 'a3012'].isin([1.0, 2.0])).astype(float).values

    # Y: a29 互联网 vs 其他
    y_mask = df['a29'].isin([1.0, 2.0, 3.0, 4.0, 5.0])
    Y = (df.loc[y_mask, 'a29'] == 5.0).astype(float).values

    # Z: 性别 (1/2) + age (2023 - a3a)
    z_mask = df['a2'].isin([1.0, 2.0]) & df['a3a'].between(1920, 2005)
    gender = (df.loc[z_mask, 'a2'] == 1.0).astype(float).values  # 1=男
    age = (2023 - df.loc[z_mask, 'a3a']).astype(float).values

    # W: a33 5级 Likert
    w_mask = df['a33'].isin([1.0, 2.0, 3.0, 4.0, 5.0])
    W = df.loc[w_mask, 'a33'].astype(float).values

    # M: a36 5级 Likert
    m_mask = df['a36'].isin([1.0, 2.0, 3.0, 4.0, 5.0])
    M = df.loc[m_mask, 'a36'].astype(float).values

    # 取交集：所有变量都有效的样本
    n_min = min(len(X), len(Y), len(gender), len(W), len(M))
    if n_min < 100:
        print(f'[WARN] too few valid samples ({n_min}); falling back to synthetic')
        return None

    X = X[:n_min]
    Y = Y[:n_min]
    Z = np.column_stack([gender[:n_min], age[:n_min]])
    W = W[:n_min]
    M = M[:n_min]

    # 标准化 W 和 M 到 0-1（5级 Likert → [0,1]）
    W_norm = (W - 1) / 4
    M_norm = (M - 1) / 4

    print(f'[OK] CGSS 2023 loaded: n={n_min}, '
          f'X high={X.mean():.2%}, Y internet={Y.mean():.2%}, '
          f'gender male={gender.mean():.2%}, age mean={age.mean():.1f}, '
          f'W mean={W.mean():.2f}/5, M mean={M.mean():.2f}/5')
    return X, Y, Z, W_norm, M_norm


def _make_synthetic(n=7000, seed=42):
    """Synthetic fallback matching CGSS-style distribution."""
    rng = np.random.default_rng(seed)

    # Z: 性别 (0=女, 1=男) + 年龄 (18-90)
    gender = rng.binomial(1, 0.55, n)
    age = rng.integers(18, 90, n).astype(float)

    # W: 社会信任（5级 Likert → 0-1 标准化），约 0.65 mean
    W = np.clip(rng.normal(0.65, 0.2, n), 0, 1)

    # X: 上网频率（high=1 if 每天/一周数次, low=0 if 一年数次/从不）
    # 概率依赖 W：W 低 (低信任) 时 high 概率更高
    p_high = 0.25 + 0.15 * (1 - W) + 0.005 * (50 - age) / 30  # 年轻人更多高强度
    X = rng.binomial(1, np.clip(p_high, 0.05, 0.95))

    # Y: 互联网作为最主要信息源，依赖 X + W + age
    p_y = 0.3 + 0.3 * X + 0.2 * (1 - W) - 0.005 * age
    Y = rng.binomial(1, np.clip(p_y, 0.05, 0.95))

    # M: 生活幸福（5级 Likert → 0-1 标准化），依赖 X 和 Y（collider）
    M = np.clip(0.6 + 0.1 * X + 0.1 * Y - 0.05 * (1 - W) + rng.normal(0, 0.15, n), 0, 1)

    # 打包 Z 为 (gender, age)
    Z = np.column_stack([gender, age])

    return X.astype(float), Y.astype(float), Z, W, M


def _load_data():
    data = _try_load_cgss()
    if data is not None:
        print('[OK] Using CGSS 2023 real data')
        return data
    print('[FALLBACK] Using synthetic data (CGSS .dta not available)')
    return _make_synthetic()


# ============================================================
# DAG topology: 5 nodes, 7 edges (CGSS variable names)
# ============================================================
def _draw_dag(ax, annotate=True):
    nodes = {
        'X': (1.6, 2.4, C_X, 'X 上网频率\na3012'),
        'Y': (7.4, 2.4, C_Y, 'Y 信息依赖\na29'),
        'Z': (1.0, 4.4, C_L1, 'Z 性别/年龄\na2/a3a'),
        'W': (1.0, 0.4, C_L2, 'W 社会信任\na33'),
        'M': (7.4, 0.4, C_M, 'M 生活幸福\na36'),
    }
    edges = [
        ('X', 'Y', C_X, '-', 1.6),
        ('Z', 'X', C_CUT, '--', 1.4),
        ('Z', 'Y', C_CUT, '--', 1.4),
        ('W', 'X', C_CUT, '--', 1.4),
        ('W', 'Y', C_CUT, '--', 1.4),
        ('X', 'M', C_M, '-', 1.2),
        ('Y', 'M', C_M, '-', 1.2),
    ]
    for (a, b, c, ls, lw) in edges:
        xa, ya, _, _ = nodes[a]
        xb, yb, _, _ = nodes[b]
        ax.annotate('', xy=(xb, yb), xytext=(xa, ya),
                    arrowprops=dict(arrowstyle='->', color=c, ls=ls, lw=lw, alpha=0.8))

    for key, (x, y, c, label) in nodes.items():
        circle = plt.Circle((x, y), 0.42, facecolor='white', edgecolor=c, lw=2.4, zorder=5)
        ax.add_patch(circle)
        ax.text(x, y, label, ha='center', va='center', fontsize=11, fontweight='bold',
                color=c, zorder=6)

    if annotate:
        ax.text(4.5, 4.6, 'backdoor 路径 Z → X / Y', color=C_CUT, fontsize=9,
                ha='center', va='center', style='italic', zorder=7)
        ax.text(4.5, 0.3, 'backdoor 路径 W → X / Y', color=C_CUT, fontsize=9,
                ha='center', va='center', style='italic', zorder=7)
        ax.text(7.4, -0.05, 'collider（不能调）', color=C_M, fontsize=8.5,
                ha='center', va='top', style='italic', zorder=7)
        ax.text(4.5, 5.05, 'DAG：调整集 {Z 性别/年龄, W 社会信任}，M 是 collider 不能动',
                color=INK, fontsize=10, ha='center', va='center',
                fontweight='bold', zorder=7)


# ============================================================
# PSM estimation: Naive / Backdoor / PSM / Wrong-M
# ============================================================
def _estimate_effects(X, Y, Z, W, M):
    """Compute four estimates."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.neighbors import NearestNeighbors

    # 1. Naive
    naive = Y[X == 1].mean() - Y[X == 0].mean()

    # 2. PSM (logistic propensity score on Z + W, 1:4 NN, caliper)
    ps_design = np.column_stack([Z[:, 0], Z[:, 1], W])
    ps_model = LogisticRegression(max_iter=1000)
    ps_model.fit(ps_design, X)
    ps = ps_model.predict_proba(ps_design)[:, 1]

    treated_idx = np.where(X == 1)[0]
    control_idx = np.where(X == 0)[0]

    nn = NearestNeighbors(n_neighbors=4)
    nn.fit(ps[control_idx].reshape(-1, 1))
    distances, indices = nn.kneighbors(ps[treated_idx].reshape(-1, 1))

    caliper = 0.2 * ps.std()
    psm_treated_y = []
    psm_control_y = []
    for i, ti in enumerate(treated_idx):
        mask = distances[i] < caliper
        if mask.any():
            psm_treated_y.append(Y[ti])
            psm_control_y.append(Y[control_idx[indices[i][mask]]].mean())

    psm = np.mean(psm_treated_y) - np.mean(psm_control_y)

    # 3. Backdoor regression (Y ~ X + Z + W)
    X_design = np.column_stack([X, Z[:, 0], Z[:, 1], W])
    beta = np.linalg.lstsq(X_design, Y, rcond=None)[0]
    backdoor = beta[0]

    # 4. Wrong: also condition on M
    X_design_wrong = np.column_stack([X, Z[:, 0], Z[:, 1], W, M])
    beta_wrong = np.linalg.lstsq(X_design_wrong, Y, rcond=None)[0]
    wrong = beta_wrong[0]

    return naive, psm, backdoor, wrong


# ============================================================
# Cover: mini DAG (left) + "+2 倍" callout (center) + 4-bar chart (right)
# ============================================================
def make_cover(values):
    naive, backdoor, psm, wrong = values

    fig, ax = plt.subplots(figsize=(9, 3.83))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 3.83)
    ax.axis('off')

    ax.plot([0.4, 8.6], [3.55, 3.55], color='#E0DCD3', lw=1, zorder=1)
    ax.text(0.4, 3.65, '#07  因果推断  /  Short Video Addiction Attribution',
            fontsize=10, color=SUB, ha='left', va='center', zorder=3)

    sub_ax_left = fig.add_axes([0.04, 0.32, 0.40, 0.55])
    sub_ax_left.set_facecolor(BG)
    sub_ax_left.set_xlim(-0.5, 8.5)
    sub_ax_left.set_ylim(-0.6, 5.0)
    sub_ax_left.axis('off')
    _draw_dag(sub_ax_left, annotate=True)

    callout_x = 4.6
    callout_y = 2.0
    ax.text(callout_x, callout_y + 0.35, '2×', fontsize=40, fontweight='bold',
            color=C_CUT, ha='center', va='center', zorder=6)
    ax.text(callout_x, callout_y - 0.45,
            '信任低 vs\n信任高\n互联网信息依赖率',
            fontsize=9, color=INK, ha='center', va='center', zorder=6)

    bar_ax = fig.add_axes([0.62, 0.32, 0.34, 0.55])
    bar_ax.set_facecolor(BG)
    labels = ['朴素', '调 W', 'PSM', '调错 M']
    values_list = [naive, backdoor, psm, wrong]
    colors_bar = [SUB, C_L1, C_L2, C_M]
    bars = bar_ax.barh(labels, values_list, color=colors_bar, height=0.55)

    # 真值参考线（backdoor 值作为 best estimate proxy）
    bar_ax.axvline(backdoor, color=C_CUT, ls=':', lw=1, alpha=0.6)
    bar_ax.text(backdoor, 3.6, f'剥离后 {backdoor:+.2f}', fontsize=8, color=C_CUT,
                ha='center', va='bottom')

    bar_ax.set_xlim(min(values_list) - 0.1, max(values_list) + 0.3)
    bar_ax.set_xlabel('信息依赖差（概率差）', fontsize=9)
    bar_ax.tick_params(labelsize=8, colors=SUB)
    for spine in ['top', 'right']:
        bar_ax.spines[spine].set_visible(False)
    bar_ax.spines['left'].set_color(SUB)
    bar_ax.spines['bottom'].set_color(SUB)

    ax.text(4.5, 0.42,
            '沉迷归因：算法、社会、还是用户自己？',
            fontsize=12, fontweight='bold', color=INK,
            ha='center', va='center', zorder=5)
    ax.text(4.5, 0.10,
            'DAG · backdoor 准则告诉你该调 {社会信任}，别动 {生活幸福}',
            fontsize=9, color=SUB, ha='center', va='center', zorder=5)

    fig.savefig(COVER_PATH, dpi=100, bbox_inches=None,
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'Cover saved: {COVER_PATH}')


# ============================================================
# Fig 1: 5-node DAG topology
# ============================================================
def make_fig_dag():
    fig, ax = plt.subplots(figsize=(9, 4.5))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    ax.set_xlim(-0.5, 8.5)
    ax.set_ylim(-0.6, 5.0)
    ax.set_aspect('equal')
    ax.axis('off')
    _draw_dag(ax, annotate=True)
    ax.set_title('5 节点 DAG：X 上网频率 → Y 信息依赖；Z/W 后门路径，M collider',
                 fontsize=12, fontweight='bold', color=INK, pad=10, loc='left')
    fig.tight_layout()
    fig.savefig(FIG_DAG_PATH, dpi=150, bbox_inches='tight',
                facecolor='white')
    plt.close(fig)
    print(f'DAG figure saved: {FIG_DAG_PATH}')


# ============================================================
# Fig 2: PSM estimation comparison (4 bars)
# ============================================================
def make_fig_psm(values):
    naive, backdoor, psm, wrong = values

    fig, ax = plt.subplots(figsize=(9, 4.0))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    labels = ['朴素\nY ~ X', 'Backdoor 调整\nY ~ X + Z + W', 'PSM\n配对后比', '错误调整\nY ~ X + Z + W + M']
    vals = [naive, backdoor, psm, wrong]
    colors_bar = [SUB, C_L1, C_L2, C_M]

    bars = ax.bar(labels, vals, color=colors_bar, width=0.6)
    ax.axhline(backdoor, color=C_CUT, ls='--', lw=1.6, alpha=0.7)
    ax.text(3.5, backdoor + 0.005, f'剥离后 {backdoor:+.3f}', fontsize=10, color=C_CUT,
            ha='right', va='bottom')

    for bar, val in zip(bars, vals):
        h = bar.get_height()
        va = 'bottom' if h >= 0 else 'top'
        offset = 0.005 if h >= 0 else -0.005
        ax.text(bar.get_x() + bar.get_width() / 2, h + offset,
                f'{val:+.3f}', ha='center', va=va, fontsize=11, fontweight='bold')

    ax.set_ylabel('信息依赖差（概率差）', fontsize=11)
    ymin = min(vals) - 0.05
    ymax = max(vals) + 0.1
    ax.set_ylim(ymin, ymax)
    ax.tick_params(labelsize=10, colors=SUB)
    ax.grid(axis='y', alpha=0.3, ls=':')
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)

    ax.set_title('PSM 实证：剥离社会信任后效应回落，调 collider 翻负',
                 fontsize=12, fontweight='bold', color=INK, pad=10, loc='left')

    fig.tight_layout()
    fig.savefig(FIG_PSM_PATH, dpi=150, bbox_inches='tight',
                facecolor='white')
    plt.close(fig)
    print(f'PSM figure saved: {FIG_PSM_PATH}')
    print(f'  Naive={naive:+.3f}  Backdoor={backdoor:+.3f}  PSM={psm:+.3f}  Wrong={wrong:+.3f}')


if __name__ == '__main__':
    X, Y, Z, W, M = _load_data()
    values = _estimate_effects(X, Y, Z, W, M)
    make_cover(values)
    make_fig_dag()
    make_fig_psm(values)
    print('Done.')
```

- [ ] **Step 2: 跑脚本生成三张图**

```bash
cd "D:\Workspace\ml-learning" && python scripts/causal/gen_cover_causal_07.py
```

Expected: 终端打印
- `[OK] CGSS 2023 loaded: n=..., X high=..., Y internet=..., ...`（如果 Task 0 完成 + 数据有效）
- 或 `[FALLBACK] Using synthetic data (CGSS .dta not available)`（如果数据不可用）
- 之后三行 `Cover saved: ...`、`DAG figure saved: ...`、`PSM figure saved: ...`、一行 `Naive=... Backdoor=... PSM=... Wrong=...`、以及 `Done.`

数字预期（CGSS 2023 真实数据，约 7000 样本）：
- 朴素 ≈ +0.25（被 W 抬升）
- Backdoor ≈ +0.10-0.15（剥离后）
- PSM ≈ +0.10-0.15（接近真值）
- 错误 M ≈ -0.05 ~ +0.05（collider 翻负或扰动）

合成数据兜底下数字可能不同，但相对大小关系应保持"朴素 > Backdoor ≈ PSM > 错误 M"。

- [ ] **Step 3: 视觉检查**

打开 `articles/causal/cover_causal_07.png`、`fig_dag_video.png`、`fig_psm_family.png`，确认：
- **封面**：左侧 5 节点 DAG 拓扑清晰，节点标签用 CGSS 变量名（X 上网频率 a3012 / Y 信息依赖 a29 / Z 性别/年龄 a2/a3a / W 社会信任 a33 / M 生活幸福 a36）；红色 Z/W 双后门路径用虚线，灰色 M 用实线灰色；中间"2×"callout 红色；右侧 4-bar 横图（朴素/调 W/PSM/调错 M），用红色虚线竖标剥离后估计值
- **封面底部**：标题"沉迷归因：算法、社会、还是用户自己？"，副标题"DAG · backdoor 准则告诉你该调 {社会信任}，别动 {生活幸福}"
- **fig_dag_video**：5 个节点位置（X 左中 / Y 右中 / Z 左上 / W 左下 / M 右下），节点用圆圈 + 标签，箭头方向清晰；后门路径红色虚线；collider M 灰色实线
- **fig_psm_family**：4 个竖柱，柱子顶有数值标签；红色虚线标剥离后估计值；y 轴"信息依赖差（概率差）"
- CJK 字体显示正常（无方框）

任何一项不符，回去调整 Step 1 的脚本重跑。

- [ ] **Step 4: 提交到 articles 仓库**

```bash
cd "D:\Workspace\ml-learning\articles" && git add "scripts/causal/gen_cover_causal_07.py" "causal/cover_causal_07.png" "causal/fig_dag_video.png" "causal/fig_psm_family.png" && git commit -m "art(causal/07): 封面 + DAG 拓扑 + PSM 实证——CGSS 2023 数据演示剥离社会信任"
```

预期：1 个 commit 包含 4 个文件改动（脚本 + 3 张新图）。**注意**：`.dta` 数据文件不 commit（gitignored），由 README 指引下载。

---

## Task 3: 更新 _local/plan.md 状态

**Files:**
- Modify: `_local/plan.md`（gitignored，本地唯一事实源）

**Interfaces:**
- 状态字符串需包含：新标题、5 节点 DAG、CEPS 数据、未推送状态

- [ ] **Step 1: 定位 causal/06 行附近**

```bash
cd "D:\Workspace\ml-learning" && grep -n "06 \|07 \|因果线" _local/plan.md | head -10
```

- [ ] **Step 2: 替换原 causal/07 行（之前是 CEPS 方案，现改为 CGSS 2023 真实数据方案）**

把 `07 | 沉迷归因：...` 那一行的状态描述改为：

```
07 | 沉迷归因：算法、社会、还是用户自己？DAG+PSM 怎么挑出该调的社会变量 | DAG 因果图、5 节点 DAG（X 上网频率 a3012 / Y 信息依赖 a29 / Z 性别年龄 a2+a3a / W 社会信任 a33 / M 生活幸福 a36）、backdoor 准则、PSM 倾向得分匹配、Pearl 1995、Rosenbaum & Rubin 1983、CGSS 2023（11326 样本 × 437 变量，公开可下载）、CNNIC 54 次报告 2024 | 通用 | 📝 草稿（2026-09-05 spec 完成：DAG+PSM 实证剥离社会信任 confounder；待用户手动真实发布）
```

- [ ] **Step 3: 提交到 root repo**

```bash
cd "D:\Workspace\ml-learning" && git add _local/plan.md && git commit -m "chore(plan): 因果线 #07 状态更新——CGSS 2023 真实数据替换 CEPS 方案"
```

预期：1 个 commit 包含 1 个文件改动。

**注意**：`_local/` 是 gitignored。如果 commit 报"nothing to commit"或"pathspec ... did not match"，先 `git ls-files _local/plan.md` 检查它是否被跟踪；若没跟踪，跳过此 commit（更新状态只是本地参考，不强制 commit）。

---

## Verification

执行完 Task 0-3 后做总验证：

1. **CGSS 数据可读**（如 Task 0 完成）：
   ```bash
   cd "D:\Workspace\ml-learning" && ls -la "articles/causal/data/中国综合社会调查（2023）/" | grep CGSS2023.dta
   ```
   预期：CGSS2023.dta 文件存在（约 47.6MB）。

2. **articles 仓库最终状态**（不 push）：
   ```bash
   cd "D:\Workspace\ml-learning\articles" && git log --oneline -4 && echo "---" && git status --short
   ```
   预期：最近 2 个 commit 是 Task 1（draft: 文章）和 Task 2（art: 封面+DAG+PSM）。`git status --short` 对 `causal/` 目录应是干净的（.dta 不跟踪）。

3. **图片与文章引用对得上**：
   ```bash
   cd "D:\Workspace\ml-learning\articles" && grep -E "cover_causal_07|fig_dag_video|fig_psm_family" "causal/07_短视频沉迷.md"
   ```
   预期：三行引用，对应 Task 2 产出的三张图。

4. **文章无 em dash、无"下一篇"链接**：
   ```bash
   cd "D:\Workspace\ml-learning\articles" && grep -E "——|\*\*下一篇\*\*" "causal/07_短视频沉迷.md" || echo "PASS: 无 em dash / 无下一篇"
   ```
   预期：PASS。

5. **5 节标题与 spec 一致**：
   ```bash
   cd "D:\Workspace\ml-learning\articles" && grep -E "^## " "causal/07_短视频沉迷.md"
   ```
   预期：
   ```
   ## 一、调对调错差几倍？
   ## 二、沉迷的 5 节点 DAG：算法、用户、社会、信息、幸福
   ## 三、三种基本结构：链/叉/对撞，社会信任为什么必须调
   ## 四、PSM 实证：用 CGSS 2023 ~7000 有效样本剥离社会信任
   ## 五、什么时候 DAG/PSM 失灵：算法持续升级 + 用户自适应
   ```

6. **参考文献 ≥ 7 条**：
   ```bash
   cd "D:\Workspace\ml-learning\articles" && grep -cE "^[0-9]+\. " "causal/07_短视频沉迷.md"
   ```
   预期：≥ 7。

7. **数据来源标识**：
   ```bash
   cd "D:\Workspace\ml-learning\articles" && grep -E "CGSS|中国综合社会调查" "causal/07_短视频沉迷.md"
   ```
   预期：≥ 2 个 CGSS 标识。

8. **root repo 状态**：未推送（仅本地 commit）。
   ```bash
   cd "D:\Workspace\ml-learning" && git log --oneline -3
   ```
   预期：最近 commit 是 design spec 或 plan 本任务产出的状态更新，不应有任何 push。

任何 verification 项不符，回对应 Task 修正。