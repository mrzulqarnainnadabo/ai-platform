# Dependency Strategy & Operations Audit — AI Platform (Phase 1.1 Final Revision)

## 1. Executive Summary & Provisional Dependency Strategy

To avoid dependency bloat and version conflicts, the AI Platform adopts a **Minimal Core Dependency Strategy**.

The Platform Kernel does NOT attempt to merge all 160 upstream `requirements.txt` files and 22 `package.json` files into a single monolithic environment. Core dependencies are kept provisional until Phase 2 validates their necessity.

---

## 2. Tiered Dependency Isolation Strategy

| Tier | Allowed Dependencies | Status |
| :--- | :--- | :--- |
| **Platform Core** | Python Standard Library (+ `pydantic v2`, `httpx`, `pyyaml`) | **PROVISIONAL** (Subject to Phase 2 validation) |
| **Adapters** | `openai`, `google-genai`, `anthropic`, `ollama-python` | Isolated per provider adapter |
| **Framework Adapters** | `agno` (phidata), `langchain-core`, `pydantic-ai` | Isolated behind framework interfaces |
| **Applications** | Domain-specific libraries (`streamlit`, `fastapi`) | Application-scoped dependencies |
| **Upstream Examples** | Isolated per-example virtualenv / requirements | Retained in reference applications |

---

## 3. Framework & Package Inventory Summary

- **Phidata / Agno**: 132 files (dominant upstream agent framework).
- **Streamlit**: 128 files (UI runtime for Python reference apps).
- **OpenAI SDK**: 124 component references.
- **Google GenAI / Gemini**: 105 component references.
- **LangChain / LangGraph**: 52 files.
- **FastAPI**: 39 files.
- **Qdrant**: 21 files.
- **Ollama**: 20 files.
- **Anthropic**: 19 files.
- **MCP SDK**: 13 files.
- **ChromaDB**: 9 files.
- **Mem0**: 7 files.
- **DeepSeek**: 6 files.
- **AutoGen / CrewAI**: 8 files.
- **PydanticAI**: 5 files.

---

## 4. Dependency Conflict Analysis & Remediation

| Package Conflict | Root Cause | Remediation Strategy |
| :--- | :--- | :--- |
| `phidata` vs `agno` | Package rebranding in upstream codebase | Map `phidata` calls to `agno` inside framework adapters |
| `pydantic v1` vs `v2` | Older tutorials use Pydantic v1 syntax | Keep Pydantic v1 code isolated in reference examples |
| `openai<1.0` vs `>=1.30` | Legacy breaking API changes | Wrap model invocations behind `IModelProvider` |
| Node 18 vs Node 20 | ESM module loading differences in Generative UI | Enforce Node.js 20+ for `applications/` frontend apps |
