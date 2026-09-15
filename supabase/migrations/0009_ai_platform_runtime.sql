-- P0/P1 runtime foundation: durable runs, usage budgets, approvals and pgvector knowledge.
create extension if not exists vector;

create table if not exists public.ai_platform_usage_counters (
  tenant_id text not null,
  subject_id text not null,
  model_id text not null,
  window_start timestamptz not null,
  requests integer not null default 0,
  reserved_tokens bigint not null default 0,
  primary key (tenant_id, subject_id, model_id, window_start)
);

create table if not exists public.ai_platform_budget_reservations (
  id uuid primary key,
  tenant_id text not null,
  subject_id text not null,
  model_id text not null,
  reserved_tokens bigint not null,
  actual_tokens bigint,
  status text not null default 'reserved' check (status in ('reserved','settled','released')),
  created_at timestamptz not null default now(),
  settled_at timestamptz
);

create table if not exists public.ai_platform_runs (
  id uuid primary key,
  tenant_id text not null,
  subject_id text not null,
  model_id text not null,
  provider text not null,
  model text not null,
  trace_id text not null,
  status text not null check (status in ('running','completed','failed','cancelled')),
  created_at timestamptz not null default now(),
  completed_at timestamptz
);

create table if not exists public.ai_platform_run_steps (
  id uuid primary key,
  run_id uuid not null references public.ai_platform_runs(id) on delete cascade,
  step_type text not null,
  status text not null default 'running',
  created_at timestamptz not null default now(),
  completed_at timestamptz
);

create table if not exists public.ai_platform_provider_calls (
  id uuid primary key,
  run_id uuid not null references public.ai_platform_runs(id) on delete cascade,
  step_id uuid not null references public.ai_platform_run_steps(id) on delete cascade,
  provider text not null,
  model text not null,
  status text not null default 'running',
  usage jsonb not null default '{}'::jsonb,
  error_type text,
  latency_ms numeric,
  created_at timestamptz not null default now(),
  completed_at timestamptz
);

create table if not exists public.ai_platform_cost_records (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.ai_platform_runs(id) on delete cascade,
  tenant_id text not null,
  model_id text not null,
  prompt_tokens integer not null default 0,
  completion_tokens integer not null default 0,
  total_tokens integer not null default 0,
  cost_usd numeric(18,8) not null default 0,
  created_at timestamptz not null default now()
);

create table if not exists public.ai_platform_approvals (
  id uuid primary key default gen_random_uuid(),
  tenant_id text not null,
  subject_id text not null,
  capability text not null,
  run_id uuid references public.ai_platform_runs(id) on delete set null,
  status text not null default 'pending' check (status in ('pending','approved','rejected','expired')),
  requested_at timestamptz not null default now(),
  expires_at timestamptz,
  decided_at timestamptz,
  approver_id text,
  metadata jsonb not null default '{}'::jsonb
);

create table if not exists public.ai_platform_documents (
  id uuid primary key default gen_random_uuid(),
  tenant_id text not null,
  subject_id text not null,
  name text not null,
  source_uri text,
  mime_type text,
  content_sha256 text,
  created_at timestamptz not null default now()
);

create table if not exists public.ai_platform_document_chunks (
  id uuid primary key default gen_random_uuid(),
  tenant_id text not null,
  document_id uuid not null references public.ai_platform_documents(id) on delete cascade,
  chunk_index integer not null,
  content text not null,
  embedding vector(384),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique(document_id, chunk_index)
);

create index if not exists ai_platform_runs_tenant_created_idx on public.ai_platform_runs(tenant_id, created_at desc);
create index if not exists ai_platform_approvals_tenant_status_idx on public.ai_platform_approvals(tenant_id, status, requested_at desc);
create index if not exists ai_platform_chunks_tenant_idx on public.ai_platform_document_chunks(tenant_id, document_id);
create index if not exists ai_platform_chunks_embedding_idx on public.ai_platform_document_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);

alter table public.ai_platform_usage_counters enable row level security;
alter table public.ai_platform_budget_reservations enable row level security;
alter table public.ai_platform_runs enable row level security;
alter table public.ai_platform_run_steps enable row level security;
alter table public.ai_platform_provider_calls enable row level security;
alter table public.ai_platform_cost_records enable row level security;
alter table public.ai_platform_approvals enable row level security;
alter table public.ai_platform_documents enable row level security;
alter table public.ai_platform_document_chunks enable row level security;

