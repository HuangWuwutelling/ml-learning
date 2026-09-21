# 环保申报智能助手（LangGraph Agent · 工具编排）

企业办排污许可申报，要自己查法规、核算排放量、填申报表、写报告，环节分散。
这里把每个环节做成一个工具，由 LangGraph 的 ReAct 框架驱动大模型按需调用，
用户说一句话发起，剩下的步骤智能体接着做。界面用 Gradio。

## 结果

| 指标 | 数 |
|---|---|
| 端到端工具选择（12 条用例，跑 3 遍） | 12/12、12/12、12/12 |
| 该追问、不该调工具的用例（跑题 / 笼统问「算排放」/ 开局一句话） | 3 条全没调错 |
| 行业名匹配单测 | 28 passed |

口径和保留条件见「评测」一节。

## 怎么跑

```bash
pip install -r requirements.txt

python init_chromadb.py    # 首次：从两份法规 HTML 建知识库
python app.py              # http://localhost:7861
```

`DEEPSEEK_API_KEY` 从仓库根的 `.env` 读（`config.py` 里 `load_dotenv()` 向上查找）。

## 5 个工具

| 工具 | 输入 | 输出 |
|---|---|---|
| `lookup_regulation` | 自然语言问题 | 最相关的 3 条法规原文 + 来源 |
| `calculate_emission` | 行业、废水日排放量、有无处理设施 | COD / 氨氮排放量（kg/天） |
| `calculate_air_emission` | 行业、废气量（m³/h）、月运行小时数 | SO₂ / NOₓ 排放量（kg/月） |
| `fill_form` | 企业信息 JSON | 排污许可证申报表草稿 |
| `generate_report` | 完整信息 JSON | 申报报告 |

模型靠每个工具 docstring 里的描述判断该调哪个。

## 文件

| 文件 | 干什么 |
|---|---|
| `agent.py` | 组装：DeepSeek + 5 个工具 + `prompt.md` 当 system prompt |
| `prompt.md` | system prompt 单独成文件，改提示词不用动代码 |
| `tools.py` | 5 个工具 + 行业名归一化 + 排放因子表 |
| `app.py` | Gradio 对话界面（7861） |
| `init_chromadb.py` | 从法规 HTML 建 ChromaDB |
| `eval_agent.py` | 端到端评测 |
| `test_match_industry.py` | 行业名匹配单测 |

## 知识库

`init_chromadb.py` 抽两份法规的正文，按 500 字切分、50 字重叠，
用 `BAAI/bge-small-zh-v1.5` 编码写进 ChromaDB：

| 法规 | 块数 |
|---|---|
| 排污许可管理办法 | 24 |
| 排污许可管理条例 | 22 |
| **合计** | **46** |

向量缓存在 `data/embeddings_cache.npz`，启动直接读，不重算。

## 行业名归一化

已知行业只有 5 个（印染 / 化工 / 造纸 / 钢铁 / 污水处理厂），用户嘴里的写法要靠规则落到其中之一。
规则是「精确优先 → 关键字包含 → 长关键字优先」，外加一条后缀黑名单：

```
化工      → 化工      精确
化工企业  → 化工      关键字 + 通用后缀
化工机械  → 不匹配    「机械」在黑名单里，主体是机械制造业
钢铁冶炼  → 钢铁      「冶炼」不在黑名单，是合法说法
```

语义是：**关键字后面跟着另一个行当名，就说明它不是行业主体。**
用黑名单不用白名单（「关键字后面必须是厂/公司」），因为白名单会把「钢铁冶炼」也拒掉。

`_NON_INDUSTRY_SUFFIXES` 是启发式的，不是完备的中文行业词法，漏掉的后缀会造成误命中。
`test_match_industry.py` 用 26 条用例盯这件事。

## 评测

`eval_agent.py` 12 条用例，每条给两个期望：

- `want`：这条会话里**必须**出现的工具
- `avoid`：**必须不**出现的工具

跑完解析 `create_react_agent` 返回的 `tool_calls` 自动比对，不需要人工看。
每条 AI 回复另做一次机检，看有没有违反 `prompt.md` 里「每轮只问一个问题」的约束。

```bash
python eval_agent.py                 # 全部 12 条
python eval_agent.py --repeat 3      # 看逐遍波动
python eval_agent.py --only calc_vague
```

结果写 `eval_results/eval_<时间戳>.json`（含每条用例的完整回复，便于复核）。

**最近一次 3 遍：工具选择 12/12、12/12、12/12，禁用工具被调 0 次，逐遍 pass/fail 一致。**

两点保留：

- **「单问违规」这个机检数不能用。** 口径是「单轮回复里问号 >= 2 或追问里带列表」，
  但「A？还是 B？」这种一个问题带选项的写法会被数成两个，是已知误报。
  三遍分别是 10/24、11/26、11/22 轮，分母还随模型轮数浮动。只在本地当诊断用。
- **判据写错会把模型正确的行为记成 FAIL。** 第一版 `form_ready` / `report_ready`
  只给了 4 项信息就期望直接出表，判 FAIL；但 `prompt.md` 要求 7 项齐全才生成材料，
  模型继续追问是对的。补全 7 项后两条都 PASS。用例里的注释记了这件事。

### 已知缺口

`flow_collect_then_form` 那条 9 轮用例里，模型连续 3 轮重复问同一句
「请问贵厂有几个排气筒？高度大约是多少米呢？」，用户始终没回答，
它最后也照样把申报表生成了。多轮里卡在同一个追问上，没有退路。

## 测试

```bash
python -m pytest test_match_industry.py -q    # 28 passed
```

## 依赖与说明

- 对话模型 `deepseek-chat`（temperature 0.3），嵌入模型 `BAAI/bge-small-zh-v1.5`（离线缓存）
- ChromaDB 用本地文件，不用起服务；`tools.py` 的 `_load_docs_from_chromadb()`
  直接读它的 SQLite，绕开 Python API
- `agent.py` 没有传 checkpointer，多轮上下文由调用方维护：
  `app.py` 把完整 history 转成 messages 再传进去，评测脚本按轮维护消息列表
