"""真起一次 stdio server，证明 README 里写的启动命令能用。

这条测试是有来历的：`server/mcp_server.py` 起初用相对 import（`from . import rules`），
按 README 的 `python server/mcp_server.py` 跑直接 ImportError，而进程内调的评测全绿，
看不出来。所以这里必须走子进程 + 真的 stdio 客户端。
"""
import asyncio
import json
import logging
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVER = PROJECT_ROOT / 'server' / 'mcp_server.py'

# MCP SDK 自己打的 INFO 日志会把测试输出刷满
logging.getLogger('mcp').setLevel(logging.WARNING)


def _call_all():
    """起 server、连客户端、调三个工具，返回 {工具名: 解析后的返回}。"""
    async def run():
        params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
        out = {}
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                out['_tools'] = [t.name for t in tools.tools]
                for name, args in (
                    ('screen_result', {'pollutant': '镉', 'measured': 60,
                                       'land_type': '第一类用地'}),
                    ('get_limits', {'pollutant': '芴', 'land_type': '第二类用地'}),
                    ('get_background_value', {'element': '砷', 'soil_type': '水稻土'}),
                ):
                    resp = await session.call_tool(name, args)
                    assert not resp.isError, '%s 返回错误：%s' % (name, resp.content[0].text)
                    out[name] = json.loads(resp.content[0].text)
        return out

    return asyncio.run(run())


@pytest.fixture(scope='module')
def stdio_out():
    """整个模块只起一次 server。"""
    return _call_all()


def test_server_starts_over_stdio(stdio_out):
    assert stdio_out['_tools'] == ['search_items', 'get_limits', 'screen_result',
                                    'screen_batch', 'get_background_value']


def test_screening_result_over_stdio(stdio_out):
    payload = stdio_out['screen_result']
    assert payload['pollutant'] == '镉'
    assert payload['tier'] == 'control_or_remediation'
    assert payload['screening_value'] == 20
    assert payload['control_value'] == 47


def test_limits_over_stdio(stdio_out):
    payload = stdio_out['get_limits']
    assert payload['pollutant'] == '芴'
    assert payload['screening_value'] == 1293
    assert payload['control_value'] == 12900


def test_background_over_stdio(stdio_out):
    assert stdio_out['get_background_value']['background_value'] == 40
