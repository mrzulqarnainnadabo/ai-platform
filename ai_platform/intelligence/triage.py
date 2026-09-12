"""Deterministic validation of model-suggested triage output."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .models import AssertionKind


@dataclass(frozen=True)
class ParsedTriage:
    assertions: list[dict]
    missing_evidence_questions: list[str]


def _json_payload(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE | re.DOTALL).strip()
    try:
        value = json.loads(text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Model triage output is not valid JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("Model triage output must be a JSON object")
    return value


def parse_triage_output(text: str) -> ParsedTriage:
    payload = _json_payload(text)
    raw_assertions = payload.get("assertions", [])
    raw_questions = payload.get("missing_evidence_questions", [])
    if not isinstance(raw_assertions, list) or not isinstance(raw_questions, list):
        raise ValueError("Invalid triage shape")

    assertions: list[dict] = []
    for raw in raw_assertions[:20]:
        if not isinstance(raw, dict):
            continue
        statement = raw.get("text")
        kind = raw.get("kind")
        if not isinstance(statement, str) or not statement.strip() or len(statement.strip()) > 2000:
            continue
        try:
            parsed_kind = AssertionKind(kind)
        except (TypeError, ValueError):
            continue
        # A model cannot establish a fact because no evidence is linked during triage.
        if parsed_kind == AssertionKind.FACT:
            continue
        assertions.append({"text": statement.strip(), "kind": parsed_kind})

    questions = []
    for raw in raw_questions[:20]:
        if isinstance(raw, str) and raw.strip():
            question = raw.strip()
            if len(question) <= 500:
                questions.append(question)
    return ParsedTriage(assertions=assertions, missing_evidence_questions=questions)
