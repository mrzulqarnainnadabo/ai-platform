-- Defense-in-depth integrity guards for the intelligence system of record.
-- Application authorization remains authoritative; these constraints prevent
-- accidental cross-tenant links and make evidence/audit append-only at the DB layer.

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'ai_platform_cases_id_tenant_key'
  ) THEN
    ALTER TABLE public.ai_platform_cases
      ADD CONSTRAINT ai_platform_cases_id_tenant_key UNIQUE (id, tenant_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'ai_platform_assertions_id_tenant_key'
  ) THEN
    ALTER TABLE public.ai_platform_assertions
      ADD CONSTRAINT ai_platform_assertions_id_tenant_key UNIQUE (id, tenant_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'ai_platform_assertions_case_tenant_fk'
  ) THEN
    ALTER TABLE public.ai_platform_assertions
      ADD CONSTRAINT ai_platform_assertions_case_tenant_fk
      FOREIGN KEY (case_id, tenant_id)
      REFERENCES public.ai_platform_cases (id, tenant_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'ai_platform_evidence_case_tenant_fk'
  ) THEN
    ALTER TABLE public.ai_platform_evidence
      ADD CONSTRAINT ai_platform_evidence_case_tenant_fk
      FOREIGN KEY (case_id, tenant_id)
      REFERENCES public.ai_platform_cases (id, tenant_id);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'ai_platform_evidence_assertion_tenant_fk'
  ) THEN
    ALTER TABLE public.ai_platform_evidence
      ADD CONSTRAINT ai_platform_evidence_assertion_tenant_fk
      FOREIGN KEY (assertion_id, tenant_id)
      REFERENCES public.ai_platform_assertions (id, tenant_id);
  END IF;
END $$;

CREATE OR REPLACE FUNCTION public.ai_platform_reject_evidence_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog, public
AS $$
BEGIN
  RAISE EXCEPTION 'ai_platform_evidence is append-only';
END;
$$;

DROP TRIGGER IF EXISTS ai_platform_evidence_append_only ON public.ai_platform_evidence;
CREATE TRIGGER ai_platform_evidence_append_only
BEFORE UPDATE OR DELETE ON public.ai_platform_evidence
FOR EACH ROW EXECUTE FUNCTION public.ai_platform_reject_evidence_mutation();

CREATE OR REPLACE FUNCTION public.ai_platform_reject_audit_mutation()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog, public
AS $$
BEGIN
  RAISE EXCEPTION 'ai_platform_audit_events is append-only';
END;
$$;

DROP TRIGGER IF EXISTS ai_platform_audit_append_only ON public.ai_platform_audit_events;
CREATE TRIGGER ai_platform_audit_append_only
BEFORE UPDATE OR DELETE ON public.ai_platform_audit_events
FOR EACH ROW EXECUTE FUNCTION public.ai_platform_reject_audit_mutation();
