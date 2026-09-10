# AI Platform Governance

## Trust boundaries

The platform must distinguish:

- model output from verified application state;
- drafts from approved records;
- recommendations from authorized decisions;
- tool availability from permission to invoke a tool;
- authentication from authorization;
- application health from operational health;
- upstream code from platform-owned modifications.

## Consequential actions

Actions affecting external parties, public communication, finances, permissions, destructive data operations, or other irreversible outcomes require explicit authorization and appropriate human approval.

## Data protection

- Never commit API keys, access tokens, passwords, private certificates, or production secrets.
- Keep provider credentials server-side and scoped to the minimum required capability.
- Do not expose restricted source data merely because an agent can retrieve it.
- Log security-relevant actions without logging secrets or unnecessary sensitive content.

## AI behavior

AI components may assist with summarization, extraction, drafting, classification, explanation, and recommendation. AI components must not independently grant authority, alter permissions, publish consequential statements, approve governance records, or infer official status from weak signals.

## Release gates

Before production use, a component should have:

- documented purpose and ownership;
- dependency and license review;
- tests for critical behavior;
- secret/configuration review;
- authorization review;
- failure and timeout behavior;
- observability;
- evaluation evidence appropriate to its risk;
- rollback or disablement path;
- explicit lifecycle status.

## Upstream provenance

Changes derived from `Shubhamsaboo/awesome-llm-apps` remain subject to Apache-2.0 obligations and applicable notices. Platform modifications should be clearly distinguishable in history and documentation.
