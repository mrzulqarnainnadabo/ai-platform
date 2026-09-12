# Browser Front Door

The minimum consumer-facing product surface is available at `/app` on the same Vercel host.

## User flow

1. Open `/app`.
2. Create an account or sign in with Supabase Auth email/password.
3. If the account requires email confirmation, confirm the email and sign in again.
4. Enter a prompt and press **Send**. The browser sends only the Supabase access token to `POST /api/v1/models/generate`.
5. Log out from the header when finished.

## Security boundary

- Supabase Auth is the only browser-side authentication client.
- The Supabase URL and publishable key are browser-safe configuration; no provider API key is rendered.
- The browser does not manufacture tenant IDs or permissions.
- The existing `require_auth` → `AuthorizationContext` → `AuthorizedModelRuntime` path remains the authorization boundary.
- `model.generate` must be present in trusted JWT claims for model execution.
- Provider credentials remain server-side in Vercel environment variables.
- A signed-in user without an active platform membership receives the existing 403 response; signup does not automatically grant model authority.

## Supabase requirements

The existing Custom Access Token Hook must remain enabled and must emit, for a user with exactly one active membership:

- `ai_platform_tenant_id`
- `ai_platform_permissions` containing `model.generate`
- `ai_platform_permissions` containing `model.stream` if streaming is later enabled in the UI

The current database has the hook function and the existing platform roles grant both model capabilities. Membership provisioning remains an explicit authorization decision rather than an automatic side effect of public signup.

## Owner setup

The host needs these existing values in the Vercel **Production** environment:

- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- the existing server-side provider credential(s), such as `OPENAI_API_KEY` or `XAI_API_KEY`

After changing production environment variables, create a new production deployment.

No provider key or access token should be pasted into source control or chat.
