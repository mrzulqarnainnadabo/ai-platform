-- Durable persistence for the governed problem-resolution lifecycle.
-- This schema stores proposals and human-authorized state transitions; it does
-- not grant the database or AI autonomous execution authority.

create table if not exists public.ai_platform_responsibilities (
  id uuid primary key,
  case_id uuid not null references public.ai_platform_cases(id) on delete cascade,
  tenant_id text not null,
  subject text not null,
  role text not null,
  scope text not null,
  source_assertion_ids jsonb not null default '[]'::jsonb,
  status text not null default 'proposed' check (status in ('proposed', 'confirmed', 'rejected')),
  created_by_subject text not null,
  created_at timestamptz not null default now()
);

create index if not exists ai_platform_responsibilities_case_idx
  on public.ai_platform_responsibilities (tenant_id, case_id, created_at desc);

create table if not exists public.ai_platform_action_proposals (
  id uuid primary key,
  case_id uuid not null references public.ai_platform_cases(id) on delete cascade,
  tenant_id text not null,
  title text not null,
  description text not null,
  proposed_by_subject text not null,
  responsibility_id uuid references public.ai_platform_responsibilities(id) on delete set null,
  source_assertion_ids jsonb not null default '[]'::jsonb,
  status text not null default 'draft' check (status in ('draft', 'submitted', 'approved', 'rejected', 'withdrawn')),
  approval_subject text,
  approved_at timestamptz,
  created_at timestamptz not null default now(),
  constraint ai_platform_action_proposal_approval_consistency check (
    (status = 'approved' and approval_subject is not null and approved_at is not null)
    or status <> 'approved'
  )
);

create index if not exists ai_platform_action_proposals_case_idx
  on public.ai_platform_action_proposals (tenant_id, case_id, created_at desc);

create table if not exists public.ai_platform_commitments (
  id uuid primary key,
  case_id uuid not null references public.ai_platform_cases(id) on delete cascade,
  tenant_id text not null,
  proposal_id uuid not null references public.ai_platform_action_proposals(id) on delete restrict,
  owner_subject text not null,
  action text not null,
  due_at timestamptz,
  status text not null default 'pending' check (status in ('pending', 'active', 'completed', 'cancelled')),
  created_by_subject text not null,
  created_at timestamptz not null default now()
);

create index if not exists ai_platform_commitments_case_idx
  on public.ai_platform_commitments (tenant_id, case_id, created_at desc);

create table if not exists public.ai_platform_outcomes (
  id uuid primary key,
  case_id uuid not null references public.ai_platform_cases(id) on delete cascade,
  tenant_id text not null,
  commitment_id uuid not null references public.ai_platform_commitments(id) on delete restrict,
  summary text not null,
  status text not null check (status in ('pending', 'partial', 'achieved', 'not_achieved', 'verified')),
  evidence_ids jsonb not null default '[]'::jsonb,
  recorded_by_subject text not null,
  created_at timestamptz not null default now(),
  constraint ai_platform_outcome_verification_evidence_check check (
    status <> 'verified' or jsonb_array_length(evidence_ids) > 0
  )
);

create index if not exists ai_platform_outcomes_case_idx
  on public.ai_platform_outcomes (tenant_id, case_id, created_at desc);

-- Immutable lifecycle history. Consumers can reconstruct who changed what and when.
create table if not exists public.ai_platform_resolution_events (
  id uuid primary key,
  tenant_id text not null,
  case_id uuid not null references public.ai_platform_cases(id) on delete cascade,
  actor_subject text not null,
  object_type text not null check (object_type in ('responsibility', 'action_proposal', 'commitment', 'outcome')),
  object_id uuid not null,
  event_type text not null,
  from_status text,
  to_status text,
  payload_digest text not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists ai_platform_resolution_events_case_idx
  on public.ai_platform_resolution_events (tenant_id, case_id, created_at);
create index if not exists ai_platform_resolution_events_object_idx
  on public.ai_platform_resolution_events (object_id, created_at);

alter table public.ai_platform_responsibilities enable row level security;
alter table public.ai_platform_action_proposals enable row level security;
alter table public.ai_platform_commitments enable row level security;
alter table public.ai_platform_outcomes enable row level security;
alter table public.ai_platform_resolution_events enable row level security;

-- Defense in depth: clients receive no direct table privileges. The authorized
-- service path remains responsible for capability checks and tenant scoping.
revoke all on public.ai_platform_responsibilities from anon, authenticated, public;
revoke all on public.ai_platform_action_proposals from anon, authenticated, public;
revoke all on public.ai_platform_commitments from anon, authenticated, public;
revoke all on public.ai_platform_outcomes from anon, authenticated, public;
revoke all on public.ai_platform_resolution_events from anon, authenticated, public;

-- Prevent deletion of immutable lifecycle history.
create or replace function public.ai_platform_prevent_resolution_event_mutation()
returns trigger
language plpgsql
security invoker
as $$
begin
  raise exception 'Resolution events are append-only';
end;
$$;

drop trigger if exists ai_platform_resolution_events_no_update_delete
  on public.ai_platform_resolution_events;
create trigger ai_platform_resolution_events_no_update_delete
before update or delete on public.ai_platform_resolution_events
for each row execute function public.ai_platform_prevent_resolution_event_mutation();
