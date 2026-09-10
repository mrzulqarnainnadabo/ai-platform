# Jules Phase 1 — Import, Audit, Architecture

## Mission

Turn this repository into a coherent AI-platform foundation without blindly rewriting the upstream codebase.

The repository incorporates `Shubhamsaboo/awesome-llm-apps` under Apache-2.0. Preserve applicable license, copyright, NOTICE, and attribution requirements.

## Operating model

Jules is the principal implementation engineer for this phase. ChatGPT is the architecture/review gate. Grok will perform a later independent refinement and hardening pass.

Do not compete with or overwrite the other engineering roles. Produce a clean, reviewable implementation boundary.

## Phase 1 scope

### 1. Establish provenance
- Identify the exact upstream source and imported revision.
- Preserve upstream licensing and notices.
- Clearly distinguish upstream material from platform-owned additions.
- Do not claim upstream authorship as platform authorship.

### 2. Inventory the repository
Inspect the entire repository, not just the README.

Catalog:
- applications
- agents
- skills
- RAG/knowledge implementations
- memory implementations
- MCP integrations
- tools
- multi-agent systems
- voice systems
- generative UI
- frameworks
- model/provider integrations
- databases/vector stores
- authentication/authorization
- deployment infrastructure
- environment variables/secrets
- tests
- CI/CD
- duplicated patterns
- abandoned/broken examples

For every meaningful component record:
- location
- purpose
- runtime/language
- dependencies
- provider assumptions
- data stores
- external services
- maturity
- test coverage
- security concerns
- reuse potential

### 3. Classification
Classify components as exactly one of:

- CORE
- PLATFORM
- ADAPTER
- EXAMPLE
- EXPERIMENTAL
- LEGACY
- BROKEN
- DUPLICATE
- CANDIDATE-FOR-PLATFORM

Also assign lifecycle status where appropriate:
- EXPERIMENT
- PROTOTYPE
- INTERNAL
- BETA
- PRODUCTION-CANDIDATE
- PRODUCTION
- DEPRECATED

Do not mass-delete anything during this phase.

### 4. Architecture proposal
Design the target platform around these layers:

1. Core Platform
2. Agent Runtime
3. Agent Registry
4. Skills
5. Knowledge/RAG
6. Memory
7. Tools/MCP/Connectors
8. Multi-Agent Orchestration
9. Experience/UI
10. Voice
11. Evaluation
12. Observability
13. Security/Governance
14. Applications

Explain where existing upstream implementations fit and what should remain isolated as examples.

### 5. Provider abstraction
Identify model-provider coupling and propose stable provider interfaces. Do not force one provider. Do not add unnecessary infrastructure.

### 6. Security audit
Look for:
- committed secrets
- unsafe environment handling
- unrestricted tool execution
- SSRF/browser risks
- prompt-injection exposure
- insecure file handling
- authorization gaps
- unsafe external actions
- unbounded agent loops
- excessive permissions
- sensitive logging
- insecure defaults

Report findings by severity and do not silently dismiss them.

### 7. Dependency and operational audit
Identify:
- conflicting package managers
- duplicated dependencies
- obsolete frameworks
- incompatible Python/Node versions
- install/run instructions that conflict
- missing health checks
- missing tests
- deployment assumptions

Do not upgrade dependencies simply for cosmetic reasons. Record compatibility risks first.

### 8. Platform seams
Where the codebase contains multiple implementations of the same capability, propose the smallest useful shared contract rather than rewriting every implementation immediately.

Examples:
- provider adapter
- agent interface
- tool interface
- skill metadata
- retrieval interface
- memory interface
- execution event schema
- evaluation interface

### 9. Deliverables
Create:

- `docs/audit/REPOSITORY_INVENTORY.md`
- `docs/audit/COMPONENT_CLASSIFICATION.md`
- `docs/audit/SECURITY_AUDIT.md`
- `docs/audit/DEPENDENCY_AUDIT.md`
- `docs/audit/ARCHITECTURE_PROPOSAL.md`
- `docs/audit/MIGRATION_PLAN.md`

Add concise machine-readable inventories where useful, but avoid creating a database just for the audit.

### 10. Tests
Run the repository's available tests/lint/build checks where practical. Record failures accurately. Do not hide failing examples by deleting them.

## Hard constraints

- Do not rebuild the project from scratch.
- Do not mass-delete upstream applications.
- Do not convert everything into one monolith.
- Do not add microservices merely because they sound scalable.
- Do not commit secrets.
- Do not introduce production credentials.
- Do not silently change licenses.
- Do not make consequential external actions.
- Do not make AI-generated authority decisions.
- Do not claim production readiness from a successful build alone.
- Do not merge or deploy this phase automatically.

## Completion report

Return:
- branch
- commit SHA
- files added/changed
- inventory counts
- classification counts
- security findings
- dependency findings
- proposed target architecture
- migration priorities
- tests executed and results
- unresolved risks
- what should happen in Phase 2

Stop after this phase and leave the repository ready for ChatGPT architectural review.