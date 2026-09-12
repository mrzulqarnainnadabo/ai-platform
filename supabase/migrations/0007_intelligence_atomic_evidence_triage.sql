-- Atomic persistence boundaries for evidence attachment and AI triage.
-- Both functions are SECURITY DEFINER and executable only by service_role.
-- All writes occur in the function transaction; any exception rolls back the aggregate.

create or replace function public.attach_evidence_bundle(
  p_evidence jsonb,
  p_audit jsonb,
  p_assertion_id uuid default null
)
returns public.ai_platform_evidence
language plpgsql
security definer
set search_path = public
as $$
declare
  created_evidence public.ai_platform_evidence;
  evidence_case_id uuid;
  evidence_tenant_id text;
  audit_object_id text;
  audit_tenant_id text;
  assertion_tenant_id text;
begin
  evidence_case_id := (p_evidence->>'case_id')::uuid;
  evidence_tenant_id := p_evidence->>'tenant_id';
  audit_object_id := p_audit->>'object_id';
  audit_tenant_id := p_audit->>'tenant_id';

  if evidence_case_id is null or evidence_tenant_id is null then
    raise exception 'evidence case and tenant are required';
  end if;
  if audit_object_id <> evidence_case_id::text or audit_tenant_id <> evidence_tenant_id then
    raise exception 'evidence bundle tenant references do not match case';
  end if;
  if not exists (select 1 from public.ai_platform_cases c where c.id = evidence_case_id and c.tenant_id = evidence_tenant_id) then
    raise exception 'evidence case does not exist for tenant';
  end if;

  if p_assertion_id is not null then
    if (p_evidence->>'assertion_id')::uuid <> p_assertion_id then
      raise exception 'evidence assertion reference does not match';
    end if;
    select a.tenant_id into assertion_tenant_id
    from public.ai_platform_assertions a
    where a.id = p_assertion_id and a.case_id = evidence_case_id;
    if assertion_tenant_id is null or assertion_tenant_id <> evidence_tenant_id then
      raise exception 'assertion does not belong to evidence case tenant';
    end if;
  elsif p_evidence->>'assertion_id' is not null then
    raise exception 'linked evidence requires assertion id';
  end if;

  insert into public.ai_platform_evidence (
    id, case_id, tenant_id, assertion_id, body, source_type, source_uri, note,
    created_by_subject, created_at
  ) values (
    (p_evidence->>'id')::uuid,
    evidence_case_id,
    evidence_tenant_id,
    p_assertion_id,
    p_evidence->>'body',
    p_evidence->>'source_type',
    p_evidence->>'source_uri',
    p_evidence->>'note',
    p_evidence->>'created_by_subject',
    (p_evidence->>'created_at')::timestamptz
  ) returning * into created_evidence;

  if p_assertion_id is not null then
    update public.ai_platform_assertions
    set evidence_ids = case
      when (evidence_ids @> jsonb_build_array((p_evidence->>'id'))) then evidence_ids
      else evidence_ids || jsonb_build_array((p_evidence->>'id'))
    end
    where id = p_assertion_id and case_id = evidence_case_id and tenant_id = evidence_tenant_id;
    if not found then
      raise exception 'assertion disappeared during evidence attachment';
    end if;
  end if;

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

  return created_evidence;
end;
$$;

revoke execute on function public.attach_evidence_bundle(jsonb, jsonb, uuid) from public;
revoke execute on function public.attach_evidence_bundle(jsonb, jsonb, uuid) from anon;
revoke execute on function public.attach_evidence_bundle(jsonb, jsonb, uuid) from authenticated;
grant execute on function public.attach_evidence_bundle(jsonb, jsonb, uuid) to service_role;

create or replace function public.save_triage_bundle(
  p_case jsonb,
  p_assertions jsonb,
  p_audit jsonb
)
returns public.ai_platform_cases
language plpgsql
security definer
set search_path = public
as $$
declare
  updated_case public.ai_platform_cases;
  case_id uuid;
  case_tenant_id text;
  audit_object_id text;
  audit_tenant_id text;
  item jsonb;
  assertion_id uuid;
begin
  case_id := (p_case->>'id')::uuid;
  case_tenant_id := p_case->>'tenant_id';
  audit_object_id := p_audit->>'object_id';
  audit_tenant_id := p_audit->>'tenant_id';

  if case_id is null or case_tenant_id is null then
    raise exception 'triage case and tenant are required';
  end if;
  if audit_object_id <> case_id::text or audit_tenant_id <> case_tenant_id then
    raise exception 'triage bundle tenant references do not match case';
  end if;
  if not exists (select 1 from public.ai_platform_cases c where c.id = case_id and c.tenant_id = case_tenant_id) then
    raise exception 'triage case does not exist for tenant';
  end if;

  for item in select value from jsonb_array_elements(coalesce(p_assertions, '[]'::jsonb)) loop
    assertion_id := (item->>'id')::uuid;
    if assertion_id is null or (item->>'case_id')::uuid <> case_id or item->>'tenant_id' <> case_tenant_id then
      raise exception 'triage assertion references do not match case';
    end if;
    insert into public.ai_platform_assertions (
      id, case_id, tenant_id, text, kind, created_by,
      requires_evidence, evidence_ids, created_at
    ) values (
      assertion_id, case_id, case_tenant_id, item->>'text', item->>'kind', item->>'created_by',
      coalesce((item->>'requires_evidence')::boolean, true),
      coalesce(item->'evidence_ids', '[]'::jsonb),
      (item->>'created_at')::timestamptz
    );
  end loop;

  update public.ai_platform_cases
  set status = p_case->>'status',
      missing_evidence_questions = coalesce(p_case->'missing_evidence_questions', '[]'::jsonb),
      updated_at = (p_case->>'updated_at')::timestamptz
  where id = case_id and tenant_id = case_tenant_id
  returning * into updated_case;
  if not found then
    raise exception 'triage case disappeared during update';
  end if;

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

  return updated_case;
end;
$$;

revoke execute on function public.save_triage_bundle(jsonb, jsonb, jsonb) from public;
revoke execute on function public.save_triage_bundle(jsonb, jsonb, jsonb) from anon;
revoke execute on function public.save_triage_bundle(jsonb, jsonb, jsonb) from authenticated;
grant execute on function public.save_triage_bundle(jsonb, jsonb, jsonb) to service_role;
