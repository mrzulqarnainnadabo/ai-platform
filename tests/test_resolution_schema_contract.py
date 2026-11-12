"""Static contract checks for the durable resolution migration.

These tests intentionally avoid requiring a live Supabase database. They protect
critical governance invariants while the durable repository adapter is added.
"""
from pathlib import Path


MIGRATION = Path(__file__).parents[1] / "supabase" / "migrations" / "0009_intelligence_resolution.sql"


def test_resolution_schema_contains_governance_entities_and_rls():
    sql = MIGRATION.read_text(encoding="utf-8")
    for table in (
        "ai_platform_responsibilities",
        "ai_platform_action_proposals",
        "ai_platform_commitments",
        "ai_platform_outcomes",
        "ai_platform_resolution_events",
    ):
        assert f"create table if not exists public.{table}" in sql
        assert f"alter table public.{table} enable row level security" in sql
        assert f"revoke all on public.{table} from anon, authenticated, public" in sql


def test_resolution_schema_blocks_unverified_outcomes_and_event_mutation():
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "status <> 'verified' or jsonb_array_length(evidence_ids) > 0" in sql
    assert "Resolution events are append-only" in sql
    assert "before update or delete on public.ai_platform_resolution_events" in sql
