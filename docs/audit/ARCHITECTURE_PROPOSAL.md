# Target Architecture Proposal — AI Platform (Phase 1.1 Final Correction)

## 1. Executive Summary & Current vs. Target Distinction

This document presents the **Target Architecture Proposal** for the AI Platform.

### Current State vs. Target State Boundary

- **CURRENT STATE**: Audit documentation, component inventory, security taxonomy, licensing provenance, and baseline CI. No runtime platform code or provider adapters exist in the repository yet.
- **TARGET STATE**: A 5-tier conceptual platform architecture containing a Platform Kernel, Capability Services, Agent System, Optional Orchestration, and Applications.

---

## 2. The 5-Tier Conceptual Architecture (Target State)

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

### Tier Descriptions (Proposed Design)

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

The provider abstraction is strictly provider-neutral and dependency-light. It does NOT lock the kernel to OpenAI, Gemini, Anthropic, Groq, Ollama, or any specific framework.

```python
# Conceptual Target Provider Contract (For Phase 2 Implementation)
class IModelProvider(ABC):
    async def generate(self, messages: List[Message], config: ModelConfig) -> ModelResponse:
        pass

    async def stream(self, messages: List[Message], config: ModelConfig) -> AsyncGenerator[ModelResponse, None]:
        pass
```

### Conceptual Contract Capabilities
- **Multi-Message Conversations**: Supports `system`, `developer`, `user`, `assistant`, and `tool` message roles.
- **Streaming & Structured Output**: Token streaming and JSON schema output validation.
- **Tool Calls & Multimodal Inputs**: Native tool call schemas and image/audio input payloads where supported.
- **Extensible Telemetry & Usage**: Provider-neutral token usage metadata (`prompt_tokens`, `completion_tokens`) and extensible event payloads rather than hardcoded vendor fields.
- **Timeouts, Retries & Cancellation**: Standardized error hierarchy, exponential backoff retries, and cancellation tokens.
- **Model Capability Metadata**: Queryable provider capability flags (e.g., `supports_vision`, `supports_tool_calling`).

### Framework Integration via Adapters
Frameworks (Agno, LangChain, PydanticAI, CrewAI) will be integrated as **adapters** consuming `IModelProvider`, keeping the Platform Kernel dependency-light.

---

## 5. Target Security Architecture & Capability Model

The security model is a **TARGET design** to be implemented in Phase 2+. It establishes clear separation between security boundaries:

| Target Security Layer | Functional Responsibility |
| :--- | :--- |
| **Identity** | Identifies Agent ID, User Principal, Tenant ID |
| **Authorization** | Evaluates Principal Role & Assigned Capabilities |
| **Capability Grants** | Scopes permitted actions ("knowledge.read") |
| **Policy Evaluation** | Real-time check before tool execution |
| **Tool Execution** | Sandboxed invocation of atomic tools |
| **Sandboxing** | Process/container isolation for external code |
| **Human Approval** | Mandatory gateway for consequential actions |
| **Audit Logging** | Immutable OpenTelemetry event tracing |

### Capability Specification Schema

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

### Core Security Principle
**Zero AI-Generated Authority**: AI agents cannot grant themselves permissions, modify governance records, publish external communications, or execute destructive actions without deterministic human approval.

---

## 6. Deferred Technology Decisions

To preserve architectural neutrality, specific technology selections are marked with clear deferral statuses:

| Technology | Problem Solved | Alternatives | Target Layer | Decision Status |
| :--- | :--- | :--- | :--- | :--- |
| **Mem0** | Long-term user memory | Vector DBs, SQLite, PostgreSQL | Capability / Memory | **DEFERRED** (Phase 3) |
| **OpenTelemetry** | Distributed tracing | Datadog, Prometheus, Custom JSON | Cross-Cutting | **DEFERRED** (Phase 2 Kernel interface first) |
| **FastMCP / MCP** | Standardized tool protocol | Native Python tools, REST APIs | Capability / MCP | **DEFERRED** (Phase 3 Capability Service) |
| **Qdrant / Chroma** | Vector search | Pgvector, FAISS, In-memory | Capability / Knowledge | **DEFERRED** (Adapter abstraction in Phase 3) |
| **Signed Approval Tokens** | Cryptographic approvals | Session HMAC, OAuth2 JWT | Cross-Cutting | **DEFERRED** (Simple RBAC first in Phase 2) |
| **Agno / LangChain** | Agent orchestration | PydanticAI, Native Python | Framework Adapters | **DEFERRED** (Adapters outside Kernel) |

---

## 7. Target Repository Directory Structure (Planned Separation)

*Note*: Files currently remain in their original imported root paths. The directory structure below represents the **planned repository layout** for future extraction phases:

```
ai-platform/
├── platform/                      # PLATFORM INFRASTRUCTURE (Target Phase 2+)
│   ├── core/                      # Kernel: Identity, Config, Errors, Policies
│   ├── runtime/                   # Agent execution loop, State machine
│   ├── providers/                 # IModelProvider contracts & adapters
│   ├── capabilities/              # Tools, Skills, MCP, Knowledge, Memory
│   ├── policies/                  # Security guardrails & capability checks
│   ├── observability/             # OpenTelemetry event schemas & loggers
│   └── evaluation/                # Quality benchmarks & evals runner
├── applications/                  # DOMAIN APPLICATIONS (Target Phase 5+)
│   └── civic_brain/               # ISEYC Civic Brain Flagship Application
├── foundation/                    # UPSTREAM REFERENCE MATERIAL (Apache-2.0 Target)
│   ├── examples/                  # Target location for isolated reference apps
│   └── experimental/              # Target location for research & browser code
├── docs/                          # PLATFORM DOCUMENTATION & AUDITS
│   └── audit/                     # Phase 1 / Phase 1.1 Audit Documentation
├── AGENTS.md                      # Agent rules & guidelines
├── PLATFORM_ARCHITECTURE.md       # Target architecture overview
├── PLATFORM_GOVERNANCE.md         # Governance boundaries
└── PLATFORM_STRATEGY.md           # North Star Strategy
```
