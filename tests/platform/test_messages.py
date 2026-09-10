"""Tests for Message, Role, ContentPart, ToolCall, and ToolResult Contracts."""

import unittest

from platform.core.messages import (
    ContentPart,
    Message,
    Role,
    ToolCall,
    ToolResult,
)


class TestMessageContracts(unittest.TestCase):
    """Tests message creation, multimodal content, tool calls, and serialization."""

    def test_plain_text_message(self) -> None:
        msg = Message(role=Role.USER, content="Hello AI Platform")
        self.assertEqual(msg.role, Role.USER)
        self.assertEqual(msg.get_text_content(), "Hello AI Platform")

        data = msg.to_dict()
        self.assertEqual(data["role"], "user")
        self.assertEqual(data["content"], "Hello AI Platform")

        restored = Message.from_dict(data)
        self.assertEqual(restored.role, Role.USER)
        self.assertEqual(restored.get_text_content(), "Hello AI Platform")

    def test_multimodal_message(self) -> None:
        msg = Message(
            role=Role.USER,
            content=[
                ContentPart(type="text", text="What is in this image?"),
                ContentPart(type="image_url", image_url="https://example.com/chart.png"),
            ],
        )
        self.assertEqual(msg.get_text_content(), "What is in this image?")

        json_str = msg.to_json()
        self.assertIn("chart.png", json_str)

        restored = Message.from_json(json_str)
        self.assertIsInstance(restored.content, list)
        self.assertEqual(len(restored.content), 2)
        self.assertEqual(restored.content[1].image_url, "https://example.com/chart.png")

    def test_tool_call_and_tool_result_messages(self) -> None:
        tc = ToolCall(id="call-123", name="search_documents", arguments={"query": "civic policy"})
        assistant_msg = Message(
            role=Role.ASSISTANT,
            content="Searching civic documents...",
            tool_calls=[tc],
        )
        self.assertEqual(assistant_msg.tool_calls[0].name, "search_documents")

        data = assistant_msg.to_dict()
        self.assertEqual(data["tool_calls"][0]["arguments"]["query"], "civic policy")

        tool_msg = Message(
            role=Role.TOOL,
            content="Document found: Policy 2026-B",
            tool_call_id="call-123",
        )
        self.assertEqual(tool_msg.role, Role.TOOL)
        self.assertEqual(tool_msg.tool_call_id, "call-123")


if __name__ == "__main__":
    unittest.main()
