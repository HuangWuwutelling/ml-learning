# ADR-0006 · 推 GitHub 只推选定的那一笔

- 状态: superseded（ADR-0024 取代）
- 登记日期: 2026-11-01
- 决策日期: 2026-11-01

## 约束

主仓 main 上混着三类 commit：简历主项目、准备公开的副线项目（Rust / QMS / PowerBI）、
以及本机专用内容。其中有些还没准备好公开。

## 裁定

**push 之前先确认这次要推哪些 commit**，用临时分支 + cherry-pick 推出选定的那一笔，
再合并回 main。一次只推一组，不整条 main 一起推。

## 后果

main 与 origin/main 之间会出现 ahead 差距，这是有意的，不是忘了推。
国内网络需要临时设 git proxy，推完取消：

```bash
git config --global http.proxy http://127.0.0.1:7897 && git push && git config --global --unset http.proxy
```

## 后续（2026-11-07）

ADR-0024 把边界从「挑 commit」改成「挑跟踪集」：副线项目移出索引，`.gitignore`
用白名单表达公开范围，`main` 的跟踪集直接等于 GitHub 上的内容。临时分支 +
cherry-pick 这套流程不再需要，本文由 ADR-0024 取代，保留作记录。
