# 质量合规智能助手 (QMS AI Assistant)

Django 5.1 + LangGraph + ChromaDB + DeepSeek-V3 实现的"AI 增强质量合规"项目。
数据来源公开可追溯，可一键复现。

依赖版本写在 `requirements.txt` 里（范围），本机实测装的是：Django 5.1.15 / LangGraph 1.2.14 /
langchain 1.4.3 / langchain-community 0.4.2 / chromadb 0.5.5 / Streamlit 1.65.0。

## 数据来源

- **召回数据**：国家市场监督管理总局缺陷产品召回技术中心
  - 召回公告：https://www.samrdprc.org.cn/xfpzh/xfpzhgg/
  - 召回动态：https://www.samr.gov.cn:3030/zlfzj/qxcpzh/zhdt/
- **知识库**：GB/T 19001-2016 摘要、AIAG CQI 摘要、SAMR 2025 年统计通告 + 第 21 号公告
- **说明**：仓库中 `data/knowledge_sources/` 与 `raw_html/` 仅为**演示节选**（非 GB/T 19001 全文 PDF / SAMR 完整公告页），用于支撑端到端跑通与本地评测。

## 快速复现

```bash
# 1. 启动数据库
docker compose up -d

# 2. 安装依赖
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 填 DEEPSEEK_API_KEY（默认是占位符 replace-me）

# 3. 迁移 + 灌演示数据
python manage.py migrate
python scripts/seed_demo_data.py

# 4. 灌知识库 + 召回历史索引
python knowledge/ingest.py
python scripts/seed_chroma_recall.py

# 5. 启动服务
python manage.py runserver       # API: http://localhost:8000
streamlit run dashboard/app.py   # Dashboard: http://localhost:8501

# 6. 跑评测
python eval/run_eval.py
```

`docker compose down -v && ./scripts/reset_and_seed.sh` 可一键清库 + 重建（bash 环境，Windows 走 Git Bash）。

## 演示场景

1. **客户投诉分析**：`POST /api/agent/complaint-analyze/ {"text": "充电器冒烟"}`
2. **CAPA 智能起草**：同上接口返回 `capa_draft` 字段
3. **知识库问答**：`POST /api/agent/chat/ {"message": "GB/T 19001 关于不合格品控制的要求"}`
4. **多轮对话**：传 `thread_id` 保持上下文

## 评测结果

`python eval/run_eval.py` 的退出码是三态：

| 退出码 | 含义 |
|---|---|
| 0 | 4 个指标都跑到，且全部达标 |
| 1 | 有指标跑到，但低于目标 |
| 2 | 有指标没跑到（跳过）——数字没测出来，不算失败，也不能当通过 |

**2026-11-03（改动判定逻辑后，本机重跑）**：

| 评测集 | 数字 | 目标 | 结果 |
|---|---|---|---|
| 严重度判定（severity_25） | 25/25 = 100% | ≥ 75% | PASS |
| 工具选择（tools_30） | 没测出来 | ≥ 80% | SKIPPED |
| 不该调工具（no_tool_8） | 没测出来 | = 100% | SKIPPED |
| RAG 引用准确（rag_20，真 precision@5） | 没测出来 | ≥ 40% | SKIPPED |

三个跳过的原因各不相同，都不是"跑分不达标"：

- `tools_30` / `no_tool_8`：`.env` 里 `DEEPSEEK_API_KEY=replace-me` 是占位符，DeepSeek 返回 401，30 条 / 8 条全部没跑起来。**这两个指标在 2026-11-03 之前是假指标**（判定逻辑见下），现在逻辑是对的，但本机没有真 key，所以数字还没测出来。填入真 key 重跑即可解锁。
- `rag_20`：本机装的是 NumPy 2.4.6，而 chromadb 0.5.5 用了 `np.float_`（NumPy 2.0 起被删），`import chromadb` 直接炸。`requirements.txt` 已加 `numpy<2` 钉住，照着装即可跑。

### 判定口径（改过的地方，别照旧数字理解）

| 指标 | 口径 | 2026-11-03 之前 |
|---|---|---|
| `severity_25` | 关键词规则表的**回归测试**：数据集标签与 `agent/tools.py` 的关键词表同源 | 同左，但 README 没写清，看起来像分类能力 |
| `tools_30` | 跑真 agent，读轨迹里的 `tool_calls`，与 `expected_tools` 比集合 F1；`accuracy` = 平均 F1，`correct` = 集合完全一致的条数 | **假指标**：另起一个 LLM 去猜该调哪些工具，只要回了非空字符串就算对，从没跟 `expected_tools` 比过，不可能失败 |
| `no_tool_8` | 一次工具都没调，且 agent 仍然回了一句话 | **假指标**：用"回复长度 < 100"当"没调工具"的代理，调了工具回长文照样算过 |
| `rag_20` | 全集合 top-5 里 `doc_id` 落在 `expected_doc_ids` 的占比（真 precision@5） | 同左（2026-10-09 已改过一次，去掉了退化写法） |

`tools_30` / `no_tool_8` 的判定逻辑用 `tests/test_eval_scoring.py` 离线覆盖（14 条用例，不调 LLM）。
`multi_turn_5.jsonl`（5 条）目前**没有指标消费**，只作为多轮对话的样例数据留在仓库里。

## 技术栈

- Django 5.1 + DRF 3.15（业务系统，7 张表：3 维 + 2 事实 + 2 业务）
- PostgreSQL 16（OLTP + 星型分析）
- LangGraph >= 0.2（5 工具 agent + 多轮记忆 + 3 intent router）
- ChromaDB + bge-small-zh-v1.5（向量库）
- DeepSeek-V3（LLM）
- Streamlit + Plotly（数据看板，4 tabs）

## 已知限制（Known Limitations）

- **⚠️ 当前评测状态：1 PASS / 3 SKIPPED**（共 4 个指标）。`severity_25` 通过（25/25，目标 75%）；`tools_30`、`no_tool_8` 因 `DEEPSEEK_API_KEY=replace-me` 是占位符被跳过；`rag_20` 因本机 NumPy 2.4.6 与 chromadb 0.5.5 不兼容被跳过。**跳过的三个数字都没有测出来，不能当通过。**
- **`severity_25` 不是分类能力评测**：它测的是关键词规则表有没有被改坏。数据集标签与规则表同源，换一批人工标注的数据才有资格说"分类准不准"。
- **`DEEPSEEK_API_KEY` 是占位符**：`scripts/seed_demo_data.py` 与 eval 中的 LLM 调用在没有真实 key 时只能跑不依赖 LLM 的部分（如严重度判定走关键词规则，不调 LLM；agent 多轮、工具选择评估直接跳过）。
- **NumPy 必须 < 2**：chromadb 0.5.5 用了 `np.float_`，NumPy 2.0 起这个别名被删，`import chromadb` 会直接抛 AttributeError。`requirements.txt` 已钉 `numpy<2`。
- **知识库为演示节选**：`data/knowledge_sources/` 内是 GB/T 19001-2016 / AIAG CQI / SAMR 公告的摘要 + 节选，不是完整 PDF / 官方公告页。接生产前需要替换为正式来源。
- **召回数据为种子数据**：`scripts/seed_demo_data.py` 灌的是预置示例，`scrapers/` 下的 3 个爬虫（samr 主站 + samrdprc 公告 + samrdprc 新闻）可拉真实数据但需要出口网络可达，且 samrdprc 主站有反爬，生产 IP 限流时建议走 NHTSA 备援源。
- **`multi_turn_5` 没有指标消费**：5 条多轮样例只作数据留存，不参与打分。
- **演示截图**：未捕获，README 不附截图。