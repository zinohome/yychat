import types
import pytest
from unittest.mock import MagicMock


@pytest.mark.asyncio
async def test_streaming_chunk_splitting_with_punctuation():
    from core.chat_engine import ChatEngine

    engine = ChatEngine()

    long_text = ("这是一个很长的段落，包含标点。" * 10) + "结束。"
    chunk = types.SimpleNamespace(
        choices=[types.SimpleNamespace(delta=types.SimpleNamespace(content=long_text))]
    )

    async def gen():
        yield chunk

    engine.client.create_chat_stream = MagicMock(return_value=gen())

    out = []
    async for item in engine._generate_streaming_response(
        {"messages": [{"role": "user", "content": "q"}]}, "cid", [{"role": "user", "content": "q"}]
    ):
        out.append(item)

    # Should emit multiple chunks since content is long with punctuation
    assert len([i for i in out if i.get('content')]) > 1


@pytest.mark.asyncio
async def test_streaming_chunk_splitting_fixed_length_no_punctuation():
    from core.chat_engine import ChatEngine

    engine = ChatEngine()

    long_text = "x" * 250  # no punctuation
    chunk = types.SimpleNamespace(
        choices=[types.SimpleNamespace(delta=types.SimpleNamespace(content=long_text))]
    )

    async def gen():
        yield chunk

    engine.client.create_chat_stream = MagicMock(return_value=gen())

    out = []
    async for item in engine._generate_streaming_response(
        {"messages": [{"role": "user", "content": "q"}]}, "cid", [{"role": "user", "content": "q"}]
    ):
        out.append(item)

    # Expect at least 3 chunks for 250 length with 100-slice splitting
    emitted = [i for i in out if i.get('content')]
    assert len(emitted) >= 3