-- The platform uses the server credential for these tables. Direct client access remains blocked.
revoke all on table public.ai_platform_usage_counters, public.ai_platform_budget_reservations,
  public.ai_platform_runs, public.ai_platform_run_steps, public.ai_platform_provider_calls,
  public.ai_platform_cost_records, public.ai_platform_approvals, public.ai_platform_documents,
  public.ai_platform_document_chunks from anon, authenticated;

create or replace function public.reserve_ai_platform_budget(
  p_tenant_id text, p_subject_id text, p_model_id text,
  p_requests_per_minute integer, p_tokens_per_day bigint,
  p_requested_tokens bigint, p_request_id text
) returns jsonb language plpgsql security invoker as $$
declare
  now_ts timestamptz := now();
  minute_start timestamptz := date_trunc('minute', now_ts);
  day_start timestamptz := date_trunc('day', now_ts);
  minute_requests integer;
  day_tokens bigint;
begin
  if p_requested_tokens <= 0 then raise exception 'requested tokens must be positive'; end if;

  select coalesce(sum(requests),0), coalesce(sum(reserved_tokens),0)
    into minute_requests, day_tokens
  from public.ai_platform_usage_counters
  where tenant_id = p_tenant_id and subject_id = p_subject_id and model_id = p_model_id
    and window_start >= day_start;

  if minute_requests >= p_requests_per_minute then
    return jsonb_build_object('allowed', false, 'reason', 'request rate limit exceeded');
  end if;
  if day_tokens + p_requested_tokens > p_tokens_per_day then
    return jsonb_build_object('allowed', false, 'reason', 'daily token budget exceeded');
  end if;

  insert into public.ai_platform_usage_counters(tenant_id, subject_id, model_id, window_start, requests, reserved_tokens)
  values(p_tenant_id, p_subject_id, p_model_id, minute_start, 1, p_requested_tokens)
  on conflict (tenant_id, subject_id, model_id, window_start)
  do update set requests = public.ai_platform_usage_counters.requests + 1,
                reserved_tokens = public.ai_platform_usage_counters.reserved_tokens + excluded.reserved_tokens;

  insert into public.ai_platform_budget_reservations(id, tenant_id, subject_id, model_id, reserved_tokens)
  values(p_request_id::uuid, p_tenant_id, p_subject_id, p_model_id, p_requested_tokens);

  return jsonb_build_object('allowed', true);
end;
$$;

create or replace function public.settle_ai_platform_budget(
  p_tenant_id text, p_subject_id text, p_model_id text,
  p_request_id text, p_reserved_tokens bigint, p_actual_tokens bigint
) returns void language plpgsql security invoker as $$
declare
  delta bigint := greatest(0, p_reserved_tokens) - greatest(0, p_actual_tokens);
  minute_start timestamptz := date_trunc('minute', now());
begin
  update public.ai_platform_budget_reservations
     set actual_tokens = greatest(0, p_actual_tokens), status = 'settled', settled_at = now()
   where id = p_request_id::uuid and tenant_id = p_tenant_id and subject_id = p_subject_id and model_id = p_model_id;
  if delta > 0 then
    update public.ai_platform_usage_counters
       set reserved_tokens = greatest(0, reserved_tokens - delta)
     where tenant_id = p_tenant_id and subject_id = p_subject_id and model_id = p_model_id
       and window_start = minute_start;
  end if;
end;
$$;

create or replace function public.complete_ai_platform_run(
  p_run_id uuid, p_step_id uuid, p_call_id uuid, p_status text,
  p_usage jsonb, p_cost_usd numeric, p_latency_ms numeric, p_error_type text
) returns void language plpgsql security invoker as $$
begin
  update public.ai_platform_provider_calls set status = p_status, usage = coalesce(p_usage,'{}'::jsonb),
    error_type = p_error_type, latency_ms = p_latency_ms, completed_at = now() where id = p_call_id;
  update public.ai_platform_run_steps set status = p_status, completed_at = now() where id = p_step_id;
  update public.ai_platform_runs set status = p_status, completed_at = now() where id = p_run_id;
  insert into public.ai_platform_cost_records(run_id, tenant_id, model_id, prompt_tokens, completion_tokens, total_tokens, cost_usd)
  select r.id, r.tenant_id, r.model_id,
    coalesce((p_usage->>'prompt_tokens')::integer,0), coalesce((p_usage->>'completion_tokens')::integer,0),
    coalesce((p_usage->>'total_tokens')::integer,0), coalesce(p_cost_usd,0)
  from public.ai_platform_runs r where r.id = p_run_id;
end;
$$;
