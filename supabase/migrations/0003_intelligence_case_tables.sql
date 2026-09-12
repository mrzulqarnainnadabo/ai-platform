-- Durable case-intake storage (system of record for intelligence vertical slice).
-- Tenant isolation is enforced in application code AND should be mirrored with RLS
-- once service-role vs user-role access patterns are finalized.
-- This migration does not weaken JWT claim authority.

create table if not exists public.ai_platform_cases (
  id uuid primary key,
  tenant_id text not null,
  created_by_subject text not null,
  title text not null,
  summary text not null,
  status text not null check (status in ('open', 'in_progress', 'resolved', 'closed')),
  missing_evidence_questions jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists ai_platform_cases_tenant_idx
  on public.ai_platform_cases (tenant_id, created_at desc);

create table if not exists public.ai_platform_assertions (
  id uuid primary key,
  case_id uuid not null references public.ai_platform_cases(id) on delete cascade,
  tenant_id text not null,
  text text not null,
  kind text not null check (kind in ('fact', 'claim', 'inference', 'unknown')),
  created_by text not null check (created_by in ('user', 'model')),
  requires_evidence boolean not null default true,
  evidence_ids jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists ai_platform_assertions_case_idx
  on public.ai_platform_assertions (case_id);

create table if not exists public.ai_platform_evidence (
  id uuid primary key,
  case_id uuid not null references public.ai_platform_cases(id) on delete cascade,
  tenant_id text not null,
  assertion_id uuid references public.ai_platform_assertions(id) on delete set null,
  body text not null,
  source_type text not null check (source_type in ('user_text', 'url', 'document_ref')),
  source_uri text,
  note text,
  created_by_subject text not null,
  created_at timestamptz not null default now(),
  constraint ai_platform_evidence_uri_required check (
    source_type = 'user_text' or (source_uri is not null and length(trim(source_uri)) > 0)
  )
);

create index if not exists ai_platform_evidence_case_idx
  on public.ai_platform_evidence (case_id);

-- Append-only audit. Prefer insert-only grants in production roles.
create table if not exists public.ai_platform_audit_events (
  id text primary key,
  tenant_id text not null,
  actor_subject text not null,
  action text not null,
  object_type text not null,
  object_id text not null,
  payload_digest text not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists ai_platform_audit_object_idx
  on public.ai_platform_audit_events (object_id, created_at);

create index if not exists ai_platform_audit_tenant_idx
  on public.ai_platform_audit_events (tenant_id, created_at desc);

alter table public.ai_platform_cases enable row level security;
alter table public.ai_platform_assertions enable row level security;
alter table public.ai_platform_evidence enable row level security;
alter table public.ai_platform_audit_events enable row level security;

-- No broad client policies here. Host should use a constrained server path.
-- Do not grant anon/authenticated unrestricted DML on these tables.
revoke all on public.ai_platform_cases from anon, authenticated, public;
revoke all on public.ai_platform_assertions from anon, authenticated, public;
revoke all on public.ai_platform_evidence from anon, authenticated, public;
revoke all on public.ai_platform_audit_events from anon, authenticated, public;
