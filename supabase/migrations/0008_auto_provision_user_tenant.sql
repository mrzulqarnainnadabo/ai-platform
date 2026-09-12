-- AI Platform production hardening
-- 0008_auto_provision_user_tenant.sql
--
-- Provisions one isolated tenant membership for every new Auth user and
-- backfills existing users without an active membership. Authorization is
-- derived only from server-controlled membership/role data.

begin;

-- Ensure the default role exists and has the complete application capability set.
insert into public.ai_platform_roles (role, description)
values ('platform_user', 'Default authenticated AI Platform user.')
on conflict (role) do nothing;

insert into public.ai_platform_role_permissions (role, capability)
values
  ('platform_user', 'case.read'),
  ('platform_user', 'case.create'),
  ('platform_user', 'case.triage'),
  ('platform_user', 'case.update'),
  ('platform_user', 'evidence.attach'),
  ('platform_user', 'model.generate')
on conflict do nothing;

-- Create an isolated tenant UUID for each new Auth user.
create or replace function public.provision_ai_platform_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.ai_platform_memberships (
    user_id,
    tenant_id,
    role,
    active
  )
  values (
    new.id,
    gen_random_uuid(),
    'platform_user',
    true
  )
  on conflict (user_id, tenant_id) do nothing;

  return new;
end;
$$;

drop trigger if exists on_auth_user_created_ai_platform on auth.users;

create trigger on_auth_user_created_ai_platform
after insert on auth.users
for each row
execute function public.provision_ai_platform_user();

-- Backfill users already created before this migration.
insert into public.ai_platform_memberships (
  user_id,
  tenant_id,
  role,
  active
)
select
  u.id,
  gen_random_uuid(),
  'platform_user',
  true
from auth.users u
where not exists (
  select 1
  from public.ai_platform_memberships m
  where m.user_id = u.id
    and m.active = true
);

-- Keep provisioning server-only.
revoke execute on function public.provision_ai_platform_user() from public, anon, authenticated;
grant execute on function public.provision_ai_platform_user() to postgres;

-- Reassert the Auth Custom Access Token Hook. It fails closed unless the
-- authenticated user has exactly one active membership.
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

  if active_membership_count = 1 then
    select m.tenant_id, m.role
      into selected_tenant, selected_role
    from public.ai_platform_memberships m
    where m.user_id = (event->>'user_id')::uuid
      and m.active = true
    limit 1;

    select coalesce(
      jsonb_agg(rp.capability order by rp.capability),
      '[]'::jsonb
    )
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
    claims := jsonb_set(
      claims,
      '{ai_platform_tenant_id}',
      'null'::jsonb,
      true
    );

    claims := jsonb_set(
      claims,
      '{ai_platform_permissions}',
      '[]'::jsonb,
      true
    );
  end if;

  return jsonb_build_object('claims', claims);
end;
$$;

grant usage on schema public to supabase_auth_admin;
grant select on public.ai_platform_roles to supabase_auth_admin;
grant select on public.ai_platform_role_permissions to supabase_auth_admin;
grant select on public.ai_platform_memberships to supabase_auth_admin;
grant execute on function public.custom_access_token_hook(jsonb) to supabase_auth_admin;

revoke execute on function public.custom_access_token_hook(jsonb) from anon, authenticated, public;

commit;
