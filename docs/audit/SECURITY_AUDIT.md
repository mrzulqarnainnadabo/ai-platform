# Contextual Security Audit — AI Platform (Phase 1.1 Final Revision)

## 1. Executive Summary & Contextual Framework

This security audit evaluates security findings across all 1,652 imported files through a **Contextual Risk Framework**.

Rather than treating every instance of `eval()`, `exec()`, `subprocess`, or browser automation as an immediate critical platform vulnerability, findings are classified by their **Execution Context** and **Deployment Exposure**.

---

## 2. Contextual Risk Matrix

Security findings are categorized into 5 execution contexts:
1. **Trusted Platform Infrastructure**: High severity; affects platform kernel or shared core services (None currently exist).
2. **Candidate Platform Component**: Medium/High severity; components selected for promotion to platform.
3. **Isolated Example / Tutorial**: Low severity; upstream educational code retained in reference examples.
4. **Development / Test-Only Risk**: Low severity; evaluation scripts or local test harnesses.
5. **Configuration / Deployment Risk**: Operations risk; unauthenticated Streamlit/FastAPI endpoints.

| Finding Category | Contextual Placement | Severity | Action Required |
| :--- | :--- | :---: | :--- |
| `eval()` in adk tool | Isolated Tutorial Example | **LOW** | Block promotion to platform |
| `exec()` in win_use | Experimental Sandbox App | **LOW** | Quarantine in planned experimental area |
| `subprocess` in tts | Isolated Example | **MEDIUM** | Pass list args without `shell=True` |
| Direct Env Keys | Candidate Components | **MEDIUM** | Implement `PlatformSecrets` adapter in Phase 2 |
| Unauth Streamlit | Deployment Config Risk | **HIGH** | Add Auth Middleware before deployment |

---

## 3. Component Promotion & Security Lifecycle

To prevent unsafe upstream code from contaminating the trusted platform, components must pass through a strict 6-stage lifecycle:

```
  [ DISCOVER ] ──► [ CLASSIFY ] ──► [ QUARANTINE / BLOCK PROMOTION ]
                                                │
  [ PROMOTE ] ◄─── [ VALIDATE ] ◄─── [ REMEDIATE IF SELECTED ]
```

1. **DISCOVER**: Catalog component during audit.
2. **CLASSIFY**: Assign taxonomy classification (`EXAMPLE`, `EXPERIMENTAL`, `CANDIDATE`).
3. **QUARANTINE / BLOCK PROMOTION**: Unselected or unsafe components remain isolated in upstream reference folders.
4. **REMEDIATE IF SELECTED**: If selected for platform extraction, eliminate `eval()`, sanitize subprocesses, and enforce capability bounds.
5. **VALIDATE**: Run security test suite, secret guards, and capability checks.
6. **PROMOTE**: Move remediated component into `platform/capabilities/`.

---

## 4. Sensitive-Domain Application Boundaries

Upstream components operating in sensitive domain areas (Financial, Health, Legal, Political, Recruitment) must **NOT** be promoted into the generic Platform Kernel:

- `ai_finance_agent_team`, `xai_finance_agent` -> Remain **Applications / Reference Implementations**.
- `ai_medical_imaging_agent`, `ai_mental_wellbeing_agent` -> Remain **Applications / Reference Implementations**.
- `ai_legal_agent_team` -> Remains **Application / Reference Implementation**.
- `ai_recruitment_agent_team` -> Remains **Application / Reference Implementation**.

*Principle*: Domain-specific decision authority and clinical/legal liability remain strictly outside the generic platform core. Reusable low-level adapters (e.g., SEC EDGAR fetchers or PDF table parsers) may be extracted as capability services if justified.

---

## 5. Summary of Contextualized Security Findings

| Finding ID | Vulnerability Type | File Location | Execution Context | Severity | Remediation Strategy |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **SEC-001** | `eval()` call | `google_adk_crash_course/.../calculator_agent/tools.py` | Isolated Tutorial | **LOW** | Quarantine in reference examples |
| **SEC-002** | `exec()` call | `windows_use_autonomous_agent/agent/utils.py` | Experimental Sandbox | **LOW** | Quarantine in experimental area |
| **SEC-003** | Subprocess shell | `beifong/scheduler.py` | Isolated Example | **MEDIUM** | Pass list args without `shell=True` |
| **SEC-004** | Direct Env Key | 120+ Python reference apps | Candidate / Example | **MEDIUM** | Centralized `PlatformSecrets` loader |
| **SEC-005** | SSRF Browser | `browser_mcp_agent`, `windows_use` | Experimental | **HIGH** | URL whitelist sandbox before execution |
| **SEC-006** | Auth Absence | 128 Streamlit & 39 FastAPI apps | Deployment Config | **HIGH** | Auth middleware on app boundaries |
