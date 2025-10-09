import pytest


@pytest.mark.asyncio
async def test_generate_response_invalid_messages_streaming_error_generator():
    from core.chat_engine import ChatEngine

    engine = ChatEngine()
    gen = await engine.generate_response(messages=None, conversation_id='cid', stream=True)
    outs = []
    async for item in gen:
        outs.append(item)
    assert outs and outs[0]['finish_reason'] == 'error'


@pytest.mark.asyncio
async def test_generate_response_missing_required_fields_streaming():
    from core.chat_engine import ChatEngine

    engine = ChatEngine()
    # message without role/content
    gen = await engine.generate_response(messages=[{'text': 'hi'}], conversation_id='cid', stream=True)
    outs = []
    async for item in gen:
        outs.append(item)
    assert outs and outs[0]['finish_reason'] == 'error'


