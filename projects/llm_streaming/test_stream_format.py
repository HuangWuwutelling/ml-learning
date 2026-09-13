"""Test stream.py output format. Run: python test_stream_format.py"""
import asyncio
from stream import format_sse_from


def test_sse_format_empty():
    """空字符串不输出 chunk（filter 掉 padding）。"""
    async def empty_gen():
        for tok in ["", "hi", "", "ok"]:
            yield tok
    out = []
    async def run():
        async for c in format_sse_from("", empty_gen()):
            out.append(c)
    asyncio.run(run())
    assert out == ["data: hi\n\n", "data: ok\n\n"]


if __name__ == "__main__":
    test_sse_format_empty()
    print("OK: stream format tests passed")
