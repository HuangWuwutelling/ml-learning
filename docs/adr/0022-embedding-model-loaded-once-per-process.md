# ADR-0022 · embedding 模型进程内只建一次

- 状态: accepted
- 登记日期: 2026-11-04
- 决策日期: 2026-11-04

## 约束

QMS 项目的 agent 一轮里会调多个工具，LangGraph 的 `ToolNode` 是**并发**跑的。
2026-11-04 填了真 key 之后重跑评测，`tools_30` / `no_tool_8` / `rag_20` 三个指标
一条用例都没跑起来，全挂在：

```
NotImplementedError: Cannot copy out of meta tensor; no data!
  agent/tools.py:12 _get_chroma
  langchain_community/embeddings/huggingface.py:349 SentenceTransformer(...)
  sentence_transformers/SentenceTransformer.py:316 self.to(device)
```

诊断结论（`projects/quality_compliance_assistant/`）：

- transformers 4.57.1 的 `from_pretrained` 走 **meta device** 加载权重。
- **同一个模型并发加载会 race**：两个线程同时 `AutoModel.from_pretrained`，
  至少有一个的 71 个参数全留在 meta 上，`.to('cpu')` 直接抛（有时两个都坏）。
- **坏状态留在进程里**：race 之后连顺序加载也一直失败，重开进程才恢复。
  磁盘上的 HF 缓存是好的（72 个张量都能读），不是文件坏了。
- 顺序加载永远正常；装 `accelerate` 没用（不是 accelerate 那条加载路径的问题）。

另一半原因是 `_get_chroma()` **每次工具调用都重建一次 embedding 模型**：
95 MB 的模型每次从磁盘重新加载，既慢，又把并发窗口一直撑开。

## 裁定

**embedding 模型进程内只建一次并加锁；Chroma 包装对象照旧每次新建。**

- `agent/tools.py` 加模块级 `_embeddings` + `threading.Lock`，暴露 `get_embeddings()`，
  双检锁。`_get_chroma()` 改用它，不再自己建模型。
- `eval/run_eval.py` 的 `eval_rag` 复用同一个 `get_embeddings()`：一个评测进程里
  只加载一次模型，测的也就是 agent 实际用的那个 dense 检索器。
- **不缓存 Chroma 包装对象**：新建一个 Chroma 只是拿一个集合句柄，chromadb 内部
  按路径共享底层 system；缓存它会让"重灌知识库后服务端还拿着旧集合"这类问题更难查。
- 配套两条回归单测（`tests/test_tools.py`）：模型只建一次、并发取集合不炸。

## 后果

- 评测进程不再被并发加载打断，三个指标能真正测出数字。
- 工具调用从"每次重载 95 MB 模型"变成"第一次加载，之后复用"，评测快一大截。
- **约束推广**：本仓任何在多线程里加载 transformers 模型的代码，都必须复用同一个
  实例，不要每次 `from_pretrained`。LangGraph 的工具并发是常态，不是例外。
- 代价：模型常驻内存（95 MB，CPU float32），进程退出才释放。
- 这条只是绕开 transformers 的上游 bug，不是修它。上游修好之前别把这层缓存删掉。
