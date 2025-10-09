import pytest
from unittest.mock import MagicMock


@pytest.mark.asyncio
async def test_response_handler_non_stream_message_content_none():
    from core.mem0_proxy import ResponseHandler
    from config.config import get_config

    rh = ResponseHandler(get_config())
    msg = type('M', (), {'tool_calls': None, 'content': None})()
    resp = type('R', (), {'choices': [type('C', (), {'message': msg})()]})()

    out = await rh.handle_non_streaming_response(
        client=type('Client', (), {'chat': type('Ch', (), {'completions': type('Co', (), {'create': lambda **kw: resp})()})()})(),
        call_params={},
        conversation_id='cid',
        original_messages=[{'role':'user','content':'q'}]
    )
    # Fallback is to return role assistant with empty content
    assert out.get('role') == 'assistant'
    assert isinstance(out.get('content', ''), str)
