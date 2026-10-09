# 质量合规智能助手 (QMS AI Assistant)

Django 5.1 + LangGraph 0.2 + ChromaDB + DeepSeek-V3 实现的"AI 增强质量合规"项目。
数据来源公开可追溯，可一键复现。

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

最后一次 `python eval/run_eval.py` 跑分（2026-10-09）：

| 评测集 | 数字 | 目标 | 结果 |
|---|---|---|---|
| 严重度分类（severity_25） | 25/25 = 100% | ≥ 75% | PASS |
| 工具选择（tools_30） | — | ≥ 80% | SKIPPED |
| 不该调工具（no_tool_8） | — | = 100% | SKIPPED |
| RAG 引用准确（rag_20） | 10/20 = 50% | ≥ 62% | FAIL |

`tools_30` 与 `no_tool_8` 跳过的原因：评测脚本调用 DeepSeek-V3 做 LLM-as-judge / agent 执行，当前 `.env` 中 `DEEPSEEK_API_KEY=replace-me` 是占位符，未配置真实 key；填入真实 key 后重新跑即可解锁这两个指标。

`rag_20` 50% 偏低于 62% 目标的原因：知识库当前只灌了演示节选文本（~30 块），不是 GB/T 19001 全文 PDF；接入真实 PDF 后预计可达 62%+。

## 技术栈

- Django 5.1 + DRF 3.15（业务系统，7 张表：3 维 + 2 事实 + 2 业务）
- PostgreSQL 16（OLTP + 星型分析）
- LangGraph 0.2（5 工具 agent + 多轮记忆 + 3 intent router）
- ChromaDB + bge-small-zh-v1.5（向量库）
- DeepSeek-V3（LLM）
- Streamlit + Plotly（数据看板，4 tabs）

## 已知限制（Known Limitations）

- **⚠️ 当前评测状态：1 PASS / 1 FAIL / 2 SKIPPED**（共 4 个指标）。`severity_25` 通过（100%，目标 75%）；`rag_20` 未达标（50%，目标 62%，根因：知识库只灌了演示节选，接入真实 PDF 后可达 62%+）；`tools_30` 与 `no_tool_8` 因 `.env` 中 `DEEPSEEK_API_KEY=replace-me` 是占位符被跳过，配置真实 key 后重跑 `python eval/run_eval.py` 即可解锁。
- **`DEEPSEEK_API_KEY` 是占位符**：`scripts/seed_demo_data.py` 与 eval 中的 LLM 调用在没有真实 key 时只能跑不依赖 LLM 的部分（如严重度分类走关键词 + 规则，不调 LLM；agent 多轮、工具选择评估直接跳过）。
- **知识库为演示节选**：`data/knowledge_sources/` 内是 GB/T 19001-2016 / AIAG CQI / SAMR 公告的摘要 + 节选，不是完整 PDF / 官方公告页。接生产前需要替换为正式来源。
- **召回数据为种子数据**：`scripts/seed_demo_data.py` 灌的是预置示例，`scrapers/` 下的 3 个爬虫（samr 主站 + samrdprc 公告 + samrdprc 新闻）可拉真实数据但需要出口网络可达，且 samrdprc 主站有反爬，生产 IP 限流时建议走 NHTSA 备援源。
- **2/4 评测指标暂跳过**：见上表 "SKIPPED" 两行，待真实 API key 配置后重跑 `python eval/run_eval.py` 即可出分。
- **演示截图**：未捕获，README 不附截图。