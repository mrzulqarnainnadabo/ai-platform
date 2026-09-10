# AI Platform

A unified, modular AI platform built from a broad open-source AI application foundation and evolved into a governed platform for agents, skills, knowledge, tools, memory, orchestration, and AI applications.

## Mission

Build a reusable AI platform that can host many specialized AI products without turning every application into a separate stack.

## Foundation

This repository incorporates material from [`Shubhamsaboo/awesome-llm-apps`](https://github.com/Shubhamsaboo/awesome-llm-apps), licensed under Apache-2.0. See `UPSTREAM_FOUNDATION.md` and retain all applicable upstream notices and license requirements.

## Platform direction

```text
AI Platform
├── Core Platform
│   ├── configuration
│   ├── provider abstraction
│   ├── identity / authorization
│   ├── audit / observability
│   └── runtime contracts
├── Agent Runtime
│   ├── agents
│   ├── workflows
│   ├── tools
│   ├── memory
│   └── orchestration
├── Knowledge
│   ├── ingestion
│   ├── retrieval / RAG
│   ├── embeddings
│   └── citations
├── Skills
├── Connectors / MCP
├── Experience
│   ├── chat
│   ├── agent workspace
│   ├── generative UI
│   └── voice
├── Governance
│   ├── permissions
│   ├── approvals
│   ├── evaluations
│   ├── safety controls
│   └── data boundaries
└── Applications
```

## Engineering rule

**Preserve → understand → test → modularize → consolidate → improve.**

The foundation is not to be blindly rewritten or mass-deleted. Reusable components should be migrated incrementally after dependency, security, licensing, and behavior are understood.

## Collaboration

- **Jules:** primary implementation engineer.
- **Grok:** independent refinement, testing, hardening, and second-pass engineering.
- **ChatGPT:** architecture, security, product, code-review, and release-gate partner.

No major merge or production deployment is considered approved merely because an agent reports success.
