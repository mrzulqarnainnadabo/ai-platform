"""Tests for ModelConfig, ResponseFormat, and ToolDefinition Contracts."""

import unittest

from ai_platform.core.config import (
    ModelConfig,
    ResponseFormat,
    ResponseFormatType,
    ToolDefinition,
    ToolFunction,
)


class TestConfigContracts(unittest.TestCase):
    """Tests model configuration, structured output format, tool definitions, and contract validation."""

    def test_model_config_valid(self) -> None:
        cfg = ModelConfig(model_name="gpt-4o", temperature=0.5, top_p=0.9, max_tokens=1000)
        self.assertEqual(cfg.model_name, "gpt-4o")
        self.assertEqual(cfg.temperature, 0.5)

    def test_model_config_invalid_model_name_raises(self) -> None:
        with self.assertRaises(ValueError) as cm:
            ModelConfig(model_name="")
        self.assertIn("model_name cannot be empty", str(cm.exception))

        with self.assertRaises(ValueError):
            ModelConfig.from_dict({"model_name": "   "})

    def test_model_config_invalid_temperature_raises(self) -> None:
        with self.assertRaises(ValueError):
            ModelConfig(model_name="gpt-4o", temperature=-0.1)

        with self.assertRaises(ValueError):
            ModelConfig(model_name="gpt-4o", temperature=2.5)

    def test_model_config_invalid_top_p_raises(self) -> None:
        with self.assertRaises(ValueError):
            ModelConfig(model_name="gpt-4o", top_p=1.5)

    def test_model_config_invalid_max_tokens_raises(self) -> None:
        with self.assertRaises(ValueError):
            ModelConfig(model_name="gpt-4o", max_tokens=0)

    def test_model_config_invalid_timeout_raises(self) -> None:
        with self.assertRaises(ValueError):
            ModelConfig(model_name="gpt-4o", timeout_seconds=-5.0)

    def test_invalid_tool_function_raises(self) -> None:
        with self.assertRaises(ValueError):
            ToolFunction(name="", description="desc", parameters={})

        with self.assertRaises(ValueError):
            ToolFunction(name="test", description="desc", parameters="not_a_dict")

    def test_model_config_serialization(self) -> None:
        rf = ResponseFormat(
            type=ResponseFormatType.JSON_SCHEMA,
            json_schema={"type": "object", "properties": {"summary": {"type": "string"}}},
            schema_name="SummarySchema",
        )
        tool = ToolDefinition(
            type="function",
            function=ToolFunction(
                name="get_weather",
                description="Get weather for city",
                parameters={"type": "object", "properties": {"city": {"type": "string"}}},
            ),
        )

        cfg = ModelConfig(
            model_name="gemini-2.0-flash",
            temperature=0.2,
            max_tokens=2048,
            response_format=rf,
            tools=[tool],
        )

        json_str = cfg.to_json()
        restored = ModelConfig.from_json(json_str)
        self.assertEqual(restored.model_name, "gemini-2.0-flash")
        self.assertEqual(restored.tools[0].function.name, "get_weather")


if __name__ == "__main__":
    unittest.main()
