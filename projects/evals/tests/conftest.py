"""三个简历主项目的契约测试脚手架。

设计原则（来自 ADR-0015）：

1. **只读**。三个主项目已定稿（`环境法律法规智能问答系统/`、`projects/env_agent/`、
   `projects/lora_finetune/`），本目录不往它们里面写任何文件。
2. **不 import 业务模块**。`import tools` 会拉起 langchain_core，`import eval` 会拉起
   torch 和 transformers。契约测试要在一台只装了 pytest 的机器上也跑得动，
   所以这里一律用 `ast` 解析源码、用 `json` 读产物。
3. **验口径，不验智能**。契约要钉住的是「评测集有几条、id 怎么排、默认档位是哪个、
   README 里的数字和产物对不对得上」。模型答得好不好由各自的 eval 脚本负责
   （`projects/env_agent/eval_agent.py`、`projects/lora_finetune/eval.py`）。

路径一律从本文件位置推，不依赖当前工作目录。
"""
import ast
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RAG_DIR = REPO_ROOT / "环境法律法规智能问答系统"
AGENT_DIR = REPO_ROOT / "projects" / "env_agent"
LORA_DIR = REPO_ROOT / "projects" / "lora_finetune"


# ── 读文件 ─────────────────────────────────────────────────────────────────

def read_text(path) -> str:
    return Path(path).read_text(encoding="utf-8")


def read_json(path):
    return json.loads(read_text(path))


def read_jsonl(path):
    """读 jsonl，跳过空行。"""
    records = []
    for line in read_text(path).splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


# ── 从源码里取值（不 import） ──────────────────────────────────────────────

def env_default(source: str, name: str) -> str:
    """取 `os.getenv(NAME, "default")` 里的默认字面量。

    取源码里的默认值而不是 import 模块后的值：本机 `.env` 或环境变量不该影响断言，
    否则测试结果随开发机的配置变，就不是契约了。
    """
    m = re.search(rf'os\.getenv\(\s*"{re.escape(name)}"\s*,\s*"([^"]*)"', source)
    assert m, f'源码里找不到 {name} 的 os.getenv 默认值'
    return m.group(1)


def _literal(node, env):
    """把 AST 节点求成 Python 值，能解析对同模块常量的引用。"""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_literal(e, env) for e in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_literal(e, env) for e in node.elts)
    if isinstance(node, ast.Dict):
        out = {}
        for key, value in zip(node.keys, node.values):
            assert key is not None, 'dict 解包写法不支持'
            out[_literal(key, env)] = _literal(value, env)
        return out
    if isinstance(node, ast.Name):
        assert node.id in env, f'源码里引用了未解析的常量 {node.id}'
        return env[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_literal(node.operand, env)
    raise AssertionError(f'暂不支持的字面量节点: {type(node).__name__}')


def module_literal(path, name):
    """取模块顶层的 `NAME = <字面量>`，支持引用同模块的其他常量。

    例如 `eval_agent.py` 里 `CASES` 有一条 `"avoid": ALL_TOOLS`，`ALL_TOOLS` 是同模块
    的常量。`ast.literal_eval` 直接跑会抛 `malformed node or string`，
    所以这里先把模块顶层的字面量常量收成 env，再逐个节点解析。
    """
    tree = ast.parse(read_text(path))
    env = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        env[target.id] = ast.literal_eval(node.value)
                    except (ValueError, TypeError):
                        pass
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return _literal(node.value, env)
    raise AssertionError(f'{path} 里找不到顶层常量 {name}')


def module_functions(path):
    """取模块顶层函数的 {名字: 参数名列表}。"""
    tree = ast.parse(read_text(path))
    funcs = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            funcs[node.name] = args
    return funcs


def decorated_functions(path, decorator_name):
    """取被指定装饰器（如 `@tool`）标记的函数名集合。"""
    tree = ast.parse(read_text(path))
    found = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            name = dec.id if isinstance(dec, ast.Name) else getattr(dec, 'attr', None)
            if name == decorator_name:
                found.add(node.name)
    return found
