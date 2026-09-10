# Supabase application authentication and authorization

The AI Platform keeps Supabase at the application boundary. `ai_platform.core`, policy evaluation, runtime execution, and provider adapters do not import Supabase.

## Trust boundary

```text
Supabase Auth JWT
      |
      v
SupabaseAuthContextProvider
      |
      | verified subject + server-controlled tenant/capability claims
      v
AuthorizationContext
      |
      v
AuthorizedModelRuntime
      |
      v
Deterministic Policy
      |
      v
ModelRuntime -> ProviderRegistry -> Provider
```

Supabase JWT verification is performed through `supabase-py`'s `auth.get_claims()` path. Supabase documents `get_claims()` as the preferred verified-JWT path; with asymmetric signing keys it verifies against the project's JWKS endpoint, while symmetric signing can fall back to Auth-server verification.

## Authorization claims

The application adapter accepts only:

- `ai_platform_tenant_id`
- `ai_platform_permissions`

These can be emitted as top-level custom claims by the Custom Access Token Hook or nested under `app_metadata`. `user_metadata` is never used for authorization.

A missing tenant is an authentication failure at the application boundary. Unknown capability strings are ignored rather than granted. A valid user with no recognized capabilities remains authenticated but cannot invoke the model runtime.

## Supabase setup

1. Create the Supabase project.
2. Apply `supabase/migrations/0001_platform_authz.sql`.
3. Enable the `custom_access_token_hook` under **Authentication > Hooks**.
4. Create an application membership for a user in `ai_platform_memberships`.
5. Use `platform_user` or another explicitly assigned role.
6. Confirm the user's next access token contains `ai_platform_tenant_id` and `ai_platform_permissions`.
7. Configure Vercel with:
   - `SUPABASE_URL`
   - `SUPABASE_PUBLISHABLE_KEY`
   - `AI_PLATFORM_TENANT_CLAIM=ai_platform_tenant_id`
   - `AI_PLATFORM_PERMISSIONS_CLAIM=ai_platform_permissions`

Do **not** put a Supabase secret/service-role key in the browser or repository. The current application auth adapter does not require one.

## Multi-tenant behavior

Phase 1 of this boundary intentionally fails closed when a user has zero or multiple active tenant memberships. Tenant switching will be implemented later as an explicit, authenticated tenant-selection flow; the API must not infer a tenant from arbitrary request JSON.

## Model API

`POST /api/v1/models/generate` requires:

```http
Authorization: Bearer <supabase-access-token>
Content-Type: application/json
```

The request body cannot grant itself permissions, change tenant identity, or supply human approval. The verified authorization context is the only source of authority.

If the caller is authenticated but lacks `model.generate`, the deterministic policy denies execution before the provider is called.

## Production gate

The Vercel host is now structurally protected, but it is not yet production-ready until a real Supabase project is connected, the migration/hook is exercised with real users, provider secrets are configured in Vercel, and end-to-end authorization/provider/rollback tests pass.
