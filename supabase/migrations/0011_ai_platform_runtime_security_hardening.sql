create schema if not exists extensions;
alter extension vector set schema extensions;

-- All SECURITY DEFINER/privileged runtime functions use an explicit search_path.
alter function public.reserve_ai_platform_budget(text,text,text,integer,bigint,bigint,text) set search_path = public, extensions, pg_temp;
alter function public.settle_ai_platform_budget(text,text,text,text,bigint,bigint) set search_path = public, extensions, pg_temp;
alter function public.complete_ai_platform_run(uuid,uuid,uuid,text,jsonb,numeric,numeric,text) set search_path = public, extensions, pg_temp;
alter function public.match_ai_platform_document_chunks(text,extensions.vector,integer,real) set search_path = public, extensions, pg_temp;
