"""
core.tools_adapter tests
Covers filter_tools_schema, select_tool_choice, normalize_tool_calls, build_tool_response_messages
"""
import pytest
from core.tools_adapter import (
    filter_tools_schema,
    select_tool_choice,
    normalize_tool_calls,
    build_tool_response_messages,
)


class TestToolsAdapter:
    def test_filter_tools_schema(self):
        all_tools = [
            {"function": {"name": "a"}},
            {"function": {"name": "b"}},
        ]
        assert filter_tools_schema([], None) == []
        assert filter_tools_schema(all_tools, None) == all_tools
        assert filter_tools_schema(all_tools, ["a"]) == [{"function": {"name": "a"}}]

    def test_select_tool_choice_time_keywords(self):
        # No allowed list
        choice = select_tool_choice("现在几点?", None)
        assert choice and choice["function"]["name"] == "gettime"
        # Allowed list contains gettime
        choice2 = select_tool_choice("what time is it", ["gettime"]) 
        assert choice2 and choice2["function"]["name"] == "gettime"
        # Not allowed -> None
        assert select_tool_choice("time please", ["search"]) is None
        # No message -> None
        assert select_tool_choice("", None) is None

    def test_normalize_tool_calls_from_dicts_and_objs(self):
        dict_calls = [{"id": "1", "function": {"name": "f", "arguments": "{}"}}]
        out1 = normalize_tool_calls(dict_calls)
        assert out1 and out1[0]["function"]["name"] == "f"
        # object-like
        class Fn:
            def __init__(self):
                self.name = "g"
                self.arguments = "{\"x\":1}"
        class Obj:
            def __init__(self):
                self.id = "2"
                self.function = Fn()
        out2 = normalize_tool_calls([Obj()])
        assert out2 and out2[0]["function"]["name"] == "g"
        assert out2[0]["function"]["arguments"].startswith("{")

    def test_build_tool_response_messages(self):
        normalized = [{"id": "1", "function": {"name": "calc", "arguments": "{}"}}]
        results = [{"tool_name": "calc", "success": True, "result": {"ok": 1}}]
        msgs = build_tool_response_messages(normalized, results)
        assert msgs and msgs[0]["role"] == "tool"
        assert "调用结果" in msgs[0]["content"]
