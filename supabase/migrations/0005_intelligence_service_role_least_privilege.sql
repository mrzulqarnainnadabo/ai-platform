-- Harden the durable intelligence tables against Supabase default-grant drift.
-- The application uses the server-side service role only; browser roles already
-- have no access. Keep only the operations the repository actually needs.
-- This also closes the TRUNCATE escape hatch that bypasses row-level triggers.

-- Explicit server grants make the schema reproducible as Supabase moves toward
-- opt-in Data API exposure/default privileges.
grant select, insert, update on public.ai_platform_cases to service_role;
grant select, insert, update on public.ai_platform_assertions to service_role;
grant select, insert on public.ai_platform_evidence to service_role;
grant select, insert on public.ai_platform_audit_events to service_role;

-- Cases and assertions are mutable through the governed service layer, but the
-- application has no delete path for these records.
revoke delete, truncate on public.ai_platform_cases from service_role;
revoke delete, truncate on public.ai_platform_assertions from service_role;

-- Evidence and audit are append-only. The database triggers already reject
-- UPDATE/DELETE; revoking those privileges plus TRUNCATE makes that invariant
-- hold even if a trigger is bypassed by a bulk operation.
revoke update, delete, truncate on public.ai_platform_evidence from service_role;
revoke update, delete, truncate on public.ai_platform_audit_events from service_role;

-- Keep client access explicitly closed.
revoke all on public.ai_platform_cases from anon, authenticated, public;
revoke all on public.ai_platform_assertions from anon, authenticated, public;
revoke all on public.ai_platform_evidence from anon, authenticated, public;
revoke all on public.ai_platform_audit_events from anon, authenticated, public;
