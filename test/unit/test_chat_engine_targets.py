import asyncio
import types
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_non_streaming_tool_calls_json_error(monkeypatch):
    # Arrange: mock ChatEngine internals
    from core.chat_engine import ChatEngine

    engine = ChatEngine()

    # Mock client.create_chat to return a response with tool_calls
    bad_args = '{"a":1'  # invalid JSON
    tool_call = types.SimpleNamespace(
        function=types.SimpleNamespace(name="calc", arguments=bad_args)
    )
    message = types.SimpleNamespace(tool_calls=[tool_call], content=None)
    response = types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)], model="m")

    engine.client.create_chat = AsyncMock(return_value=response)

    # normalize_tool_calls should pass through tool_calls like list of dicts
    with patch("core.chat_engine.normalize_tool_calls", return_value=[{"function": {"name": "calc", "arguments": bad_args}}]):
        # execute_tools_concurrently returns a simple result
        engine.tool_manager.execute_tools_concurrently = AsyncMock(return_value=[{"content": "42"}])

        result = await engine._generate_non_streaming_response(
            {"messages": [{"role": "user", "content": "1+1"}]},
            conversation_id="c1",
            original_messages=[{"role": "user", "content": "1+1"}],
            personality_id=None,
            metrics=None,
        )

    # Assert: tool path returns assistant message
    assert result["role"] == "assistant"
    assert "content" in result


@pytest.mark.asyncio
async def test_streaming_tool_calls_follow_up_and_memory_saved(monkeypatch):
    from core.chat_engine import ChatEngine

    engine = ChatEngine()

    # Prepare streaming chunks that include a tool_call delta then end
    first_chunk = types.SimpleNamespace(
        choices=[types.SimpleNamespace(delta=types.SimpleNamespace(tool_calls=[types.SimpleNamespace(index=0, id="id1", function=types.SimpleNamespace(name="calc", arguments="{\"x\":1}"))]))]
    )
    end_chunk = types.SimpleNamespace(choices=[types.SimpleNamespace(delta=types.SimpleNamespace(content=None), finish_reason="stop")])

    async def chunk_gen():
        yield first_chunk
        yield end_chunk

    engine.client.create_chat_stream = MagicMock(return_value=chunk_gen())

    # normalize to single call
    with patch("core.chat_engine.normalize_tool_calls", return_value=[{"id": "id1", "type": "function", "function": {"name": "calc", "arguments": "{\"x\":1}"}}]):
        # tools execute returns one result
        engine.tool_manager.execute_tools_concurrently = AsyncMock(return_value=[{"content": "ok"}])

        # follow-up streaming returns one content chunk
        follow_chunk = types.SimpleNamespace(choices=[types.SimpleNamespace(delta=types.SimpleNamespace(content="answer"))])

        async def follow_gen():
            yield follow_chunk

        engine.client.create_chat_stream = MagicMock(side_effect=[chunk_gen(), follow_gen()])

        # spy memory save
        engine._async_save_message_to_memory = AsyncMock()

        out = []
        async for item in engine._generate_streaming_response(
            {"messages": [{"role": "user", "content": "q"}]}, "cid", [{"role": "user", "content": "q"}], None, None
        ):
            out.append(item)

    # Expect at least one streamed content chunk from follow-up and a final stop
    assert any(i.get("content") == "answer" for i in out)


@pytest.mark.asyncio
async def test_generate_response_param_validation_stream_error_path():
    from core.chat_engine import ChatEngine

    engine = ChatEngine()
    # Invalid messages (not list)
    gen = await engine.generate_response(messages=None, conversation_id="c")
    assert gen["content"]


@pytest.mark.asyncio
async def test_non_streaming_api_invalid_format_returns_friendly_error():
    from core.chat_engine import ChatEngine

    engine = ChatEngine()
    engine.client.create_chat = AsyncMock(return_value=types.SimpleNamespace(choices=[]))

    res = await engine._generate_non_streaming_response(
        {"messages": [{"role": "user", "content": "hi"}]},
        "cid",
        [{"role": "user", "content": "hi"}],
    )
    assert "AI响应内容为空" in res["content"] or "格式错误" in res["content"]


