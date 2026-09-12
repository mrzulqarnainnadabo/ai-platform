# Civic Intelligence Research Foundations

These repositories are included as pinned Git submodules for evaluation and selective extraction. They are **not** the AI Platform product and are not imported wholesale into the platform runtime.

The purpose is to study and selectively adapt strong open-source building blocks for a differentiated civic/institutional problem-solving system.

## Selected foundations

| Foundation | Role in AI Platform | License | Pinned upstream |
|---|---|---|---|
| `agent-memory` | Graph-native long-term memory, entity resolution, reasoning traces, audit edges | Apache-2.0 | `05cf1110012bd43f8dcaf5473befaed92c88d7e9` |
| `khive` | Typed knowledge graph, structured memory, MCP verbs, research/workspace primitives | Apache-2.0 | `551bf2ef3b7b1980402aff56d06270350ac85f67` |
| `heard` | Civic issue-to-action workflow, jurisdiction mapping, community accountability UX | MIT | `9c3e6cb128f7c94b748ca2c896ce360ccda653e5` |
| `ciutatis` | Institutional/GovOps control plane, objectives, approvals, budgets, activity/audit concepts | MIT | `1a9ec3b25fc16a5e8260c42851c32acccde1f9e8` |
| `kg-research-agent` | Evidence-grounded research pipeline, claims/evidence, RAG + knowledge graph | MIT | `0f16c2e645d8d5d13e91292dcd98a760d44dd52b` |

## Direction

The target is **not another general-purpose chatbot**. The intended product direction is a civic/institutional problem-resolution engine that can:

1. capture a real-world problem;
2. identify the responsible institution/jurisdiction;
3. gather and preserve evidence;
4. build a durable problem/actor/institution knowledge graph;
5. propose governed next actions;
6. keep a traceable record of decisions, evidence and outcomes;
7. measure whether the problem actually moved toward resolution.

Only components that fit the existing AI Platform security, authorization, provider and runtime boundaries should graduate from these foundations into first-party code.

## Provenance

Upstream source code remains attributable to its original authors. Preserve each upstream repository's license and attribution requirements. Do not present upstream projects as original AI Platform work.
