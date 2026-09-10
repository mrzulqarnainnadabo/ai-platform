# AI Platform Agent Rules

## Collaboration

Jules is the primary implementation engineer. Grok is the independent refinement/hardening engineer. ChatGPT is the architecture, security, product, and release-review partner.

Agents must inspect the actual repository state before changing it and must report exact branches, commits, tests, and limitations.

## Change discipline

- Prefer small, reviewable phases.
- Preserve working behavior unless the change explicitly replaces it.
- Do not mass-delete examples before classification and replacement are verified.
- Do not create speculative infrastructure.
- Keep platform contracts provider-neutral where practical.
- Keep application-specific logic out of core platform layers.

## Security

Never commit secrets. Treat tools, connectors, browser automation, external communication, file writes, permissions, financial operations, and destructive actions as privileged capabilities.

AI output is untrusted data until validated by the application and, where required, a human authority.

## Production gate

A build passing is not sufficient for production. Production candidates require tests, dependency review, authorization review, secret/configuration review, observability, failure handling, and an explicit rollback/disablement path.

## Git discipline

- Work on a dedicated branch for substantial changes.
- Use descriptive commits.
- Do not force-push shared development branches unless the task explicitly requires it.
- Do not merge or deploy without the designated review gate.
