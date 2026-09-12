-- Grant the first Intelligence Layer capabilities to the existing platform roles.
-- Authorization remains server-controlled through the custom access-token hook.
insert into public.ai_platform_role_permissions(role, capability)
values
  ('platform_user', 'case.create'),
  ('platform_user', 'case.read'),
  ('platform_user', 'case.triage'),
  ('platform_user', 'evidence.attach'),
  ('platform_admin', 'case.create'),
  ('platform_admin', 'case.read'),
  ('platform_admin', 'case.triage'),
  ('platform_admin', 'evidence.attach')
on conflict do nothing;
