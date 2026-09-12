"""Development-only demo wrapper for the Intelligence Case Workspace.

This module never changes production authentication or authorization. Demo mode
is exposed only when explicitly enabled by the server and never in production.
The browser uses deterministic mock data and does not receive any credentials.
"""
from __future__ import annotations

import os

from fastapi.responses import HTMLResponse

from api.cases_frontend import cases_page


def demo_mode_enabled() -> bool:
    """Return whether the server explicitly permits the development demo."""
    enabled = os.getenv("AI_PLATFORM_DEMO_MODE", "").strip().lower() == "true"
    vercel_env = os.getenv("VERCEL_ENV", "").strip().lower()
    app_env = os.getenv("ENVIRONMENT", "").strip().lower()
    return enabled and vercel_env != "production" and app_env != "production"


_DEMO_SCRIPT = r"""
<script>
(() => {
  const DEMO_USER = {
    id: "demo-user",
    email: "demo.operator@local.invalid",
  };
  const TENANT_ID = "demo-tenant";
  const now = new Date();
  const iso = (minutes) => new Date(now.getTime() - minutes * 60000).toISOString();
  const makeCase = (id, title, summary, status, age) => ({
    id, tenant_id: TENANT_ID, created_by_subject: DEMO_USER.id, title, summary,
    status, created_at: iso(age), updated_at: iso(Math.max(age - 8, 1))
  });
  const state = {
    cases: [
      makeCase("demo-case-001", "Water access disruption", "Residents report repeated interruption of potable water access in the affected area.", "open", 180),
      makeCase("demo-case-002", "Clinic medicine stockout", "A community clinic reports that several essential medicines are unavailable.", "in_progress", 420),
      makeCase("demo-case-003", "School transport complaint", "Parents report inconsistent school transport availability during the current term.", "resolved", 900)
    ],
    details: {},
    next: 4
  };
  const audit = (caseId, action, objectType, objectId) => ({
    id: `demo-audit-${caseId}-${Date.now()}`,
    tenant_id: TENANT_ID,
    actor_subject: DEMO_USER.id,
    action, object_type: objectType, object_id: objectId,
    payload_digest: "demo-digest-immutable-development-only",
    metadata: { demo: true }, created_at: new Date().toISOString()
  });
  for (const c of state.cases) {
    state.details[c.id] = {
      case: c,
      assertions: [
        { id: `${c.id}-assertion-1`, case_id: c.id, text: c.summary, kind: "claim", created_by: DEMO_USER.id, requires_evidence: true, created_at: c.created_at, evidence_ids: [] },
        { id: `${c.id}-assertion-2`, case_id: c.id, text: "The reported pattern may indicate a recurring service-level problem.", kind: "inference", created_by: "demo-triage", requires_evidence: true, created_at: c.updated_at, evidence_ids: [] }
      ],
      evidence: [],
      missing_evidence_questions: ["What primary record or source can verify the reported incident?", "What date range and affected population should be checked?"],
      audit_events: [audit(c.id, "case.created", "case", c.id)]
    };
  }
  const response = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
  const clone = (value) => JSON.parse(JSON.stringify(value));
  const fakeSession = { access_token: "demo-session-token", user: DEMO_USER };

  window.supabase.createClient = () => ({
    auth: {
      getSession: async () => ({ data: { session: fakeSession }, error: null }),
      signInWithPassword: async () => ({ data: { session: fakeSession, user: DEMO_USER }, error: null }),
      signUp: async () => ({ data: { session: fakeSession, user: DEMO_USER }, error: null }),
      signOut: async () => ({ error: null }),
      onAuthStateChange: () => ({ data: { subscription: { unsubscribe() {} } } })
    }
  });

  const realFetch = window.fetch.bind(window);
  window.fetch = async (input, init = {}) => {
    const url = typeof input === "string" ? input : input.url;
    if (!url.startsWith("/api/v1/cases")) return realFetch(input, init);
    const path = url.split("?")[0];
    const method = (init.method || "GET").toUpperCase();
    if (method === "GET" && path === "/api/v1/cases") return response({ cases: clone(state.cases) });
    const parts = path.split("/").filter(Boolean);
    const caseId = parts[3];
    if (!caseId || !state.details[caseId]) return response({ detail: "Case not found" }, 404);
    const detail = state.details[caseId];
    if (method === "GET") return response(clone(detail));
    if (method === "POST" && parts[4] === "triage") {
      const c = detail.case;
      detail.assertions.push({ id: `${caseId}-triage-${Date.now()}`, case_id: caseId, text: "AI suggests verifying the reported pattern against an independent source before treating it as established fact.", kind: "unknown", created_by: "demo-triage", requires_evidence: true, created_at: new Date().toISOString(), evidence_ids: [] });
      detail.missing_evidence_questions = ["Which independent source can corroborate the report?", "Can the reported condition be verified for a specific date or location?"];
      detail.audit_events.push(audit(caseId, "case.triaged", "case", caseId));
      c.updated_at = new Date().toISOString();
      return response(clone(detail));
    }
    if (method === "POST" && parts[4] === "evidence") {
      const payload = JSON.parse(init.body || "{}");
      const id = `${caseId}-evidence-${Date.now()}`;
      detail.evidence.push({ id, case_id: caseId, assertion_id: payload.assertion_id || null, body: payload.body, source_type: payload.source_type, source_uri: payload.source_uri || null, note: payload.note || null, created_by_subject: DEMO_USER.id, created_at: new Date().toISOString() });
      if (payload.assertion_id) {
        const assertion = detail.assertions.find((item) => item.id === payload.assertion_id);
        if (assertion) assertion.evidence_ids.push(id);
      }
      detail.audit_events.push(audit(caseId, "evidence.attached", "evidence", id));
      return response({ ...clone(detail.evidence.at(-1)) });
    }
    return response({ detail: "Demo operation not supported" }, 400);
  };

  const banner = document.createElement("div");
  banner.textContent = "DEMO MODE — DEVELOPMENT ONLY · No production data or credentials are used";
  banner.style.cssText = "position:fixed;left:0;right:0;bottom:0;z-index:9999;background:#111827;color:#f8fafc;text-align:center;padding:9px 12px;font:700 12px system-ui;letter-spacing:.02em";
  document.addEventListener("DOMContentLoaded", () => document.body.appendChild(banner));
})();
</script>
"""


def demo_cases_page() -> HTMLResponse:
    if not demo_mode_enabled():
        return HTMLResponse("Not Found", status_code=404)
    html = cases_page().body.decode("utf-8")
    marker = '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script><script>'
    replacement = '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>' + _DEMO_SCRIPT + '<script>'
    return HTMLResponse(html.replace(marker, replacement, 1))
