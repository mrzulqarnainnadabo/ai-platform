-- Durable execution integrity: exactly-once settlement, cost records, and runtime audit events.
-- This migration is additive and preserves existing runtime data.

create table if not exists public.ai_platform_audit_events (
  id text primary key,
  tenant_id text not null,
  actor_subject text not null,
  action text not null,
  object_type text not null,
  object_id text not null,
  payload_digest text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.ai_platform_audit_events enable row level security;
revoke all on table public.ai_platform_audit_events from anon, authenticated, public;
grant all on table public.ai_platform_audit_events to service_role;

create index if not exists ai_platform_audit_events_tenant_created_idx
  on public.ai_platform_audit_events (tenant_id, created_at desc);
create index if not exists ai_platform_audit_events_object_idx
  on public.ai_platform_audit_events (object_type, object_id, created_at desc);
create index if not exists ai_platform_audit_events_action_idx
  on public.ai_platform_audit_events (action, created_at desc);

-- There must be exactly one final cost record for a run.
create unique index if not exists ai_platform_cost_records_run_id_uidx
  on public.ai_platform_cost_records (run_id);

create or replace function public.reserve_ai_platform_budget(
  p_tenant_id text,
  p_subject_id text,
  p_model_id text,
  p_requests_per_minute integer,
  p_tokens_per_day bigint,
  p_requested_tokens bigint,
  p_request_id text
) returns jsonb
language plpgsql
security invoker
set search_path = public, extensions, pg_temp
as $$
declare
  now_ts timestamptz := now();
  minute_start timestamptz := date_trunc('minute', now_ts);
  day_start timestamptz := date_trunc('day', now_ts);
  minute_requests integer;
  day_tokens bigint;
  lock_key bigint;
begin
  if p_requested_tokens <= 0 then
    raise exception 'requested tokens must be positive';
  end if;

  lock_key := hashtextextended(concat_ws(':', p_tenant_id, p_subject_id, p_model_id), 0);
  perform pg_advisory_xact_lock(lock_key);

  select coalesce(sum(requests), 0)
    into minute_requests
    from public.ai_platform_usage_counters
   where tenant_id = p_tenant_id
     and subject_id = p_subject_id
     and model_id = p_model_id
     and window_start = minute_start;

  select coalesce(sum(reserved_tokens), 0)
    into day_tokens
    from public.ai_platform_usage_counters
   where tenant_id = p_tenant_id
     and subject_id = p_subject_id
     and model_id = p_model_id
     and window_start >= day_start;

  if minute_requests >= p_requests_per_minute then
    insert into public.ai_platform_audit_events
      (id, tenant_id, actor_subject, action, object_type, object_id, metadata)
    values
      (gen_random_uuid()::text, p_tenant_id, p_subject_id, 'budget.denied', 'budget', p_request_id,
       jsonb_build_object('model_id', p_model_id, 'reason', 'request rate limit exceeded'));
    return jsonb_build_object('allowed', false, 'reason', 'request rate limit exceeded');
  end if;

  if day_tokens + p_requested_tokens > p_tokens_per_day then
    insert into public.ai_platform_audit_events
      (id, tenant_id, actor_subject, action, object_type, object_id, metadata)
    values
      (gen_random_uuid()::text, p_tenant_id, p_subject_id, 'budget.denied', 'budget', p_request_id,
       jsonb_build_object('model_id', p_model_id, 'reason', 'daily token budget exceeded'));
    return jsonb_build_object('allowed', false, 'reason', 'daily token budget exceeded');
  end if;

  insert into public.ai_platform_usage_counters
    (tenant_id, subject_id, model_id, window_start, requests, reserved_tokens)
  values
    (p_tenant_id, p_subject_id, p_model_id, minute_start, 1, p_requested_tokens)
  on conflict (tenant_id, subject_id, model_id, window_start)
  do update set
    requests = public.ai_platform_usage_counters.requests + 1,
    reserved_tokens = public.ai_platform_usage_counters.reserved_tokens + excluded.reserved_tokens;

  insert into public.ai_platform_budget_reservations
    (id, tenant_id, subject_id, model_id, reserved_tokens)
  values
    (p_request_id::uuid, p_tenant_id, p_subject_id, p_model_id, p_requested_tokens);

  insert into public.ai_platform_audit_events
    (id, tenant_id, actor_subject, action, object_type, object_id, metadata)
  values
    (gen_random_uuid()::text, p_tenant_id, p_subject_id, 'budget.reserved', 'budget', p_request_id,
     jsonb_build_object('model_id', p_model_id, 'reserved_tokens', p_requested_tokens));

  return jsonb_build_object('allowed', true);
end;
$$;

create or replace function public.settle_ai_platform_budget(
  p_tenant_id text,
  p_subject_id text,
  p_model_id text,
  p_request_id text,
  p_reserved_tokens bigint,
  p_actual_tokens bigint
) returns void
language plpgsql
security invoker
set search_path = public, extensions, pg_temp
as $$
declare
  v_reserved_tokens bigint;
  v_created_at timestamptz;
  v_actual_tokens bigint := greatest(0, p_actual_tokens);
  v_delta bigint;
  v_updated integer;
begin
  -- The reservation row is the source of truth. The caller-supplied reserved
  -- amount is retained for API compatibility but is not trusted for settlement.
  update public.ai_platform_budget_reservations
     set actual_tokens = v_actual_tokens,
         status = 'settled',
         settled_at = now()
   where id = p_request_id::uuid
     and tenant_id = p_tenant_id
     and subject_id = p_subject_id
     and model_id = p_model_id
     and status = 'reserved'
   returning reserved_tokens, created_at
        into v_reserved_tokens, v_created_at;

  get diagnostics v_updated = row_count;

  -- Already-settled/released reservations are idempotent no-ops. Crucially,
  -- the aggregate counter is only changed when this transaction performed the
  -- reserved -> settled transition itself.
  if v_updated = 0 then
    return;
  end if;

  v_delta := greatest(0, v_reserved_tokens) - v_actual_tokens;

  if v_delta > 0 then
    update public.ai_platform_usage_counters
       set reserved_tokens = greatest(0, reserved_tokens - v_delta)
     where tenant_id = p_tenant_id
       and subject_id = p_subject_id
       and model_id = p_model_id
       and window_start = date_trunc('minute', v_created_at);
  end if;

  insert into public.ai_platform_audit_events
    (id, tenant_id, actor_subject, action, object_type, object_id, metadata)
  values
    (gen_random_uuid()::text, p_tenant_id, p_subject_id, 'budget.settled', 'budget', p_request_id,
     jsonb_build_object('model_id', p_model_id, 'reserved_tokens', v_reserved_tokens,
                        'actual_tokens', v_actual_tokens, 'released_tokens', greatest(0, v_delta)));
end;
$$;

create or replace function public.complete_ai_platform_run(
  p_run_id uuid,
  p_step_id uuid,
  p_call_id uuid,
  p_status text,
  p_usage jsonb,
  p_cost_usd numeric,
  p_latency_ms numeric,
  p_error_type text
) returns void
language plpgsql
set search_path = public, extensions, pg_temp
as $$
declare
  v_tenant_id text;
  v_subject_id text;
  v_model_id text;
  v_updated integer;
begin
  if p_status not in ('completed', 'failed', 'cancelled') then
    raise exception 'invalid run completion status: %', p_status;
  end if;

  -- Only the running -> terminal transition may finalize accounting. A second
  -- completion/failure call is therefore an idempotent no-op.
  update public.ai_platform_runs
     set status = p_status,
         completed_at = now()
   where id = p_run_id
     and status = 'running'
   returning tenant_id, subject_id, model_id
        into v_tenant_id, v_subject_id, v_model_id;

  get diagnostics v_updated = row_count;
  if v_updated = 0 then
    return;
  end if;

  update public.ai_platform_provider_calls
     set status = p_status,
         usage = coalesce(p_usage, '{}'::jsonb),
         error_type = p_error_type,
         latency_ms = p_latency_ms,
         completed_at = now()
   where id = p_call_id
     and run_id = p_run_id
     and step_id = p_step_id;

  update public.ai_platform_run_steps
     set status = p_status,
         completed_at = now()
   where id = p_step_id
     and run_id = p_run_id;

  insert into public.ai_platform_cost_records
    (run_id, tenant_id, model_id, prompt_tokens, completion_tokens, total_tokens, cost_usd)
  values
    (p_run_id, v_tenant_id, v_model_id,
     coalesce((p_usage->>'prompt_tokens')::integer, 0),
     coalesce((p_usage->>'completion_tokens')::integer, 0),
     coalesce((p_usage->>'total_tokens')::integer, 0),
     coalesce(p_cost_usd, 0))
  on conflict (run_id) do nothing;

  insert into public.ai_platform_audit_events
    (id, tenant_id, actor_subject, action, object_type, object_id, metadata)
  values
    (gen_random_uuid()::text, v_tenant_id, v_subject_id,
     case when p_status = 'completed' then 'run.completed' else 'run.failed' end,
     'run', p_run_id::text,
     jsonb_build_object('model_id', v_model_id, 'status', p_status,
                        'usage', coalesce(p_usage, '{}'::jsonb),
                        'cost_usd', coalesce(p_cost_usd, 0),
                        'error_type', p_error_type));
end;
$$;

-- Runtime RPCs are server-side implementation details. They do not need to be
-- callable by browser anon/authenticated roles.
revoke execute on function public.reserve_ai_platform_budget(text, text, text, integer, bigint, bigint, text) from public, anon, authenticated;
revoke execute on function public.settle_ai_platform_budget(text, text, text, text, bigint, bigint) from public, anon, authenticated;
revoke execute on function public.complete_ai_platform_run(uuid, uuid, uuid, text, jsonb, numeric, numeric, text) from public, anon, authenticated;
grant execute on function public.reserve_ai_platform_budget(text, text, text, integer, bigint, bigint, text) to service_role;
grant execute on function public.settle_ai_platform_budget(text, text, text, text, bigint, bigint) to service_role;
grant execute on function public.complete_ai_platform_run(uuid, uuid, uuid, text, jsonb, numeric, numeric, text) to service_role;
