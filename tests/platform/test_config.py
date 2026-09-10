"""Tests for ModelConfig, ResponseFormat, and ToolDefinition Contracts."""

import unittest

from platform.core.config import (
    ModelConfig,
    ResponseFormat,
    ResponseFormatType,
    ToolDefinition,
    ToolFunction,
)


class TestConfigContracts(unittest.TestCase):
    """Tests model configuration, structured output format, and tool definitions."""

    def test_model_config_defaults(self) -> None:
        cfg = ModelConfig(model_name="gpt-4o")
        self.assertEqual(cfg.model_name, "gpt-4o")
        self.assertEqual(cfg.temperature, 0.7)
        self.assertEqual(cfg.timeout_seconds, 60.0)

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
            extra_params={"seed": 42},
        )

        json_str = cfg.to_json()
        self.assertIn("gemini-2.0-flash", json_str)
        self.assertIn("get_weather", json_str)
        self.assertIn("SummarySchema", json_str)

        restored = ModelConfig.from_json(json_str)
        self.assertEqual(restored.model_name, "gemini-2.0-flash")
        self.assertEqual(restored.temperature, 0.2)
        self.assertEqual(restored.response_format.type, ResponseFormatType.JSON_SCHEMA)
        self.assertEqual(restored.tools[0].function.name, "get_weather")
        self.assertEqual(restored.extra_params["seed"], 42)


if __name__ == "__main__":
    unittest.main()
