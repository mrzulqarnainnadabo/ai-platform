# Architecture Proposal — AI Platform (Phase 1.1 Correction)

## 1. Executive Summary & Structural Correction

This document revises the initial 14-layer architecture into a practical, highly maintainable **5-Tier Conceptual Architecture** with **Cross-Cutting Controls**.

Rather than enforcing 14 rigid, sequential layers where every component must pass through every layer, the corrected architecture separates the **Platform Kernel**, **Capability Services**, **Agent System**, **Optional Orchestration**, and **Applications**.

---

## 2. The 5-Tier Conceptual Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 5. APPLICATIONS (Flagship: ISEYC Civic Brain | Business AI | Doc AI)   │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│ 4. OPTIONAL ORCHESTRATION (Workflows | Routing | Multi-Agent Handoffs)  │
│    *Simple agents do NOT depend on orchestration!                        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│ 3. AGENT SYSTEM (Registry | Manifests | Capabilities | Evaluation)       │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│ 2. CAPABILITY SERVICES (Tools | Skills | MCP Connectors | RAG | Memory) │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│ 1. PLATFORM KERNEL (Identity | Config | Provider Abstraction | Runtime) │
└─────────────────────────────────────────────────────────────────────────┘

===========================================================================
 CROSS-CUTTING CONTROLS (Applied across ALL 5 tiers):
 Security | Authorization | Governance | Auditability | Observability | Evals
===========================================================================
```

### Tier Descriptions

#### Tier 1: PLATFORM KERNEL (Minimal Trusted Foundation)
- **Identity & Authorization**: Tenant ID, user/agent principal, role assignment.
- **Configuration**: Environment variables, feature flags, system settings.
- **Model / Provider Abstraction**: Provider-neutral interfaces (`IModelProvider`) supporting streaming, structured outputs, tool calls, and usage telemetry.
- **Agent Runtime Contracts**: Base execution loop, lifecycle states, cancellation, timeouts.
- **Capabilities & Policies**: Policy engine validating capability requests.
- **Events & Errors**: OpenTelemetry structured event schema and standardized error hierarchy.

#### Tier 2: CAPABILITY SERVICES (Reusable Primitives)
- **Tools**: Single-purpose atomic functions (web search, calculator, database lookup).
- **Skills**: Versioned executable capability packages with explicit schemas and permissions.
- **MCP Connectors**: Model Context Protocol client/server adapters (GitHub, SQLite, Notion).
- **Knowledge & RAG**: Ingestion pipelines, chunking, embeddings, hybrid retrieval, citations.
- **Memory**: Session memory, short-term context, and long-term semantic memory.

#### Tier 3: AGENT SYSTEM
- **Agent Registry**: Capability discovery, version tracking, and status management.
- **Agent Manifests**: Declarative YAML/JSON definitions of agent identity, prompt, allowed capabilities, tools, and limits.
- **Evaluation & Observability**: Evaluation benchmarks, trace capture, and quality metrics.

#### Tier 4: OPTIONAL ORCHESTRATION
- **Multi-Agent Coordination**: Event-driven handoffs, router agents, dynamic team assembly.
- **Workflows & Background Execution**: Task queues, scheduled runs (APScheduler).
- *Strict Rule*: Multi-agent orchestration is **completely optional**. A single agent must execute directly on the Platform Kernel without requiring orchestration overhead.

#### Tier 5: APPLICATIONS
- **ISEYC Civic Brain**: Flagship civic intelligence and policy application.
- **Specialized AI Products**: Financial due diligence, legal research, operations monitoring.

---

## 3. Cross-Cutting Platform Controls

Security, governance, auditability, observability, and evaluation are **cross-cutting platform concerns** enforced across every tier:

| Cross-Cutting Control | Enforcement Scope |
| :--- | :--- |
| **Security & Authz** | Validates principal permissions & capability scopes |
| **Governance** | Human approval gateway for consequential tasks |
| **Auditability** | Immutable event logs for all tool executions |
| **Observability** | OpenTelemetry tracing across models and tools |
| **Evaluation** | Automated quality benchmarking & scorecards |
| **Data Boundaries** | Tenant isolation & PII masking filters |

---

## 4. Provider Abstraction Contract Design

The provider abstraction avoids simplistic prompt-in string-out signatures. The platform defines a rich, provider-neutral conceptual contract in Python:

```python
# Conceptual Provider Contract
class IModelProvider(ABC):
    async def generate(self, messages: List[Message], config: ModelConfig) -> ModelResponse:
        pass

    async def stream(self, messages: List[Message], config: ModelConfig) -> AsyncGenerator[ModelResponse, None]:
        pass
