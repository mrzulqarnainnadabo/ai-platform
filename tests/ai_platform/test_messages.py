"""Tests for Message, Role, ContentPart, ToolCall, and ToolResult Contracts."""

import json
import unittest

from ai_platform.core.messages import (
    ContentPart,
    Message,
    Role,
    ToolCall,
    ToolResult,
)


class TestMessageContracts(unittest.TestCase):
    """Tests message creation, multimodal content, tool calls, serialization, and input validation."""

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

    def test_multimodal_content_and_binary_roundtrip(self) -> None:
        binary_payload = b"\x00\x01\x02\x03\xff\xfe\xfd"
        part_text = ContentPart(type="text", text="Look at audio and image")
        part_img = ContentPart(type="image_url", image_url="https://example.com/image.png")
        part_bin = ContentPart(type="binary", data=binary_payload, mime_type="application/octet-stream")

        msg = Message(role=Role.USER, content=[part_text, part_img, part_bin])
        json_str = msg.to_json()

        restored = Message.from_json(json_str)
        self.assertIsInstance(restored.content, list)
        self.assertEqual(len(restored.content), 3)
        self.assertEqual(restored.content[2].data, binary_payload)
        self.assertEqual(restored.content[2].mime_type, "application/octet-stream")

    def test_invalid_role_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            Message(role="invalid_role", content="hello")

        with self.assertRaises(ValueError):
            Message.from_dict({"role": "superadmin", "content": "hello"})

    def test_missing_content_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            Message(role=Role.USER, content=None)

        with self.assertRaises(ValueError):
            Message.from_dict({"role": "user"})

    def test_invalid_tool_call_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            ToolCall(id="", name="search", arguments={})

        with self.assertRaises(ValueError):
            ToolCall.from_dict({"id": "call-1", "name": ""})

    def test_invalid_tool_result_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            ToolResult(tool_call_id="", content="result")

        with self.assertRaises(ValueError):
            ToolResult.from_dict({"content": "result"})


if __name__ == "__main__":
    unittest.main()
