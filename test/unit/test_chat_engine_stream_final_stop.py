import types
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_streaming_tool_calls_emits_final_stop():
    from core.chat_engine import ChatEngine

    engine = ChatEngine()

    # First stream has tool_calls
    first_chunk = types.SimpleNamespace(
        choices=[types.SimpleNamespace(delta=types.SimpleNamespace(tool_calls=[types.SimpleNamespace(index=0, id=None, function=types.SimpleNamespace(name='calc', arguments='{"x":1}'))]))]
    )
    end_chunk = types.SimpleNamespace(choices=[types.SimpleNamespace(delta=types.SimpleNamespace(content=None), finish_reason='stop')])

    async def gen():
        yield first_chunk
        yield end_chunk

    # Follow-up stream yields content then ends
    fu_content = types.SimpleNamespace(choices=[types.SimpleNamespace(delta=types.SimpleNamespace(content='ok'), finish_reason=None)])

    async def fu_gen():
        yield fu_content

    engine.client.create_chat_stream = MagicMock(side_effect=[gen(), fu_gen()])

    with patch('core.chat_engine.normalize_tool_calls', return_value=[{"id":"tmp","type":"function","function":{"name":"calc","arguments":"{\"x\":1}"}}]):
        engine.tool_manager.execute_tools_concurrently = AsyncMock(return_value=[{"content":"r"}])
        out = []
        async for item in engine._generate_streaming_response({"messages":[{"role":"user","content":"q"}]}, 'cid', [{"role":"user","content":"q"}]):
            out.append(item)

    # After follow-up, there should be a final stop event with empty content
    assert any(i.get('finish_reason') == 'stop' for i in out)


