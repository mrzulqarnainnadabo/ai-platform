create or replace function public.reserve_ai_platform_budget(p_tenant_id text, p_subject_id text, p_model_id text, p_requests_per_minute integer, p_tokens_per_day bigint, p_requested_tokens bigint, p_request_id text) returns jsonb language plpgsql security invoker set search_path = public, extensions, pg_temp as $$
declare now_ts timestamptz := now(); minute_start timestamptz := date_trunc('minute', now_ts); day_start timestamptz := date_trunc('day', now_ts); minute_requests integer; day_tokens bigint; lock_key bigint;
begin
  if p_requested_tokens <= 0 then raise exception 'requested tokens must be positive'; end if;
  lock_key := hashtextextended(concat_ws(':',p_tenant_id,p_subject_id,p_model_id),0);
  perform pg_advisory_xact_lock(lock_key);
  select coalesce(sum(requests),0) into minute_requests from public.ai_platform_usage_counters where tenant_id=p_tenant_id and subject_id=p_subject_id and model_id=p_model_id and window_start=minute_start;
  select coalesce(sum(reserved_tokens),0) into day_tokens from public.ai_platform_usage_counters where tenant_id=p_tenant_id and subject_id=p_subject_id and model_id=p_model_id and window_start>=day_start;
  if minute_requests >= p_requests_per_minute then return jsonb_build_object('allowed',false,'reason','request rate limit exceeded'); end if;
  if day_tokens + p_requested_tokens > p_tokens_per_day then return jsonb_build_object('allowed',false,'reason','daily token budget exceeded'); end if;
  insert into public.ai_platform_usage_counters(tenant_id,subject_id,model_id,window_start,requests,reserved_tokens) values(p_tenant_id,p_subject_id,p_model_id,minute_start,1,p_requested_tokens)
  on conflict (tenant_id,subject_id,model_id,window_start) do update set requests=public.ai_platform_usage_counters.requests+1,reserved_tokens=public.ai_platform_usage_counters.reserved_tokens+excluded.reserved_tokens;
  insert into public.ai_platform_budget_reservations(id,tenant_id,subject_id,model_id,reserved_tokens) values(p_request_id::uuid,p_tenant_id,p_subject_id,p_model_id,p_requested_tokens);
  return jsonb_build_object('allowed',true);
end; $$;
