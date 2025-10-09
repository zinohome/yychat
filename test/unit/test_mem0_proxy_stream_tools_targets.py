import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_response_handler_stream_with_tool_calls():
    from core.mem0_proxy import ResponseHandler
    from config.config import get_config

    rh = ResponseHandler(get_config())

    # Build a streaming response with tool_calls then finish
    class ToolCall:
        def __init__(self):
            self.index = 0
            self.id = None
            self.function = type('F', (), {'name':'calc', 'arguments':'{"x":1}'})()

    class Delta:
        def __init__(self, tool_calls=None, content=None):
            self.tool_calls = tool_calls
            self.content = content

    class Choice:
        def __init__(self, delta, finish_reason=None):
            self.delta = delta
            self.finish_reason = finish_reason

    async def stream_gen():
        yield type('Chunk', (), {'choices':[Choice(Delta([ToolCall()]))]})()
        yield type('Chunk', (), {'choices':[Choice(Delta(None), finish_reason='stop')]})()

    client = type('Client', (), {'chat': type('Ch', (), {'completions': type('Co', (), {'create': lambda **kw: stream_gen()})()})()})()

    # Tool handling returns content which will be re-streamed by handle_streaming_tool_calls
    rh.tool_handler.handle_tool_calls = AsyncMock(return_value={'content': 'xyz'})

    outs = []
    async for item in rh.handle_streaming_response(client, {}, 'cid', [{'role':'user','content':'q'}]):
        outs.append(item)
    # Expect streamed output from tool follow-up
    assert any(i.get('content') for i in outs)


