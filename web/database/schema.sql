-- Isolated Teha web tables. Does not alter existing clinical/legacy tables.
create schema if not exists teha_private;
revoke all on schema teha_private from public, anon, authenticated;
create table public.teha_records (
 owner_id uuid not null references auth.users(id) on delete cascade,
 store text not null check(store in ('patients','triages','settings','appointments','notes','teeth','treatments','documents','finance','team')),
 id text not null check(length(id) between 1 and 200),
 data jsonb not null check(jsonb_typeof(data)='object' and data->>'id'=id),
 version bigint not null default 1,
 updated_at timestamptz not null default now(),
 primary key(owner_id,store,id)
);
create table public.teha_history (
 id bigint generated always as identity primary key,
 owner_id uuid not null references auth.users(id) on delete cascade,
 actor uuid not null,
 store text not null,
 record_id text not null,
 at timestamptz not null default now(),
 previous jsonb,
 current jsonb not null
);
create index teha_history_owner_at on public.teha_history(owner_id,at desc);
alter table public.teha_records enable row level security;
alter table public.teha_history enable row level security;
create policy teha_read_own on public.teha_records for select to authenticated using(owner_id=(select auth.uid()));
create policy teha_insert_own on public.teha_records for insert to authenticated with check(owner_id=(select auth.uid()));
create policy teha_update_own on public.teha_records for update to authenticated using(owner_id=(select auth.uid())) with check(owner_id=(select auth.uid()));
create policy teha_history_own on public.teha_history for select to authenticated using(owner_id=(select auth.uid()));
revoke all on public.teha_records,public.teha_history from anon,authenticated;
grant select,insert,update on public.teha_records to authenticated;
grant select on public.teha_history to authenticated;

create function teha_private.validate_record() returns trigger language plpgsql security invoker set search_path='' as $$
declare r jsonb; a jsonb; start_at timestamp; end_at timestamp;
begin
 if auth.uid() is null or new.owner_id<>auth.uid() then raise exception 'Acesso negado'; end if;
 perform pg_advisory_xact_lock(hashtextextended(new.owner_id::text,0));
 if tg_op='UPDATE' then
  if old.owner_id<>new.owner_id or old.store<>new.store or old.id<>new.id then raise exception 'Identidade do registro imutável'; end if;
  if new.store in ('notes','teeth') then raise exception 'Registro preservado: crie um adendo'; end if;
  new.version:=old.version+1;
 else new.version:=1;
 end if;
 new.updated_at:=now();
 new.data:=new.data || jsonb_build_object('author',auth.uid()::text,'updatedAt',now(),'createdAt',case when tg_op='UPDATE' then old.data->>'createdAt' else coalesce(new.data->>'createdAt',now()::text) end);
 if octet_length(new.data::text)>16000000 then raise exception 'Registro excede o limite de 16 MB'; end if;
 if new.store in ('patients','team') and coalesce(trim(new.data->>'name'),'')='' then raise exception 'Informe o nome'; end if;
 if new.store in ('triages','appointments','notes','teeth','treatments','documents') or (new.store='finance' and coalesce(new.data->>'patient','')<>'') then
  if not exists(select 1 from public.teha_records where owner_id=new.owner_id and store='patients' and id=new.data->>'patient') then raise exception 'Paciente não encontrado nesta conta'; end if;
 end if;
 if coalesce(new.data->>'professional','')<>'' and not exists(select 1 from public.teha_records where owner_id=new.owner_id and store='team' and id=new.data->>'professional') then raise exception 'Profissional não encontrado nesta conta'; end if;
 if new.store='triages' then
  if coalesce((new.data->>'pain')::numeric,-1) not between 0 and 10 then raise exception 'Dor deve estar entre 0 e 10'; end if;
  if coalesce(new.data->>'appointmentId','')<>'' and not exists(select 1 from public.teha_records where owner_id=new.owner_id and store='appointments' and id=new.data->>'appointmentId' and data->>'patient'=new.data->>'patient') then raise exception 'A avaliação deve pertencer ao paciente da consulta'; end if;
 end if;
 if new.store='finance' and (coalesce((new.data->>'amount')::numeric,0)<=0 or coalesce(new.data->>'type','') not in ('Receita','Despesa') or coalesce(new.data->>'status','') not in ('Pendente','Quitado','Cancelado')) then raise exception 'Lançamento financeiro inválido'; end if;
 if new.store='finance' and new.data->>'status'='Quitado' and coalesce(new.data->>'paidAt','')='' then raise exception 'Informe a data de pagamento'; end if;
 if new.store='appointments' then
  if coalesce(new.data->>'status','') not in ('Agendado','Confirmado','Na sala de espera','Em atendimento','Concluído','Faltou','Cancelado') then raise exception 'Situação inválida'; end if;
  if coalesce(new.data->>'chair','')='' then raise exception 'Informe a sala'; end if;
  start_at:=(new.data->>'date')::date+(new.data->>'time')::time;
  end_at:=start_at+make_interval(mins=>(new.data->>'duration')::int);
  if start_at is null or end_at is null or end_at<=start_at or end_at::date<>start_at::date then raise exception 'Horário ou duração inválidos'; end if;
  if new.data->>'status' in ('Na sala de espera','Em atendimento') and ((new.data->>'date')::date<>(now() at time zone 'America/Sao_Paulo')::date or coalesce(new.data->>'arrivedAt','')='') then raise exception 'Confirme a chegada de uma consulta de hoje'; end if;
  if new.data->>'status' not in ('Cancelado','Faltou') then
   for r in select data from public.teha_records where owner_id=new.owner_id and store='appointments' and id<>new.id and data->>'date'=new.data->>'date' and data->>'status' not in ('Cancelado','Faltou') loop
    if (r->>'professional'=new.data->>'professional' or r->>'patient'=new.data->>'patient' or lower(trim(r->>'chair'))=lower(trim(new.data->>'chair'))) and start_at < (r->>'date')::date+(r->>'time')::time+make_interval(mins=>(r->>'duration')::int) and end_at > (r->>'date')::date+(r->>'time')::time then raise exception 'Conflito de horário para paciente, profissional ou sala'; end if;
   end loop;
  end if;
 end if;
 return new;
