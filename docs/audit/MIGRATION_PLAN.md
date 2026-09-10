# Phased Migration Roadmap — AI Platform (Phase 1.1 Revision)

## 1. Executive Summary & Phased Strategy

This migration plan outlines the structured, 8-phase roadmap for evolving the imported `awesome-llm-apps` foundation into the production-grade **AI Platform**.

Migration is strictly incremental. Upstream reference examples are retained in `foundation/examples/` and extracted into `platform/` only when validated against platform contracts.

---

## 2. The 8-Phase Migration Roadmap

```
PHASE 0: FOUNDATION (Repository, Provenance, Baseline CI)
   │
PHASE 1: AUDIT (Inventory, Taxonomy, Security, Dependency Audit)
   │
PHASE 1.1: ARCHITECTURE CORRECTION (North Star Strategy, 5-Tier Arch) [CURRENT]
   │
PHASE 2: PLATFORM KERNEL (Identity, Config, Provider Contracts, Runtime, Policies)
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

## 3. Detailed Phase Breakdown & Phase Dependencies

| Phase | Core Deliverables | Critical Dependencies | Risk Level |
| :--- | :--- | :--- | :---: |
| **Phase 0** | Repository setup, Apache-2.0 notice, CI workflow | None | Low |
| **Phase 1** | Full repository inventory, initial audit docs | Phase 0 | Low |
| **Phase 1.1** | `PLATFORM_STRATEGY.md`, corrected 5-tier architecture, reconciled counts | Phase 1 | Low |
| **Phase 2** | `platform/core/` (Identity, Config, `IModelProvider`, Runtime, Policies) | Phase 1.1 | High |
| **Phase 3** | `platform/capabilities/` (Tools, Skills, MCP, RAG, Memory) | Phase 2 | Medium |
| **Phase 4** | `platform/runtime/` & Registry (Agent manifests, Evals, Telemetry) | Phase 3 | Medium |
| **Phase 5** | `platform/orchestration/` (Optional workflows, routing, handoffs) | Phase 4 | Medium |
| **Phase 6** | Porting high-value candidate components to `platform/capabilities/` | Phase 4 | Medium |
| **Phase 7** | `applications/civic_brain/` full production deployment | Phase 4, Phase 6 | High |

---

## 4. Phase 2 Immediate Recommended Priorities

Upon approval of Phase 1.1 by ChatGPT review gate:
1. **Directory Creation**: Establish `platform/core/` and `platform/providers/`.
2. **Core Provider Contracts**: Implement `IModelProvider` interface in Python with `OpenAIAdapter`, `GeminiAdapter`, `AnthropicAdapter`, and `OllamaAdapter`.
3. **Secrets Loader**: Implement `PlatformSecrets` loader with environment validation.
4. **Base Runtime Loop**: Implement `AgentRuntime` base class with timeout, cancellation, and event logging hooks.
5. **Security Policy Engine**: Implement basic capability checker (`PolicyEngine`) restricting tool invocations.
