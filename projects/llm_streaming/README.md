# LLM 流式输出演示

配套文章：公众号「为什么 ChatGPT 是一个字一个字蹦出来：LLM 流式输出的本质与拼装」（#17）。

## 跑起来

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
python app.py  # 启动 FastAPI，浏览器访问 http://localhost:8000
```

## bench

```bash
python bench.py  # 跑 20 题，记录 TTFT + TPOT 到 bench_results.json
```
