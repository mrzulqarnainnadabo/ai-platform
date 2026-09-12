# Notion as a second engine (not the authority plane)

Notion is valuable for **human coordination and narrative workspace**.
It must **not** replace:

- Supabase Auth / JWT claims
- deterministic authorization
- Case / Evidence / Audit as system of record
- provider credentials or model execution

## Recommended split

| Concern | System of record | Notion role |
|--------|------------------|-------------|
| Login / tenant / capabilities | Supabase + AI Platform | None |
| Case, assertions, evidence, audit | AI Platform DB (Postgres) | **Mirror / brief** only |
| Model triage / generate | AuthorizedModelRuntime | None |
| Human case notes, meeting notes | Optional | Primary |
| Playbooks, SOPs, templates | Optional | Primary |
| Status board for operators | Derived feed | Kanban / database view |
| Public source of truth | Platform API | Never |

## Pattern: Platform writes → Notion reflects

1. Platform creates/updates a **Case**.
2. A **server-side** worker (capability-gated) upserts a Notion page/row:
   - Case ID, title, status, tenant label (not secrets)
   - Link back to platform case id
   - Checklist of missing evidence questions
3. Humans edit **Notion-only** fields (discussion, owner assignment narrative).
4. Official state transitions (`open → in_progress → resolved`) remain **platform API** calls.

## What Notion must never do

- Grant `case.*` or `model.*` capabilities
- Store OpenAI/xAI keys
- Be treated as evidence provenance without copying content into platform Evidence with source refs
- Accept client-side Notion tokens that can mutate production case tables

## Minimal Notion data model (operator workspace)

- **Cases** database: `platform_case_id`, `title`, `status`, `tenant`, `url`
- **Evidence queue**: items still missing, linked to case
- **Playbooks**: “medicine stockout”, “water outage”, etc. (human process, not policy engine)

## When to implement

After durable Postgres case storage exists.
Notion integration is an **adapter**, same spirit as `EvidenceIngestionPort`—outside `ai_platform` core.