```

Supporting:
- Multi-message conversations (`system`, `developer`, `user`, `assistant`, `tool`)
- Streaming completion tokens & tool call chunks
- Structured output formatting & JSON schema validation
- Multimodal inputs (text, image, audio) where supported
- Token usage metadata (`prompt_tokens`, `completion_tokens`, `cost_usd`)
- Timeouts, retries, and cancellation tokens
- Model capability metadata and capability detection

### Framework Integration via Adapters
Frameworks (Agno, LangChain, PydanticAI) are integrated as **adapters** consuming `IModelProvider`, ensuring the Platform Kernel remains dependency-light.

---

## 5. Capability-Based Security Model

Agents are defined by explicit capability bounds rather than unrestricted tool access:

```
Agent Principal
 ├── Identity (Agent ID, Owner Tenant)
 ├── Allowed Capabilities (e.g., "knowledge.read.civic", "web.search")
 ├── Allowed Tools (e.g., ["duckduckgo_search", "qdrant_query"])
 ├── Data Scopes (e.g., "tenant:123:public_docs")
 ├── Network Policy (e.g., Whitelisted domains: ["*.gov", "api.github.com"])
 ├── Execution Limits (Max tokens: 10,000, Max budget: $0.50, Timeout: 30s)
 ├── Approval Requirements (Human-in-the-loop for external communications)
 └── Audit Policy (Log level: VERBOSE, OpenTelemetry trace enabled)
```

### Conceptual Authorization Flow

```
User / Agent Identity
        ↓
Role / Principal Permissions
        ↓
Requested Capability / Tool Invocation
        ↓
Risk Classification (READ_ONLY vs. MUTATION vs. CONSEQUENTIAL)
        ↓
Policy Evaluation Engine
        ↓
Human Approval Gateway (If Risk == CONSEQUENTIAL)
        ↓
Scoped Tool Execution Sandbox
        ↓
Immutable Audit Event Logging
```

---

## 6. Deferred Technology Decisions

To prevent premature technology lock-in, candidate technologies are classified with clear deferral statuses:

| Technology | Problem Solved | Alternatives | Target Layer | Decision Status |
| :--- | :--- | :--- | :--- | :--- |
| **Mem0** | Long-term user memory | Vector DBs, SQLite, PostgreSQL | Capability / Memory | **DEFERRED** (Phase 3) |
| **OpenTelemetry** | Distributed tracing | Datadog, Prometheus, Custom JSON | Cross-Cutting | **DEFERRED** (Phase 2 Kernel interface first) |
| **FastMCP / MCP** | Standardized tool protocol | Native Python tools, REST APIs | Capability / MCP | **DEFERRED** (Phase 3 Capability Service) |
| **Qdrant / Chroma** | Vector search | Pgvector, FAISS, In-memory | Capability / Knowledge | **DEFERRED** (Adapter abstraction in Phase 3) |
| **Signed Approval Tokens** | Cryptographic approvals | Session HMAC, OAuth2 JWT | Cross-Cutting | **DEFERRED** (Simple RBAC first in Phase 2) |
| **Agno / LangChain** | Agent orchestration | PydanticAI, Native Python | Framework Adapters | **DEFERRED** (Adapters outside Kernel) |

---

## 7. Proposed Repository Directory Structure

```
ai-platform/
├── platform/                      # PLATFORM INFRASTRUCTURE (Phase 2+)
│   ├── core/                      # Kernel: Identity, Config, Errors, Policies
│   ├── runtime/                   # Agent execution loop, State machine
│   ├── providers/                 # IModelProvider contracts & adapters
│   ├── capabilities/              # Tools, Skills, MCP, Knowledge, Memory
│   ├── policies/                  # Security guardrails & capability checks
│   ├── observability/             # OpenTelemetry event schemas & loggers
│   └── evaluation/                # Quality benchmarks & evals runner
├── applications/                  # DOMAIN APPLICATIONS (Phase 5+)
│   └── civic_brain/               # ISEYC Civic Brain Flagship Application
├── foundation/                    # UPSTREAM REFERENCE MATERIAL (Apache-2.0)
│   ├── examples/                  # Isolated working reference applications
│   └── experimental/              # Research & browser automation code
├── docs/                          # PLATFORM DOCUMENTATION & AUDITS
│   └── audit/                     # Phase 1 / Phase 1.1 Audit Documentation
├── AGENTS.md                      # Agent rules & guidelines
├── PLATFORM_ARCHITECTURE.md       # Target architecture overview
├── PLATFORM_GOVERNANCE.md         # Governance boundaries
└── PLATFORM_STRATEGY.md           # North Star Strategy
```
