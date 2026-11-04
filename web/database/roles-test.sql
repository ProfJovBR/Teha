-- Integration test; all fixtures and role assignments are rolled back.
begin;
insert into auth.users(id,email) values('00000000-0000-4000-8000-000000000001','rbac-test@example.invalid');
select set_config('request.jwt.claim.sub','00000000-0000-4000-8000-000000000001',true);
insert into public.teha_records(owner_id,store,id,data) values
(auth.uid(),'patients','rbac-test-patient','{"id":"rbac-test-patient","name":"RBAC fictício"}'),
(auth.uid(),'team','rbac-test-provider','{"id":"rbac-test-provider","name":"RBAC fictício","salary":"secret-test"}'),
(auth.uid(),'notes','rbac-test-note','{"id":"rbac-test-note","patient":"rbac-test-patient","content":"secret-test"}');
insert into public.teha_access_roles(user_id,role,roles) values(auth.uid(),'reception',array['reception']) on conflict(user_id) do update set role=excluded.role,roles=excluded.roles;
set local role authenticated;
do $$ begin
 if (public.teha_access()->>'role')<>'reception' then raise exception 'Wrong role'; end if;
 if exists(select 1 from public.teha_records where store in ('team','finance','notes','teeth','treatments','documents')) then raise exception 'Reception leaked restricted records'; end if;
 if exists(select 1 from public.teha_history) then raise exception 'Reception leaked history'; end if;
 if public.teha_access()->'team' @> '[{"salary":"secret-test"}]' then raise exception 'Team lookup leaked'; end if;
 if exists(select 1 from public.teha_records where owner_id<>auth.uid()) then raise exception 'Other owner leaked'; end if;
 begin update public.teha_access_roles set role='management',roles=array['management'] where user_id=auth.uid();raise exception 'Self promotion succeeded';exception when insufficient_privilege then null;end;
 begin perform public.teha_save('finance','{"id":"rbac-denied","type":"Receita","amount":10,"status":"Pendente"}',0);raise exception 'Reception finance succeeded';exception when insufficient_privilege then null;end;
 perform public.teha_save('triages','{"id":"rbac-test-triage","patient":"rbac-test-patient","pain":0,"reason":"RBAC fictício"}',0);
end $$;
reset role;
update public.teha_access_roles set role='doctor',roles=array['doctor'] where user_id=auth.uid();
set local role authenticated;
do $$ begin
 if public.teha_access()->>'role'<>'doctor' then raise exception 'Role not fresh'; end if;
 if not exists(select 1 from public.teha_records where id='rbac-test-note') then raise exception 'Doctor cannot read note'; end if;
 if exists(select 1 from public.teha_history) then raise exception 'Doctor leaked history'; end if;
 begin perform public.teha_save('finance','{"id":"rbac-denied","type":"Receita","amount":10,"status":"Pendente"}',0);raise exception 'Doctor finance succeeded';exception when insufficient_privilege then null;end;
 perform public.teha_save('teeth','{"id":"rbac-test-tooth","patient":"rbac-test-patient","tooth":"11","condition":"Hígido"}',0);
end $$;
reset role;
update public.teha_access_roles set role='management',roles=array['management'] where user_id=auth.uid();
set local role authenticated;
do $$ begin
 if public.teha_access()->>'role'<>'management' then raise exception 'Role not fresh'; end if;
 if exists(select 1 from public.teha_records where store in ('patients','notes','teeth','triages','documents','appointments','treatments')) then raise exception 'Management leaked clinical records'; end if;
 if exists(select 1 from public.teha_history) then raise exception 'Management leaked history'; end if;
 begin perform public.teha_save('notes','{"id":"rbac-denied","patient":"rbac-test-patient","content":"test"}',0);raise exception 'Management clinical write succeeded';exception when insufficient_privilege then null;end;
 perform public.teha_save('finance','{"id":"rbac-test-finance","patient":"rbac-test-patient","type":"Receita","amount":10,"status":"Pendente"}',0);
end $$;
reset role;
update public.teha_access_roles set role='blocked',roles='{}' where user_id=auth.uid();
set local role authenticated;
do $$ begin
 if exists(select 1 from public.teha_records) then raise exception 'Blocked account leaked'; end if;
 if public.teha_access()->>'role'<>'blocked' then raise exception 'Blocked role failed'; end if;
end $$;
reset role;
select set_config('request.jwt.claim.sub','0fd8e9a2-88e5-4c08-ab8f-a5635db8c3ee',true);
set local role authenticated;
do $$ begin
 if public.teha_access()->>'role'<>'admin' then raise exception 'Owner lost admin'; end if;
 if not exists(select 1 from public.teha_history where record_id='rbac-test-triage') then raise exception 'Admin cannot read audit'; end if;
 if exists(select 1 from public.teha_records where owner_id<>auth.uid()) then raise exception 'Admin crossed workspace boundary'; end if;
end $$;
select 'PASS: reception, doctor, management, blocked, admin, forbidden writes, role self-promotion, audit and workspace isolation' as result;
rollback;
