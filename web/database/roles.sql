-- Role permissions are live database state, never editable JWT user metadata.
create table public.teha_access_roles (
 user_id uuid primary key references auth.users(id) on delete cascade,
 role text not null check(role in ('doctor','reception','management','blocked')),
 updated_at timestamptz not null default now()
);
alter table public.teha_access_roles enable row level security;
revoke all on public.teha_access_roles from public,anon,authenticated;
grant select on public.teha_access_roles to authenticated;
grant all on public.teha_access_roles to service_role;
create policy read_own_role on public.teha_access_roles for select to authenticated using(user_id=(select auth.uid()));
create or replace function teha_private.current_role() returns text language sql stable security definer set search_path='' as $$
 select case when exists(select 1 from auth.users u join public.teha_admins a on a.user_id=u.id where u.id=auth.uid() and u.id='0fd8e9a2-88e5-4c08-ab8f-a5635db8c3ee' and lower(u.email)='wcsam@outlook.com' and u.email_confirmed_at is not null) then 'admin'
 else coalesce((select r.role from public.teha_access_roles r join auth.users u on u.id=r.user_id where r.user_id=auth.uid() and (u.banned_until is null or u.banned_until<now())),'blocked') end
$$;
revoke all on function teha_private.current_role() from public,anon;
grant usage on schema teha_private to authenticated;
grant execute on function teha_private.current_role() to authenticated;
create or replace function teha_private.allowed(p_store text,p_id text) returns boolean language sql stable security definer set search_path='' as $$
 select case teha_private.current_role()
 when 'admin' then true
 when 'doctor' then p_store in ('patients','triages','appointments','notes','teeth','treatments','documents') or (p_store='settings' and p_id='profile')
 when 'reception' then p_store in ('patients','appointments','triages') or (p_store='settings' and p_id='profile')
 when 'management' then p_store in ('finance','team') or (p_store='settings' and p_id in ('profile','clinic'))
 else false end
$$;
revoke all on function teha_private.allowed(text,text) from public,anon;
grant execute on function teha_private.allowed(text,text) to authenticated;
drop policy teha_read_own on public.teha_records;
drop policy teha_insert_own on public.teha_records;
drop policy teha_update_own on public.teha_records;
create policy teha_read_own on public.teha_records for select to authenticated using(owner_id=(select auth.uid()) and teha_private.allowed(store,id));
create policy teha_insert_own on public.teha_records for insert to authenticated with check(owner_id=(select auth.uid()) and teha_private.allowed(store,id));
create policy teha_update_own on public.teha_records for update to authenticated using(owner_id=(select auth.uid()) and teha_private.allowed(store,id)) with check(owner_id=(select auth.uid()) and teha_private.allowed(store,id));
drop policy teha_history_own on public.teha_history;
create policy teha_history_admin on public.teha_history for select to authenticated using((select teha_private.current_role())='admin');
-- The validator checks auth.uid and immutable ownership itself. Definer lets it
-- validate patient/provider references that are deliberately not visible as full records.
alter function teha_private.validate_record() security definer;
revoke all on function teha_private.validate_record() from public,anon,authenticated;
create or replace function public.teha_access() returns jsonb language plpgsql stable security definer set search_path='' as $$
declare r text:=teha_private.current_role(); teams jsonb:='[]'; patients jsonb:='[]'; stats jsonb:='{}'; clinic jsonb:='{}';
begin
 if auth.uid() is null then raise exception 'Entre na conta'; end if;
 if r in ('doctor','reception') then
 select coalesce(jsonb_agg(jsonb_build_object('id',id,'name',data->>'name','archived',data->'archived','registration',data->>'registration')),'[]') into teams from public.teha_records where owner_id=auth.uid() and store='team';
 end if;
 if r='doctor' then select coalesce(data,'{}') into clinic from public.teha_records where owner_id=auth.uid() and store='settings' and id='clinic'; end if;
 if r='management' then
 select coalesce(jsonb_agg(jsonb_build_object('id',id,'name',data->>'name','archived',data->'archived')),'[]') into patients from public.teha_records where owner_id=auth.uid() and store='patients';
 select jsonb_build_object('appointments',count(*) filter(where store='appointments'),'missed',count(*) filter(where store='appointments' and data->>'status'='Faltou'),'completed',count(*) filter(where store='treatments' and data->>'status'='Concluído')) into stats from public.teha_records where owner_id=auth.uid() and store in ('appointments','treatments');
 end if;
 return jsonb_build_object('role',r,'team',teams,'patients',patients,'stats',stats,'clinic',coalesce(clinic,'{}'));
end $$;
revoke all on function public.teha_access() from public,anon;
grant execute on function public.teha_access() to authenticated;
-- Never seed fake clinical records as a side effect of login with a limited role.
create or replace function public.teha_seed_demo() returns void language plpgsql set search_path='' as $$ begin if auth.uid() is null then raise exception 'Entre na conta'; end if; end $$;
revoke all on function public.teha_seed_demo() from public,anon;
grant execute on function public.teha_seed_demo() to authenticated;
alter table public.teha_admin_actions drop constraint teha_admin_actions_action_check;
alter table public.teha_admin_actions add constraint teha_admin_actions_action_check check(action in ('create_user','change_email','change_password','change_role'));
-- Keep the privileged lookup outside exposed API schemas.
alter function public.teha_access() set schema teha_private;
create function public.teha_access() returns jsonb language sql stable security invoker set search_path='' as $$ select teha_private.teha_access() $$;
revoke all on function public.teha_access() from public,anon;
grant execute on function public.teha_access() to authenticated;
