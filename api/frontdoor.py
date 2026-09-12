"""Minimal browser front door for AI Platform.

Authentication happens in the browser through Supabase Auth. Provider
credentials and authorization decisions remain entirely server-side; the
browser only forwards the Supabase access token to the existing protected API.
"""

from __future__ import annotations

import html
import json
import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from api.dependencies import default_model_name

app = FastAPI(title="AI Platform App", docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/", response_class=HTMLResponse)
def app_frontdoor() -> str:
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_publishable_key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
    config_error = "" if supabase_url and supabase_publishable_key else (
        "The app is not configured yet. The owner must set SUPABASE_URL and "
        "SUPABASE_PUBLISHABLE_KEY in the Vercel environment, then redeploy."
    )
    return _page(supabase_url, supabase_publishable_key, config_error)


def _page(supabase_url: str, publishable_key: str, config_error: str) -> str:
    # These values are intentionally limited to Supabase's browser-safe URL and
    # publishable key. No provider credential or service-role key is rendered.
    safe_url = html.escape(supabase_url, quote=True)
    safe_key = html.escape(publishable_key, quote=True)
    safe_error = html.escape(config_error)
    safe_model = json.dumps(default_model_name()).replace("<", "\\u003c")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0b5f46">
<meta name="description" content="AI Platform — simple, authenticated access to governed AI model execution.">
<title>AI Platform — Chat</title>
<style>
:root {{ color-scheme: light; --green:#0b5f46; --green-dark:#084a37; --ink:#10231d; --muted:#64756f; --bg:#f5f7f6; --card:#fff; --line:#dfe7e3; --danger:#a52828; }}
* {{ box-sizing:border-box }} body {{ margin:0; background:var(--bg); color:var(--ink); font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
button,input,textarea {{ font:inherit }} button {{ cursor:pointer }}
.shell {{ min-height:100svh; display:flex; flex-direction:column; }}
.top {{ height:64px; display:flex; align-items:center; justify-content:space-between; padding:0 20px; border-bottom:1px solid var(--line); background:rgba(255,255,255,.94); position:sticky; top:0; z-index:2; backdrop-filter:blur(10px); }}
.brand {{ display:flex; gap:10px; align-items:center; font-weight:750; letter-spacing:-.02em; }}
.mark {{ width:32px;height:32px;border-radius:10px;background:var(--green);color:#fff;display:grid;place-items:center;font-size:14px; }}
#userLabel {{ color:var(--muted); font-size:13px; margin-right:10px; max-width:180px; overflow:hidden;text-overflow:ellipsis;white-space:nowrap; }}
.ghost {{ border:1px solid var(--line); background:#fff; color:var(--ink); border-radius:9px; padding:8px 12px; }}
main {{ width:min(900px,100%); margin:0 auto; flex:1; display:flex; flex-direction:column; padding:28px 16px 24px; }}
.hero {{ margin:auto 0 18px; }} h1 {{ margin:0 0 7px; font-size:clamp(28px,5vw,42px); letter-spacing:-.045em; }} .sub {{ margin:0;color:var(--muted); }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:16px; padding:20px; box-shadow:0 8px 28px rgba(16,35,29,.05); }}
.auth {{ width:min(430px,100%); margin:auto; }} .auth h2 {{ margin:0 0 5px; }} .auth p {{ color:var(--muted); margin:0 0 18px; font-size:14px; }}
label {{ display:block; font-size:13px; font-weight:650; margin:12px 0 6px; }} input,textarea {{ width:100%; border:1px solid var(--line); border-radius:10px; padding:12px 13px; outline:none; background:#fff; color:var(--ink); }} input:focus,textarea:focus {{ border-color:var(--green); box-shadow:0 0 0 3px rgba(11,95,70,.1); }}
.primary {{ width:100%; margin-top:16px; border:0; border-radius:10px; padding:12px 15px; color:#fff; background:var(--green); font-weight:700; }} .primary:hover {{ background:var(--green-dark); }} .primary:disabled {{ opacity:.6;cursor:wait; }}
.switch {{ width:100%; border:0; background:transparent; color:var(--green); padding:12px 0 0; font-weight:650; }}
.notice {{ margin-top:12px; padding:11px 12px; border-radius:9px; background:#f8ecec; color:var(--danger); font-size:13px; }}
.chat {{ display:none; min-height:calc(100svh - 112px); flex-direction:column; }}
.messages {{ flex:1; display:flex; flex-direction:column; gap:12px; overflow:auto; padding-bottom:18px; }}
.msg {{ max-width:82%; padding:12px 14px; border-radius:14px; white-space:pre-wrap; overflow-wrap:anywhere; line-height:1.55; }} .user {{ align-self:flex-end; background:var(--green); color:#fff; border-bottom-right-radius:4px; }} .assistant {{ align-self:flex-start; background:#fff; border:1px solid var(--line); border-bottom-left-radius:4px; }}
.composer {{ display:flex; gap:9px; align-items:flex-end; background:var(--card); border:1px solid var(--line); border-radius:15px; padding:9px; box-shadow:0 8px 28px rgba(16,35,29,.07); }} textarea {{ border:0; box-shadow:none; resize:none; min-height:44px; max-height:150px; }} textarea:focus {{ box-shadow:none; }} .send {{ flex:0 0 auto; border:0;border-radius:10px;background:var(--green);color:#fff;padding:11px 15px;font-weight:700; }}
.status {{ color:var(--muted); font-size:12px; min-height:18px; margin:6px 4px 0; }}
@media(max-width:600px) {{ .top {{padding:0 13px}} main {{padding:20px 12px 14px}} .hero {{margin-top:8px}} .msg {{max-width:90%}} #userLabel {{max-width:110px}} }}
</style>
</head>
<body>
<div class="shell">
<header class="top"><div class="brand"><div class="mark">AI</div><span>AI Platform</span></div><div><span id="userLabel"></span><button id="logout" class="ghost" hidden>Log out</button></div></header>
<main>
<section id="auth" class="auth card">
  <h2 id="authTitle">Welcome</h2><p id="authSubtitle">Sign in to use the AI Platform.</p>
  <form id="authForm">
    <label for="email">Email</label><input id="email" type="email" autocomplete="email" required>
    <label for="password">Password</label><input id="password" type="password" autocomplete="current-password" minlength="6" required>
    <button id="authSubmit" class="primary" type="submit">Sign in</button>
  </form>
  <button id="authSwitch" class="switch" type="button">Create an account</button>
  <div id="authNotice" class="notice" hidden></div>
</section>
<section id="chat" class="chat">
  <div class="hero"><h1>Ask AI.</h1><p class="sub">A simple front door to the governed model API.</p></div>
  <div id="messages" class="messages" aria-live="polite"></div>
  <form id="composer">
    <div class="composer"><textarea id="prompt" rows="1" placeholder="Ask anything…" aria-label="Message" required></textarea><button id="send" class="send" type="submit">Send</button></div>
    <div id="status" class="status" role="status"></div>
  </form>
</section>
<div id="configNotice" class="notice" hidden>{safe_error}</div>
</main></div>
<script type="module">
import {{ createClient }} from 'https://esm.sh/@supabase/supabase-js@2';

const SUPABASE_URL = {safe_url!r};
const SUPABASE_PUBLISHABLE_KEY = {safe_key!r};
const MODEL = {safe_model};
const supabase = (SUPABASE_URL && SUPABASE_PUBLISHABLE_KEY) ? createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, {{ auth: {{ persistSession:true, autoRefreshToken:true, detectSessionInUrl:true }} }}) : null;

const $ = id => document.getElementById(id);
const auth = $('auth'), chat = $('chat'), form = $('authForm'), notice = $('authNotice');
let signUpMode = false;
function showNotice(el, text) {{ el.textContent = text; el.hidden = !text; }}
function setBusy(button,busy,label) {{ button.disabled=busy; button.textContent=busy?'Working…':label; }}
function setMode(next) {{ signUpMode=next; $('authTitle').textContent=next?'Create your account':'Welcome'; $('authSubtitle').textContent=next?'Create a secure account to continue.':'Sign in to use the AI Platform.'; $('authSubmit').textContent=next?'Create account':'Sign in'; $('authSwitch').textContent=next?'Already have an account? Sign in':'Create an account'; showNotice(notice,''); }}
function addMessage(role,text) {{ const node=document.createElement('div'); node.className='msg '+role; node.textContent=text; $('messages').appendChild(node); node.scrollIntoView({{behavior:'smooth',block:'end'}}); }}
async function enter(session) {{ auth.style.display='none'; chat.style.display='flex'; $('logout').hidden=false; $('userLabel').textContent=session.user.email || ''; }}
async function boot() {{
  if (!supabase) {{ $('configNotice').hidden=false; form.querySelectorAll('input,button').forEach(x=>x.disabled=true); return; }}
  const {{data}}=await supabase.auth.getSession(); if(data.session) await enter(data.session);
  supabase.auth.onAuthStateChange((_event,session)=>{{ if(session) enter(session); else {{chat.style.display='none';auth.style.display='block';$('logout').hidden=true;$('userLabel').textContent='';}} }});
}}
form.addEventListener('submit',async e=>{{ e.preventDefault(); if(!supabase)return; const email=$('email').value.trim(), password=$('password').value; setBusy($('authSubmit'),true,signUpMode?'Create account':'Sign in'); showNotice(notice,''); try {{
  const result=signUpMode ? await supabase.auth.signUp({{email,password}}) : await supabase.auth.signInWithPassword({{email,password}});
  if(result.error) throw result.error;
  if(signUpMode && !result.data.session) showNotice(notice,'Account created. Check your email to confirm the account, then sign in.');
}} catch(err) {{ showNotice(notice, err?.message || 'Authentication failed.'); }} finally {{ setBusy($('authSubmit'),false,signUpMode?'Create account':'Sign in'); }} }});
$('authSwitch').onclick=()=>setMode(!signUpMode);
$('logout').onclick=async()=>{{ if(supabase) await supabase.auth.signOut(); }};
$('composer').addEventListener('submit',async e=>{{ e.preventDefault(); if(!supabase)return; const input=$('prompt'), text=input.value.trim(); if(!text)return; input.value=''; addMessage('user',text); const status=$('status'); status.textContent='Thinking…'; $('send').disabled=true; try {{
  const {{data,error}}=await supabase.auth.getSession(); if(error||!data.session) throw new Error('Your session has expired. Please sign in again.');
  const response=await fetch('/api/v1/models/generate',{{method:'POST',headers:{{'Content-Type':'application/json','Authorization':'Bearer '+data.session.access_token}},body:JSON.stringify({{model_name:MODEL,messages:[{{role:'user',content:text}}]}})}});
  let body={{}}; try {{ body=await response.json(); }} catch (_) {{}}
  if(!response.ok) {{ const map={{401:'Please sign in again.',403:'Your account is not permitted to use model generation.',429:'The model provider is rate-limited or out of quota.',502:'The model provider returned an error.',503:'The model provider is currently unavailable.',504:'The model provider timed out.'}}; throw new Error(map[response.status] || body.detail || 'The request could not be completed.'); }}
  const answer=body?.message?.content; if(typeof answer!=='string') throw new Error('The model returned an unexpected response.'); addMessage('assistant',answer); status.textContent='';
}} catch(err) {{ addMessage('assistant','Sorry — '+(err?.message || 'Something went wrong.')); status.textContent=''; }} finally {{ $('send').disabled=false; input.focus(); }} }});
$('prompt').addEventListener('keydown',e=>{{ if(e.key==='Enter'&&!e.shiftKey){{e.preventDefault();$('composer').requestSubmit();}} }});
boot();
</script>
</body></html>"""


# Vercel's Python builder accepts an ASGI app named `app`.
