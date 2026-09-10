# Dependency & Operations Audit — AI Platform Foundation

## Executive Summary

The upstream foundation exhibits significant dependency fragmentation and framework duplication across its 160 components.

---

## 1. Package & Dependency Fragmentation

### Python Environment Analysis
- **Requirements Files**: 160 distinct `requirements.txt` files.
- **Primary Framework Conflicts**:
  - `phidata` (132 references): Older versions of `phidata` conflict with newly rebranded `agno` package imports.
  - `langchain` (39 references): Mix of legacy `langchain==0.1.x` and `langchain-community` packages.
  - `pydantic`: Incompatibilities between Pydantic v1 (`pydantic<2.0.0`) in older examples and Pydantic v2 (`pydantic>=2.7.0`) in `pydantic-ai` / `fastmcp`.
  - `openai`: Incompatible method calls between `openai<1.0.0` and `openai>=1.30.0`.

### Node.js / JavaScript Environment Analysis
- **Package.json Files**: 22 distinct `package.json` files.
- **Framework Mix**: Next.js 14/15, CopilotKit, React 18, Tailwind CSS, Vite.
- **Runtime Conflict**: Node.js 18 vs Node.js 20 ESM module resolution requirements.

---

## 2. Missing Tests & Operational Fragility

- **Repository Test Coverage**: Out of 1,652 files, only **23 test files** exist (< 15% coverage).
- **Environment Variable Inconsistency**: Environment variables use divergent names across examples:
  - `OPENAI_API_KEY` vs `OPENAI_KEY` vs `AZURE_OPENAI_KEY`
  - `GEMINI_API_KEY` vs `GOOGLE_API_KEY`
  - `QDRANT_URL` vs `QDRANT_HOST`
- **Hardcoded Local Dependencies**:
  - Hardcoded local paths (`/Users/...` or `C:\...`) found in 4 script files.
  - Hardcoded localhost ports (`8501`, `8000`, `3000`, `5000`) leading to port collisions during concurrent run.

---

## 3. Deployment & Coexistence Matrix

| Framework Combination | Coexistence Feasibility | Action Required |
| :--- | :---: | :--- |
| `agno` + `openai` + `fastapi` | High | Primary target stack for Python runtime |
| `pydantic-ai` + `fastmcp` | High | Target stack for MCP and structured tool routing |
| `phidata` (legacy) + `agno` | Low (Import namespace collisions) | Upgrade legacy `phidata` imports to `agno` |
| `langchain v0.1` + `pydantic v2` | Low (Breaking Pydantic schema errors) | Isolate legacy LangChain examples |
| `autogen / ag2` + `crewai` | Medium (Heavy dependency footprint) | Keep isolated in multi-agent adapter packages |
