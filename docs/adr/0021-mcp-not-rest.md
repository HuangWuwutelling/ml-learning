# ADR-0021 · 标准查询对外用 MCP server，不用 REST

- 状态: accepted
- 登记日期: 2026-11-04
- 决策日期: 2026-11-04

## 约束

`projects/env_standards_mcp/` 要把查标准的能力交给 AI agent 用。有两条路：

- REST：起 HTTP 服务，写 OpenAPI，agent 用通用 HTTP 工具去调
- MCP：起 MCP server，把「查限值」「定档」注册成工具，agent 用 MCP 客户端去调

约束有三条：

1. **消费方主要是 AI agent**，不是一个前端页面。人用的话做个网页更合适，
   但这个项目没有网页。
2. **本地多标准查询 MCP server（⑤ 前沿 PoC）** 是目标岗位 JD 明确列出的方向，
   而本仓的作品集里没有 MCP 项目（另三个主项目都是 Web / Django / 训练脚本）。
3. **能力是「几个语义明确的操作」**，不是「一堆资源」。查限值、给测值定档、
   查背景值、搜项目名、批量定档——每个都有明确的入参和出参。

## 裁定

**对外只暴露 MCP server（stdio 传输），不同时做 REST。**

- 五个工具：`search_items` / `get_limits` / `screen_result` / `screen_batch` /
  `get_background_value`。工具描述写给 agent 看，参数名用领域词（`pollutant`、
  `measured`、`land_type`、`soil_type`），不用内部词（`item_key`、`value`、`type`）。
- 另外挂一个 resource `env-standards://gb36600/limits` 给想读全表的人或程序。
- **评测走真的 MCP 通道**：`eval/run_eval.py` 起 server、连客户端、`call_tool` 发请求，
  不是直接调 Python 函数。这样测的是 agent 实际会用到的那一面，
  不是「函数返回对了但工具没挂上」。
- **不做的事**：不提供 REST 端点，不做鉴权，不做多租户。这个 server 是本机跑的，
  挂给本机的 agent 用。

## 后果

- 作品集里第一次有 MCP 项目，且接的是真领域数据（国标限值），不是玩具 demo。
- 评测覆盖到协议层：工具挂了、描述写坏了、参数名不对，都会被用例测出来。
- **stdio 传输只适合本机**。要给同事用、要挂到远端 agent，得换 streamable-http，
  那时再加鉴权——现在不做，是避免造一个没人用的鉴权层。
- MCP 工具的入参是模型生成的，不像函数调用那样有编译器保证类型，
  所以 `rules.py` 对认不出来的输入一律报错而不是猜（见 ADR-0019）。
- 想再支持别的客户端（比如给 Django 项目调），那时再补一个薄的 HTTP 包装，
  不为了「以后可能用」先把 REST 写出来。
