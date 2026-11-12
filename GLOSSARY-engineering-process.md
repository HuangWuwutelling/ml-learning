# GLOSSARY · 工程流程与工具链

文档怎么写、review 怎么做、测试怎么加、检查从哪跑。这份表描述的是**做法**，不是某次任务的记录。

## Language

**context load / cognitive load**: 每轮都进上下文的 token 量 / 人去查资料的成本。两者不是一回事：
文档写长了第一种会涨，写清楚了第二种才会降。
_Avoid_: `token 消耗`（混为一谈）

**in-file step / in-file reference / disclosed reference**: 文档信息的三档分层。in-file step 是每轮
都要照做的动作，写在文件里；in-file reference 是常查但不必每轮读的内容；disclosed reference 是
需要时才查的外部文档，只在文件里留一个指针。
_Avoid_: `详细说明`（不标层级）

**context pointer**: 指向别处的一句话。写法决定触发可靠性：前导词打头，一个分支一个触发词，
删掉正文已经带的信息。
_Avoid_: `链接`、`参考`（不说是哪一档）

**阶段边界（phase boundary）**: 一个会话该在哪停、停了之后留什么。决策顺序是
Continue → `/clear` → `/handoff` → subagent → `/compact`；`/compact` 是兜底，不是第一选择，
因为压缩会把前面的决定压平。handoff 用来换 harness、换仓库、交给同事，或中途岔出支线。
_Avoid_: `压缩上下文`（不说是哪一步）

**双轴 review**: 一次 review 拆成 Standards 轴（合不合本仓规范）与 Facts 轴（数字能不能回源核）
两条独立报告。两条轴各给各的结论，**不合并不跨轴重排**。
_Avoid_: `全面 review`、`一次看完`

**fixed point（对比基准）**: review 或写作要比对的起点。必须先验证基准能解析、diff 非空，
再往下走；坏 ref 要在这一步失败，不能拖到并行 agent 里才炸。
_Avoid_: `上一版`、`最近改动`（不写具体 commit）

**归档基线（archive baseline）**: 已发布文章在 articles 仓跟踪的 PNG 与 CSV。重跑生成器后
`cd articles && git status --porcelain` 必须为空，即产物逐字节可复现。
_Avoid_: `最新产物`

**生成器（gen_*.py）**: `scripts/<series>/gen_*.py`，输入数据与参数，输出图（PNG）与数据表（CSV）。
产物归档在 articles 仓。改数字要改生成器或模型，不改 PNG。
_Avoid_: `脚本`（不说是哪一类）

**边界测试（boundary test）**: 只验证公开接口与产物结构，不改业务逻辑、不依赖外部服务
（API key、GPU）。需要外部依赖的用例必须 skip 而不是 fail。
_Avoid_: `单元测试`（不说是哪一层）

**元测试（meta-test）**: 校验评测集与产物的结构（字段完整、id 唯一、数值落在合法范围），
而不是跑一遍业务逻辑。目前 env-rag 的 30 条评测集、env_agent 的 12 条 case、lora 的 34 条
test_set 都只有元测试。
_Avoid_: `数据校验`（太泛）

**契约测试（contract test）**: 钉住对外口径的只读测试。放在冻结项目外面
（`projects/evals/tests/`），不 import 业务代码，验的是「默认档位、条数、id、工具清单、
README 数字与产物对不对得上」。**验口径，不验智能**：模型答得好不好由各自的评测脚本负责。
_Avoid_: `回归测试`、`单元测试`

**check 入口（check entrypoint）**: `tools/check_all.py`。聚合命名规范、文章口径、
术语表与 ADR 体检、三个主项目的契约测试，逐项打印 OK/FAIL，退出码非零即失败。
_Avoid_: `测试`、`lint`（单一工具）

**评测入口（eval entrypoint）**: `projects/evals/run_all.py`。默认跑契约测试加
env_agent 的行业名匹配单元测试；加 `--agent-eval` 才跑真实评测（要 `DEEPSEEK_API_KEY`）。
对应 JD 里的测试评估项。
_Avoid_: `测试脚本`

**回归测试（regression test）**: 把一批已知输入反复跑，验证输出没有变坏。它跟评测集分工：
评测集量质量高低，回归测试防退化。期望值必须来自不受被测逻辑影响的地方，否则断言自证。
_Avoid_: `测试`（不说是哪种）、`评测`（量质量不是防退化）

**单元测试（unit test）**: 测单个函数或单个分支的最小测试，一个测试只断一件事。它在本仓
的测试分层里是最底层，往上是元测试 / 契约测试 / 回归测试。
_Avoid_: `单测`（缩写）、`测试`（不说是哪一层）

**资产台账（asset registry）**: 一份清单，记录每个可复用资产（Prompt / 知识库 / 工具 / 规则集 /
评测集）的元数据：owner、版本、适用范围、状态、下线条件。它回答「这东西归谁管、什么时候能删」，
目录结构回答不了这两个问题。
_Avoid_: `资产清单`（不写元数据字段）、`目录`（目录只列路径，台账记责任与状态）

**语料清单（corpus manifest）**: 一批外部文档的来源 URL、抓取时间、sha256、页数与许可记录。
作用是同一份语料能被重新取回并验证没有变过。
_Avoid_: `语料`（不指清单本身）、`数据源`（不指可复现记录）

## Relationships

- **check 入口** 与 **评测入口** 分工：check 管静态一致性（不执行项目代码），run_all 管可执行验证。
- **边界测试** 与 **元测试** 服务同一条命令，即评测入口。
- **契约测试** 是 **元测试** 的一种形态，位置在冻结项目外面（ADR-0015）。
- **归档基线** 是 **生成器** 的验收标准：**生成器** 的产出必须与归档基线逐字节一致。
- **术语表与 ADR** 放仓库根目录（会上 GitHub），**生成器** 放 `scripts/`
  （本地工具，被 gitignore），**check 入口** 放 `tools/`（要作为公开证据）。
  文档分层与文件可见性是两件事，别混。
- **资产台账** 与 **语料清单** 是两类不同的清单：台账记「谁负责、什么时候下线」，
  清单记「这份东西从哪来、是不是原件」。前者对应生命周期，后者对应可复现。
- **回归测试** 与 **评测集** 分工：评测集量质量高低，回归测试防退化。两者都用同一批
  输入，但一个比阈值，一个比不变。

## Flagged ambiguities

1. **「测试」一词在本仓有三个意思**：工程测试（pytest）、评测集（eval set）、元测试。
   引用时用全称。
2. **`scripts/` 被 gitignore**，所以生成器在 GitHub 上看不到。求职展示的证据落在
   `projects/evals/`、`tools/` 与根 `README.md` 的「快速复现」一节。
3. **契约测试通过 ≠ 模型效果好**。契约测试只验口径，跑真实评测要 key 和 GPU，
   两件事不能互相顶替。