end $$;
create trigger teha_validate before insert or update on public.teha_records for each row execute function teha_private.validate_record();

-- Privileged internal trigger solely to append trustworthy history; not an API.
create function teha_private.audit_record() returns trigger language plpgsql security definer set search_path='' as $$
begin
 if auth.uid() is null or auth.uid()<>new.owner_id then raise exception 'Sessão inválida'; end if;
 insert into public.teha_history(owner_id,actor,store,record_id,previous,current) values(new.owner_id,auth.uid(),new.store,new.id,case when tg_op='UPDATE' then old.data else null end,new.data);
 return new;
end $$;
revoke execute on function teha_private.audit_record() from public,anon,authenticated;
create trigger teha_audit after insert or update on public.teha_records for each row execute function teha_private.audit_record();

create function public.teha_save(p_store text,p_record jsonb,p_expected bigint default 0) returns void language plpgsql security invoker set search_path='' as $$
declare existing bigint;
begin
 if auth.uid() is null then raise exception 'Entre na sua conta'; end if;
 perform pg_advisory_xact_lock(hashtextextended(auth.uid()::text,0));
 select version into existing from public.teha_records where owner_id=auth.uid() and store=p_store and id=p_record->>'id';
 if existing is null then
  if p_expected<>0 then raise exception 'Registro não encontrado. Atualize a página'; end if;
  insert into public.teha_records(owner_id,store,id,data) values(auth.uid(),p_store,p_record->>'id',p_record);
 else
  if existing<>p_expected then raise exception 'Registro alterado em outra sessão. Reabra o formulário antes de salvar'; end if;
  update public.teha_records set data=p_record where owner_id=auth.uid() and store=p_store and id=p_record->>'id';
 end if;
end $$;
revoke execute on function public.teha_save(text,jsonb,bigint) from public,anon;
grant execute on function public.teha_save(text,jsonb,bigint) to authenticated;

create function public.teha_seed_demo() returns void language plpgsql security invoker set search_path='' as $$
declare names text[]:=array['Ana Oliveira','Bruno Almeida','Carla Souza','Diego Martins','Elisa Ferreira','Fábio Costa']; i int;
begin
 if auth.uid() is null then raise exception 'Entre na conta'; end if;
 perform pg_advisory_xact_lock(hashtextextended(auth.uid()::text,0));
 if exists(select 1 from public.teha_records where owner_id=auth.uid() and store='settings' and id='demo-v1') then return; end if;
 for i in 1..6 loop
  if not exists(select 1 from public.teha_records where owner_id=auth.uid() and store='patients' and id='demo-patient-'||i) then
   insert into public.teha_records(owner_id,store,id,data) values(auth.uid(),'patients','demo-patient-'||i,jsonb_build_object('id','demo-patient-'||i,'name',names[i]||' (teste)','remarks','Paciente fictício de demonstração','phone',''));
  end if;
 end loop;
 insert into public.teha_records(owner_id,store,id,data) values(auth.uid(),'team','demo-dentist',jsonb_build_object('id','demo-dentist','name','Dentista de demonstração','role','Dentista')) on conflict do nothing;
 insert into public.teha_records(owner_id,store,id,data) values(auth.uid(),'settings','demo-v1','{"id":"demo-v1"}'::jsonb);
end $$;
revoke execute on function public.teha_seed_demo() from public,anon;
grant execute on function public.teha_seed_demo() to authenticated;

create function public.teha_import(p_data jsonb) returns void language plpgsql security invoker set search_path='' as $$
declare kind text; record jsonb;
begin
 if auth.uid() is null then raise exception 'Entre na conta'; end if;
 perform pg_advisory_xact_lock(hashtextextended(auth.uid()::text,0));
 foreach kind in array array['patients','team','settings','appointments','notes','teeth','treatments','documents','finance','triages'] loop
  for record in select value from jsonb_array_elements(coalesce(p_data->kind,'[]'::jsonb)) loop
   insert into public.teha_records(owner_id,store,id,data) values(auth.uid(),kind,record->>'id',record);
  end loop;
 end loop;
end $$;
revoke execute on function public.teha_import(jsonb) from public,anon;
grant execute on function public.teha_import(jsonb) to authenticated;
alter publication supabase_realtime add table public.teha_records;
