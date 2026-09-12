"""Authentication-enhanced wrapper for the Intelligence Case workspace.

Keeps the existing case UI intact while adding low-friction Google OAuth and
an explicit production-safe email confirmation redirect. Supabase remains the
source of truth for authentication and the existing server-side authorization
boundary is unchanged.
"""
from __future__ import annotations

from fastapi.responses import HTMLResponse

from api.cases_frontend import cases_page


def cases_auth_page() -> HTMLResponse:
    """Return the existing case workspace with resilient auth entry points."""
    response = cases_page()
    html = response.body.decode("utf-8")

    # Expose only the browser-safe Supabase client on window so the injected
    # auth helpers can use the same client as the existing email/password flow.
    html = html.replace(
        'const sb=window.supabase.createClient(SUPABASE_URL,SUPABASE_KEY);',
        '''const sb=window.supabase.createClient(SUPABASE_URL,SUPABASE_KEY);
window.__AI_PLATFORM_SB=sb;
const __aiPlatformSignUp=sb.auth.signUp.bind(sb.auth);
sb.auth.signUp=(credentials,options={})=>__aiPlatformSignUp(credentials,{
  ...options,
  emailRedirectTo:`${window.location.origin}/app/cases`
});''',
        1,
    )

    google_button = '''<button id="googleSignIn" type="button" class="secondary" style="width:100%;margin-top:12px;display:flex;align-items:center;justify-content:center;gap:9px;font-weight:700;"><span aria-hidden="true" style="font-size:17px">G</span><span>Continue with Google</span></button><div style="display:flex;align-items:center;gap:10px;margin:14px 0;color:#94a3b8;font-size:11px"><span style="height:1px;background:#e2e8f0;flex:1"></span><span>OR</span><span style="height:1px;background:#e2e8f0;flex:1"></span></div>'''

    marker = '<form id="authForm">'
    if marker in html and 'id="googleSignIn"' not in html:
        html = html.replace(marker, google_button + marker, 1)

    auth_script = '''<script>
(() => {
  const button = document.getElementById("googleSignIn");
  if (!button) return;
  button.addEventListener("click", async () => {
    button.disabled = true;
    button.querySelector("span:last-child").textContent = "Connecting…";
    const client = window.__AI_PLATFORM_SB;
    try {
      if (!client) throw new Error("Authentication is not configured.");
      const { error } = await client.auth.signInWithOAuth({
        provider: "google",
        options: { redirectTo: `${window.location.origin}/app/cases` },
      });
      if (error) throw error;
    } catch (error) {
      const notice = document.getElementById("authNotice");
      if (notice) { notice.textContent = error?.message || "Google sign-in failed."; notice.hidden = false; }
      button.disabled = false;
      button.querySelector("span:last-child").textContent = "Continue with Google";
    }
  });
})();
</script>'''

    html = html.replace("</body>", auth_script + "</body>", 1)
    return HTMLResponse(content=html, status_code=response.status_code, headers=dict(response.headers))
