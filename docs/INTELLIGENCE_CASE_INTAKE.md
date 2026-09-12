# Intelligence Layer — Case Intake

## Why this is not a chatbot

The case-intake slice turns an unstructured real-world problem report into a governed case record. It preserves the distinction between what was reported, what the model suggests, and what has evidence. It also records an audit event for every state-changing operation.

The current loop is:

`Problem → Case → Assertions → Missing Evidence → Evidence → Audit`

The model is a reasoning assistant, not the system of record and not institutional authority.

## Entities

- **Case** — tenant-scoped problem record with lifecycle status.
- **Assertion** — a statement associated with a case and classified as `fact`, `claim`, `inference`, or `unknown`.
- **Evidence** — immutable v1 provenance record containing body/text and source metadata.
- **AuditEvent** — append-only event with a SHA-256 payload digest and no secrets.

During model triage, `fact` assertions are rejected because the model has not established evidence. Triage can produce `claim`, `inference`, or `unknown` assertions and missing-evidence questions.

## API

All endpoints require an authenticated Supabase JWT with trusted capability claims.

### Create a case

`POST /api/v1/cases`

```json
{
  "title": "Community health centre medicine shortage",
  "summary": "Residents report that the health centre has been without essential medicines for three months."
}
```

Case creation requires `case.create`. The creation response does not require a separate `case.read` capability.

### Read a case

`GET /api/v1/cases/{id}`

Returns the case, assertions, evidence, missing-evidence questions, and audit events. Requires `case.read` and tenant ownership.

### Triage a case

`POST /api/v1/cases/{id}/triage`

The server invokes `AuthorizedModelRuntime` only after `case.triage` and `model.generate` are authorized. The model receives a strict JSON schema and untrusted case text; deterministic validation rejects malformed output and any model-suggested `fact` assertion without evidence.

The triage model is selected server-side with `AI_PLATFORM_TRIAGE_MODEL` and is never supplied by the client.

### Attach evidence

`POST /api/v1/cases/{id}/evidence`

```json
{
  "body": "Stock register excerpt supplied by the reporter",
  "source_type": "document_ref",
  "source_uri": "document:stock-record-1",
  "note": "Provided during intake",
  "assertion_id": "optional-assertion-id"
}
```

For `url` and `document_ref`, a non-blank `source_uri` is required.

## Evidence ingestion boundary

The first-party `EvidenceIngestionPort` defines the future adapter boundary for text, URLs, PDF/DOCX, images, audio, and video. The vertical slice intentionally ships only a safe text passthrough adapter.

Future engines such as document parsing, OCR, speech transcription, media extraction, and local model services must sit behind adapters and must not become domain dependencies. They also must not receive provider credentials from clients.

## Security invariants

1. Supabase JWT claims are the only source of identity, tenant, and capabilities.
2. Client request bodies cannot grant permissions or change tenant identity.
3. Case access is tenant-isolated.
4. Each case operation requires its explicit capability.
5. A denied triage request is rejected before provider configuration/model execution.
6. Model calls happen only through `AuthorizedModelRuntime`.
7. Model output cannot establish a `fact` without linked evidence.
8. Evidence is append-only at the database layer and cannot be updated or deleted by the integrity trigger.
9. Audit events are append-only at the database layer and contain digests/metadata, never provider secrets.
10. Child records carry tenant IDs that are constrained against their parent case/assertion tenant IDs.
11. On Vercel, the case store defaults to durable Supabase and fails closed when required server credentials are missing; local development can use the explicit/default in-memory store.
12. `third_party/` remains research-only and is not a runtime dependency.

## Persistence

The domain remains behind `CaseRepository`. Local development and unit tests use `InMemoryCaseRepository`. Vercel defaults to `SupabaseCaseRepository` unless `INTEL_CASE_STORE` is explicitly configured. The Supabase implementation uses server-only credentials and migration `0003_intelligence_case_tables`, with integrity hardening in `0004_intelligence_integrity_guards`.

The Supabase service-role credential must never be exposed to browser code.

## Vercel production environment checklist

Set these exact variable names in the **Vercel Production** environment. Never commit their values.

```text
INTEL_CASE_STORE=supabase
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_PUBLISHABLE_KEY
OPENAI_API_KEY or XAI_API_KEY
```

`SUPABASE_SERVICE_ROLE_KEY` is server-only and is used by `SupabaseCaseRepository`; it must not be placed in browser-exposed variables such as `NEXT_PUBLIC_*`. `SUPABASE_PUBLISHABLE_KEY` is used for Supabase JWT verification at the application boundary. The provider key is also server-side only.

Production is not considered verified until an HTTP smoke test against the actual deployment succeeds with the intended environment configuration.

## Explicit non-goals

- jurisdiction or institution resolution
- official-contact discovery
- multi-agent research
- commitments, approvals, or outcome resolution
- full PDF/OCR/Whisper pipeline
- Neo4j, Chroma, LangChain, CrewAI, ADK, or other agent frameworks
- streaming triage
- `/app` UI redesign
- deployment or automatic provider configuration changes
