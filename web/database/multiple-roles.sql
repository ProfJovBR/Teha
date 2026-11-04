-- Preserve existing assignments; legacy role remains a compatibility/landing-page label.
alter table public.teha_access_roles add column roles text[] not null default '{}';
update public.teha_access_roles set roles=array[role] where role<>'blocked';
alter table public.teha_access_roles add constraint teha_valid_multiple_roles check(roles <@ array['doctor','reception','management']::text[] and cardinality(roles)<=3 and array_position(roles,null) is null);
create function teha_private.current_roles() returns text[] language sql stable security definer set search_path='' as $$
 select case when teha_private.current_role()='admin' then array['admin'] when teha_private.current_role()='blocked' then '{}'::text[] else coalesce((select roles from public.teha_access_roles where user_id=auth.uid()),'{}'::text[]) end
$$;
revoke all on function teha_private.current_roles() from public,anon;
grant execute on function teha_private.current_roles() to authenticated;
create or replace function teha_private.allowed(p_store text,p_id text) returns boolean language sql stable security definer set search_path='' as $$
 select 'admin'=any(teha_private.current_roles())
 or ('doctor'=any(teha_private.current_roles()) and p_store in ('patients','triages','appointments','notes','teeth','treatments','documents'))
 or ('reception'=any(teha_private.current_roles()) and p_store in ('patients','appointments','triages'))
 or ('management'=any(teha_private.current_roles()) and (p_store in ('finance','team') or (p_store='settings' and p_id='clinic')))
 or (cardinality(teha_private.current_roles())>0 and p_store='settings' and p_id='profile')
$$;
create or replace function teha_private.teha_access() returns jsonb language plpgsql stable security definer set search_path='' as $$
declare rs text[]:=teha_private.current_roles(); r text:=teha_private.current_role(); teams jsonb:='[]'; patients jsonb:='[]'; stats jsonb:='{}'; clinic jsonb:='{}';
begin
 if auth.uid() is null then raise exception 'Entre na conta'; end if;
 if rs && array['doctor','reception'] and not ('management'=any(rs)) then
 select coalesce(jsonb_agg(jsonb_build_object('id',id,'name',data->>'name','archived',data->'archived','registration',data->>'registration')),'[]') into teams from public.teha_records where owner_id=auth.uid() and store='team';
 end if;
 if 'doctor'=any(rs) then select coalesce(data,'{}') into clinic from public.teha_records where owner_id=auth.uid() and store='settings' and id='clinic'; end if;
 if 'management'=any(rs) then
 if not(rs && array['doctor','reception']) then
 select coalesce(jsonb_agg(jsonb_build_object('id',id,'name',data->>'name','archived',data->'archived')),'[]') into patients from public.teha_records where owner_id=auth.uid() and store='patients';
 end if;
 select jsonb_build_object('appointments',count(*) filter(where store='appointments'),'missed',count(*) filter(where store='appointments' and data->>'status'='Faltou'),'completed',count(*) filter(where store='treatments' and data->>'status'='Concluído')) into stats from public.teha_records where owner_id=auth.uid() and store in ('appointments','treatments');
 end if;
 return jsonb_build_object('role',r,'roles',rs,'team',teams,'patients',patients,'stats',stats,'clinic',coalesce(clinic,'{}'));
end $$;
