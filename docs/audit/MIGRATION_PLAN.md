# Migration Plan — AI Platform Foundation

## Executive Summary

This phased migration plan outlines the roadmap for transitioning the imported `awesome-llm-apps` foundation into the production-grade **AI Platform**.

---

## 1. Migration Roadmap Phases

### Phase 1: Full Repository Import Audit (CURRENT)
- **Goal**: Catalog, classify, and audit all imported components without mass-deleting or altering working upstream code.
- **Status**: Complete. Audit documentation established in `docs/audit/`.

### Phase 2: Core Platform & Provider Abstraction Foundation
- **Goal**: Establish core provider abstractions (`IModelProvider`), central secrets loader, security guardrails, and basic runtime interfaces in `core/`.
- **Key Primitives**: `IModelProvider`, `PlatformSecrets`, `SecurityGuard`.

### Phase 3: High-Value Primitives Extraction
- **Goal**: Extract top candidate components into platform layers:
  - `always_on_agents/always_on_hn_briefing_agent` -> Platform Scheduler & Background Runner
  - `agent_skills/` -> Platform Skill Registry
  - `mcp_ai_agents/` -> MCP Connector Gateway
  - `rag_tutorials/agentic_typed_rag_pydanticai` -> Knowledge & Typed RAG Pipeline

### Phase 4: Runtime Standardization & Agent Registry Creation
- **Goal**: Standardize agent execution loop, event telemetry, state machine, and multi-agent handoff bus.

### Phase 5: Application Migration & Civic Brain Integration
- **Goal**: Port ISEYC Civic Brain as a first-class application layer component on top of the standardized platform stack.

### Phase 6: Consolidation, Example Archival & Legacy Sunset
- **Goal**: Move legacy / broken upstream examples to an archived reference folder; establish final production candidate builds.

---

## 2. Phase 2 Scope & Immediate Recommendations

1. **Establish Core Directory**: Create `core/platform/` with provider abstractions.
2. **Fix Critical Security Issues**: Replace `eval()`/`exec()` in calculator and windows_use tools.
3. **Submit Audit Package**: Submit completed Phase 1 deliverables for ChatGPT architectural review.
