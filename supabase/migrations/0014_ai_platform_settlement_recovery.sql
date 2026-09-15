-- Recover a reservation durably when run completion succeeds after a settlement RPC
-- failed or its response was lost. The settlement function is already idempotent,
-- so this is safe when the application settled first.
--
-- This does not attempt to finalize abandoned `running` runs: doing so would
-- require a timeout/heartbeat policy that this architecture does not currently
-- define. Recovery is therefore tied to an authoritative terminal run state.

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
security invoker
set search_path = public, extensions, pg_temp
as $$
declare
  v_tenant_id text;
  v_subject_id text;
  v_model_id text;
  v_updated integer;
  v_settlement_tokens bigint;
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

  -- Durable settlement recovery: if application-level settlement failed before
  -- completion, the terminal run state is authoritative enough to settle the
  -- reservation in this same transaction. For a successful run use recorded
  -- total usage; for failed/cancelled execution release the full reservation
  -- estimate, matching RunEngine's existing failure-path semantics.
  v_settlement_tokens := case
    when p_status = 'completed'
      then greatest(0, coalesce((p_usage->>'total_tokens')::bigint, 0))
    else 0
  end;

  perform public.settle_ai_platform_budget(
    v_tenant_id,
    v_subject_id,
    v_model_id,
    p_run_id::text,
    0,
    v_settlement_tokens
  );

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

revoke execute on function public.complete_ai_platform_run(uuid, uuid, uuid, text, jsonb, numeric, numeric, text) from public, anon, authenticated;
grant execute on function public.complete_ai_platform_run(uuid, uuid, uuid, text, jsonb, numeric, numeric, text) to service_role;
