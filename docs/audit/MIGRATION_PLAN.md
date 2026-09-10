# Phased Migration Roadmap — AI Platform (Phase 1.1 Revision)

## 1. Executive Summary & Phased Strategy

This migration plan outlines the structured, 8-phase roadmap for evolving the imported `awesome-llm-apps` foundation into the production-grade **AI Platform**.

Migration is strictly incremental. Upstream reference examples are retained in their current paths and extracted into `platform/` only when validated against platform contracts.

---

## 2. The 8-Phase Migration Roadmap

```
PHASE 0: FOUNDATION (Repository, Provenance, Baseline CI)
   │
PHASE 1: AUDIT (Inventory, Taxonomy, Security, Dependency Audit)
   │
PHASE 1.1: ARCHITECTURE CORRECTION (North Star Strategy, 5-Tier Arch) [CURRENT]
   │
PHASE 2: PLATFORM KERNEL (Incremental Core Slices 2A - 2E)
   ├── 2A: Core Contracts (IModelProvider, Message, Config)
   ├── 2B: Minimal Runtime (AgentRuntime loop, Cancellation, Timeouts)
   ├── 2C: Capability & Policy Boundary (PolicyEngine, Tool Scopes)
   ├── 2D: Provider Adapter Prototype (Single provider verification)
   └── 2E: Validation & Security Tests (Unit tests & Secret guards)
   │
PHASE 3: TRUSTED CAPABILITIES (Tools, Skills, MCP, Knowledge/RAG, Memory)
   │
PHASE 4: AGENT SYSTEM (Registry, Manifests, Permissions, Evals, Observability)
   │
PHASE 5: OPTIONAL ORCHESTRATION (Workflows, Routing, Multi-Agent Teams)
   │
PHASE 6: APPLICATION EXTRACTION (Migrate Selected High-Value Components)
   │
PHASE 7: FLAGSHIP APPLICATIONS (ISEYC Civic Brain Full Deployment)
```

---

## 3. Detailed Phase Breakdown & Dependencies

| Phase | Core Deliverables | Critical Dependencies | Risk Level |
| :--- | :--- | :--- | :---: |
| **Phase 0** | Repository setup, Apache-2.0 notice, CI workflow | None | Low |
| **Phase 1** | Full repository inventory, initial audit docs | Phase 0 | Low |
| **Phase 1.1** | `PLATFORM_STRATEGY.md`, corrected 5-tier architecture, reconciled counts | Phase 1 | Low |
| **Phase 2** | `platform/core/` (Incremental Kernel Slices 2A-2E) | Phase 1.1 | High |
| **Phase 3** | `platform/capabilities/` (Tools, Skills, MCP, RAG, Memory) | Phase 2 | Medium |
| **Phase 4** | `platform/runtime/` & Registry (Agent manifests, Evals, Telemetry) | Phase 3 | Medium |
| **Phase 5** | `platform/orchestration/` (Optional workflows, routing, handoffs) | Phase 4 | Medium |
| **Phase 6** | Porting high-value candidate components to `platform/capabilities/` | Phase 4 | Medium |
| **Phase 7** | `applications/civic_brain/` full production deployment | Phase 4, Phase 6 | High |

---

## 4. Phase 2 Incremental Slice Execution Strategy

Upon approval of Phase 1.1 by ChatGPT review gate, Phase 2 will proceed in 5 tight, test-driven slices:

1. **Slice 2A — Core Contracts**: Define `IModelProvider`, `Message`, `ModelConfig`, and `ModelResponse` dataclasses in `platform/core/providers/`.
2. **Slice 2B — Minimal Runtime**: Implement `AgentRuntime` base execution loop with timeout and cancellation token handling.
3. **Slice 2C — Capability & Policy Boundary**: Implement `PolicyEngine` validating tool invocation requests against capability grants.
4. **Slice 2D — Provider Adapter Prototype**: Build a single provider adapter prototype (e.g. `OpenAIAdapter`) verifying `IModelProvider` contract compliance.
5. **Slice 2E — Validation & Security Tests**: Write unit tests, secret guard rules, and acceptance gate checks for Phase 2 kernel.
