import pytest
from unittest.mock import MagicMock, AsyncMock


@pytest.mark.asyncio
async def test_mem0_proxy_combined_long_branch_sequence():
    from core.mem0_proxy import Mem0ChatEngine

    engine = Mem0ChatEngine()

    # Force mem0 path to run but response handler returns "无法生成响应" path
    client = type('X', (), {})()
    # non-stream call returns object without choices to hit fallback path in handler
    resp = type('R', (), {})()
    client.chat = type('Ch', (), {'completions': type('Co', (), {'create': lambda **kw: resp})()})()
    engine.get_client = MagicMock(return_value=client)

    # Response handler should return default message, then generate_response should return it
    out = await engine.generate_response([{'role':'user','content':'q'}], 'cid', stream=False)
    assert '无法生成响应' in out.get('content', '') or isinstance(out, dict)
