-- Optional agreed appointment price; no finance access or payment generated.
alter table public.teha_records add constraint teha_appointment_price check (store <> 'appointments' or coalesce(data->>'price','')='' or case when data->>'price' ~ '^[0-9]{1,9}(\.[0-9]{1,2})?$' then (data->>'price')::numeric between 0 and 999999999.99 else false end);
