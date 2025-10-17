-- RLS hardening for public tables used by MockExamify
-- Run this in Supabase SQL editor (or via migration) to satisfy linter warnings

-- USERS
alter table if exists public.users enable row level security;

-- Only the user can read/update their own row
create policy if not exists "users_select_own"
on public.users for select
to authenticated
using (auth.uid() = id);

create policy if not exists "users_update_own"
on public.users for update
to authenticated
using (auth.uid() = id);

-- Optional: allow inserts from clients only when id matches auth.uid()
-- create policy if not exists "users_insert_own"
-- on public.users for insert
-- to authenticated
-- with check (auth.uid() = id);


-- MOCKS
alter table if exists public.mocks enable row level security;

-- Public can view only active mocks
create policy if not exists "mocks_public_read_active"
on public.mocks for select
to anon, authenticated
using (is_active = true);

-- Only admins can insert/update mocks
create policy if not exists "mocks_admin_insert"
on public.mocks for insert
to authenticated
with check (exists (
  select 1 from public.users u where u.id = auth.uid() and u.role = 'admin'
));

create policy if not exists "mocks_admin_update"
on public.mocks for update
to authenticated
using (exists (
  select 1 from public.users u where u.id = auth.uid() and u.role = 'admin'
));

-- Optional: allow creators to manage their own mocks
-- create policy if not exists "mocks_creator_update_own"
-- on public.mocks for update
-- to authenticated
-- using (creator_id = auth.uid())
-- with check (creator_id = auth.uid());


-- ATTEMPTS
alter table if exists public.attempts enable row level security;

create policy if not exists "attempts_select_own"
on public.attempts for select
to authenticated
using (auth.uid() = user_id);

create policy if not exists "attempts_insert_own"
on public.attempts for insert
to authenticated
with check (auth.uid() = user_id);

create policy if not exists "attempts_update_own"
on public.attempts for update
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);


-- TICKETS (legacy table retained)
alter table if exists public.tickets enable row level security;

create policy if not exists "tickets_select_own"
on public.tickets for select
to authenticated
using (auth.uid() = user_id);

create policy if not exists "tickets_insert_own"
on public.tickets for insert
to authenticated
with check (auth.uid() = user_id);

-- Optional: admin can view/update all tickets
create policy if not exists "tickets_admin_select_all"
on public.tickets for select
to authenticated
using (exists (
  select 1 from public.users u where u.id = auth.uid() and u.role = 'admin'
));

create policy if not exists "tickets_admin_update"
on public.tickets for update
to authenticated
using (exists (
  select 1 from public.users u where u.id = auth.uid() and u.role = 'admin'
));


-- Verification query
-- select schemaname, tablename, rowsecurity
-- from pg_tables
-- where schemaname = 'public' and tablename in ('users','mocks','attempts','tickets');



