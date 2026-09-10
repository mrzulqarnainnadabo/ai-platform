-- AI Platform application authorization boundary.
--
-- This migration is intentionally application-owned. The platform kernel does
-- not depend on Supabase. Enable the Custom Access Token Hook in the Supabase
-- dashboard after applying this migration.
--
-- The hook emits only server-controlled claims:
--   ai_platform_tenant_id
--   ai_platform_permissions
--
-- No user_metadata is used for authorization.

create table if not exists public.ai_platform_roles (
  role text primary key,
  description text not null default ''
);

create table if not exists public.ai_platform_role_permissions (
  role text not null references public.ai_platform_roles(role) on delete cascade,
  capability text not null,
  primary key (role, capability)
);

create table if not exists public.ai_platform_memberships (
  user_id uuid not null references auth.users(id) on delete cascade,
  tenant_id uuid not null,
  role text not null references public.ai_platform_roles(role),
  active boolean not null default true,
  created_at timestamptz not null default now(),
  primary key (user_id, tenant_id)
);

create index if not exists ai_platform_memberships_user_active_idx
  on public.ai_platform_memberships(user_id, active);

alter table public.ai_platform_roles enable row level security;
alter table public.ai_platform_role_permissions enable row level security;
alter table public.ai_platform_memberships enable row level security;

-- The Auth service needs read access to these tables for the custom access
-- token hook. Application clients receive no direct table access by default.
grant select on public.ai_platform_roles to supabase_auth_admin;
grant select on public.ai_platform_role_permissions to supabase_auth_admin;
grant select on public.ai_platform_memberships to supabase_auth_admin;

drop policy if exists "auth service reads platform roles" on public.ai_platform_roles;
create policy "auth service reads platform roles"
  on public.ai_platform_roles
  for select
  to supabase_auth_admin
  using (true);

drop policy if exists "auth service reads platform role permissions" on public.ai_platform_role_permissions;
create policy "auth service reads platform role permissions"
  on public.ai_platform_role_permissions
  for select
  to supabase_auth_admin
  using (true);

drop policy if exists "auth service reads platform memberships" on public.ai_platform_memberships;
create policy "auth service reads platform memberships"
  on public.ai_platform_memberships
  for select
  to supabase_auth_admin
  using (true);

revoke all on public.ai_platform_roles from anon, authenticated, public;
revoke all on public.ai_platform_role_permissions from anon, authenticated, public;
revoke all on public.ai_platform_memberships from anon, authenticated, public;

-- Safe starter roles. Assignment is deliberately separate from role creation.
insert into public.ai_platform_roles(role, description)
values
  ('platform_user', 'Can invoke explicitly granted model capabilities.'),
  ('platform_admin', 'Platform administration role; permissions remain explicit.')
on conflict (role) do nothing;

insert into public.ai_platform_role_permissions(role, capability)
values
  ('platform_user', 'model.generate'),
  ('platform_user', 'model.stream'),
  ('platform_admin', 'model.generate'),
  ('platform_admin', 'model.stream')
on conflict do nothing;

create or replace function public.custom_access_token_hook(event jsonb)
returns jsonb
language plpgsql
stable
as $$
declare
  claims jsonb;
  active_membership_count integer;
  selected_tenant uuid;
  selected_role text;
  selected_permissions jsonb;
begin
  claims := event->'claims';

  select count(*)
    into active_membership_count
    from public.ai_platform_memberships
   where user_id = (event->>'user_id')::uuid
     and active = true;

  -- Fail closed for users with zero or multiple active tenants. Tenant
  -- selection can be added later without weakening this boundary.
  if active_membership_count = 1 then
    select m.tenant_id, m.role
      into selected_tenant, selected_role
      from public.ai_platform_memberships m
     where m.user_id = (event->>'user_id')::uuid
       and m.active = true
     limit 1;

    select coalesce(jsonb_agg(rp.capability order by rp.capability), '[]'::jsonb)
      into selected_permissions
      from public.ai_platform_role_permissions rp
     where rp.role = selected_role;

    claims := jsonb_set(
      claims,
      '{ai_platform_tenant_id}',
      to_jsonb(selected_tenant::text),
      true
    );
    claims := jsonb_set(
      claims,
      '{ai_platform_permissions}',
      coalesce(selected_permissions, '[]'::jsonb),
      true
    );
  else
    claims := jsonb_set(claims, '{ai_platform_tenant_id}', 'null'::jsonb, true);
    claims := jsonb_set(claims, '{ai_platform_permissions}', '[]'::jsonb, true);
  end if;

  return jsonb_build_object('claims', claims);
end;
$$;

grant usage on schema public to supabase_auth_admin;
grant execute on function public.custom_access_token_hook(jsonb) to supabase_auth_admin;
revoke execute on function public.custom_access_token_hook(jsonb) from anon, authenticated, public;
