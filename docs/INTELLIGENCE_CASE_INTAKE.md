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

### Read a case

`GET /api/v1/cases/{id}`

Returns the case, assertions, evidence, missing-evidence questions, and audit events.

### Triage a case

`POST /api/v1/cases/{id}/triage`

The server invokes `AuthorizedModelRuntime` only after `case.triage` is authorized. The model receives a strict JSON schema and untrusted case text; deterministic validation rejects malformed output and any model-suggested `fact` assertion without evidence.

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

For `url` and `document_ref`, `source_uri` is required.

## Security invariants

1. Supabase JWT claims are the only source of identity, tenant, and capabilities.
2. Client request bodies cannot grant permissions or change tenant identity.
3. Case access is tenant-isolated.
4. Each case operation requires its explicit capability.
5. A denied triage request is rejected before provider configuration/model execution.
6. Model calls happen only through `AuthorizedModelRuntime`.
7. Model output cannot establish a `fact` without linked evidence.
8. Evidence is immutable after creation in the v1 service contract.
9. Audit events contain digests/metadata, never provider secrets.
10. `third_party/` remains research-only and is not a runtime dependency.

## Persistence note

This first vertical slice uses a repository interface with an in-memory implementation so the domain and authorization contracts can be tested without introducing a new database dependency. It is intentionally a replaceable persistence boundary; durable Supabase persistence is a subsequent phase.

## Explicit non-goals

- jurisdiction or institution resolution
- official-contact discovery
- multi-agent research
- commitments, approvals, or outcome resolution
- file upload/OCR pipeline
- Neo4j, Chroma, LangChain, CrewAI, ADK, or other agent frameworks
- streaming triage
- `/app` UI redesign
- deployment or Vercel environment changes
