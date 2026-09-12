-- Atomic case creation boundary for the intelligence vertical slice.
-- The function is SECURITY DEFINER so the server-side service role can commit
-- the case, initial assertion, and audit event as one PostgreSQL transaction.
-- It does not grant browser roles access and does not weaken append-only guards.

create or replace function public.create_case_bundle(
  p_case jsonb,
  p_assertion jsonb,
  p_audit jsonb
)
returns public.ai_platform_cases
language plpgsql
security definer
set search_path = public
as $$
declare
  created_case public.ai_platform_cases;
  case_id uuid;
  assertion_case_id uuid;
  audit_object_id text;
  case_tenant_id text;
  assertion_tenant_id text;
  audit_tenant_id text;
begin
  case_id := (p_case->>'id')::uuid;
  assertion_case_id := (p_assertion->>'case_id')::uuid;
  audit_object_id := p_audit->>'object_id';
  case_tenant_id := p_case->>'tenant_id';
  assertion_tenant_id := p_assertion->>'tenant_id';
  audit_tenant_id := p_audit->>'tenant_id';

  if case_id is null or assertion_case_id is null then
    raise exception 'case bundle ids are required';
  end if;
  if assertion_case_id <> case_id or audit_object_id <> case_id::text then
    raise exception 'case bundle references do not match case';
  end if;
  if case_tenant_id is null or assertion_tenant_id <> case_tenant_id or audit_tenant_id <> case_tenant_id then
    raise exception 'case bundle tenant references do not match case';
  end if;

  insert into public.ai_platform_cases (
    id, tenant_id, created_by_subject, title, summary, status,
    missing_evidence_questions, created_at, updated_at
  ) values (
    case_id,
    case_tenant_id,
    p_case->>'created_by_subject',
    p_case->>'title',
    p_case->>'summary',
    p_case->>'status',
    coalesce(p_case->'missing_evidence_questions', '[]'::jsonb),
    (p_case->>'created_at')::timestamptz,
    (p_case->>'updated_at')::timestamptz
  ) returning * into created_case;

  insert into public.ai_platform_assertions (
    id, case_id, tenant_id, text, kind, created_by,
    requires_evidence, evidence_ids, created_at
  ) values (
    (p_assertion->>'id')::uuid,
    assertion_case_id,
    case_tenant_id,
    p_assertion->>'text',
    p_assertion->>'kind',
    p_assertion->>'created_by',
    coalesce((p_assertion->>'requires_evidence')::boolean, true),
    coalesce(p_assertion->'evidence_ids', '[]'::jsonb),
    (p_assertion->>'created_at')::timestamptz
  );

  insert into public.ai_platform_audit_events (
    id, tenant_id, actor_subject, action, object_type, object_id,
    payload_digest, metadata, created_at
  ) values (
    (p_audit->>'id')::uuid,
    audit_tenant_id,
    p_audit->>'actor_subject',
    p_audit->>'action',
    p_audit->>'object_type',
    audit_object_id,
    p_audit->>'payload_digest',
    coalesce(p_audit->'metadata', '{}'::jsonb),
    (p_audit->>'created_at')::timestamptz
  );

  return created_case;
end;
$$;

revoke execute on function public.create_case_bundle(jsonb, jsonb, jsonb) from public;
revoke execute on function public.create_case_bundle(jsonb, jsonb, jsonb) from anon;
revoke execute on function public.create_case_bundle(jsonb, jsonb, jsonb) from authenticated;
grant execute on function public.create_case_bundle(jsonb, jsonb, jsonb) to service_role;
