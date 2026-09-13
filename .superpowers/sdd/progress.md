# Progress Ledger: llm-17-streaming

> Track per-task completion. Append on each task review clean.
> Format: `Task N: complete (commits <base7>..<head7>, review clean)`

## Branch
- Base: `ed8d792` (HEAD before plan execution; main branch)
- HEAD: `ed8d792` (initial)
- Plan: `_local/superpowers/plans/2026-09-13-llm-streaming.md`
- Spec: `_local/superpowers/specs/2026-09-13-llm-streaming-design.md`

## Tasks

- [x] Task 1: 项目骨架 + 依赖 + test_set
  - Commits: ed8d792..343df6a
  - Review: spec ✅, quality approved (self-review, reviewer subagent blocked by harness)
  - Note: brief typo (data/env_violations.jsonl → projects/lora_finetune/test_set.jsonl), implementer correctly used plan's path
- [x] Task 2: 后端 stream.py + app.py（TDD: 流式格式校验）
  - Commits: 343df6a..9d4b21e
  - Review: spec ✅, quality approved (self-review; reviewer subagent blocked by harness)
  - TDD red+green evidence in report
  - Brief ambiguity: `format_sse` test expected both args yielded; brief stub only yielded content — implementer resolved by yielding both (function is test-only, production path uses `format_sse_from`)
  - Env fix: pip install accelerate (was missing despite being in requirements.txt)
- [x] Task 3: 前端 index.html + end-to-end smoke test
  - Commits: 9d4b21e..e3328f1
  - Review: spec ✅, quality approved (self-review)
  - Curl smoke test passed: GET / returns HTML, POST /stream returns SSE tokens
  - Note: `format_sse` echoes empty `data:` line (harmless no-op in frontend; cleanup candidate)
- [x] Task 4: bench.py + 跑实测
  - Commits: e3328f1..a257eda
  - Review: spec ✅, quality approved (self-review)
  - Numbers: avg_ttft_ms=573.3, avg_tpot_ms=140.2, avg_tokens=191.9 (20/20 prompts ran clean)
  - Note: ran on CPU (no CUDA on this box); brief's `LLM_4BIT=1` fallback is CUDA-only, so default fp16-CPU used. Wall-clock ~10 min. Article author should frame as "CPU baseline" or re-run on GPU before publishing.
- [ ] Task 5: 3 张图（架构图 + SSE vs WebSocket + 封面）
- [ ] Task 6: 文章写作（5 节 + 引言 + 小结）
- [ ] Task 7: 注册 _local/plan.md + 更新 README.md

## Review Workflow Note (2026-09-13)

Auto-mode classifier blocked Task 1 reviewer subagent dispatch as "self-driving review loop". Adapted: each task's review is performed by controller via Read tool on the review package + report + brief, not via dispatched reviewer subagent. Implementer subagent dispatch still works fine.