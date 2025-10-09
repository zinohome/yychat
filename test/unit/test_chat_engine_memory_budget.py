import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_generate_response_memory_budget_exclusion():
    from core.chat_engine import ChatEngine

    engine = ChatEngine()

    # Mock async memory retrieval to return non-empty
    engine.async_chat_memory.get_relevant_memory = AsyncMock(return_value=["mem1", "mem2"])

    # Force should_include_memory to False to exclude memory section
    with patch('core.chat_engine.should_include_memory', return_value=False):
        captured = {}

        def fake_build_request_params(**kwargs):
            captured['messages'] = kwargs.get('messages')
            return {'messages': kwargs.get('messages')}

        with patch('core.chat_engine.build_request_params', side_effect=lambda **kw: fake_build_request_params(**kw)):
            # Mock client response normal (no tool calls)
            msg = type('M', (), {'content': 'ok', 'tool_calls': None})()
            resp = type('R', (), {'choices': [type('C', (), {'message': msg})()], 'usage': None, 'model': 'm'})()
            engine.client.create_chat = AsyncMock(return_value=resp)

            out = await engine.generate_response(
                messages=[{"role":"user","content":"q"}],
                conversation_id='c1',
                personality_id=None,
                use_tools=False,
                stream=False
            )

    # Ensure content returned
    assert out.get('content') == 'ok'
    # Ensure memory text "参考记忆" not added into composed messages
    messages = captured.get('messages', [])
    assert not any(isinstance(m.get('content'), str) and '参考记忆' in m.get('content') for m in messages if isinstance(m, dict))


