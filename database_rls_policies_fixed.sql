-- RLS hardening for public tables used by MockExamify
-- Compatible with all PostgreSQL/Supabase versions
-- Run this in Supabase SQL editor to satisfy linter warnings

-- ============================================================
-- USERS TABLE
-- ============================================================
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS "users_select_own" ON public.users;
DROP POLICY IF EXISTS "users_update_own" ON public.users;

-- Only the user can read/update their own row
CREATE POLICY "users_select_own"
ON public.users FOR SELECT
TO authenticated
USING (auth.uid() = id);

CREATE POLICY "users_update_own"
ON public.users FOR UPDATE
TO authenticated
USING (auth.uid() = id);


-- ============================================================
-- MOCKS TABLE
-- ============================================================
ALTER TABLE public.mocks ENABLE ROW LEVEL SECURITY;

-- Drop existing policies
DROP POLICY IF EXISTS "mocks_public_read_active" ON public.mocks;
DROP POLICY IF EXISTS "mocks_admin_insert" ON public.mocks;
DROP POLICY IF EXISTS "mocks_admin_update" ON public.mocks;

-- Public can view only active mocks
CREATE POLICY "mocks_public_read_active"
ON public.mocks FOR SELECT
TO anon, authenticated
USING (is_active = true);

-- Only admins can insert/update mocks
CREATE POLICY "mocks_admin_insert"
ON public.mocks FOR INSERT
TO authenticated
WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.users u 
    WHERE u.id = auth.uid() AND u.role = 'admin'
  )
);

CREATE POLICY "mocks_admin_update"
ON public.mocks FOR UPDATE
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.users u 
    WHERE u.id = auth.uid() AND u.role = 'admin'
  )
);


-- ============================================================
-- ATTEMPTS TABLE
-- ============================================================
ALTER TABLE public.attempts ENABLE ROW LEVEL SECURITY;

-- Drop existing policies
DROP POLICY IF EXISTS "attempts_select_own" ON public.attempts;
DROP POLICY IF EXISTS "attempts_insert_own" ON public.attempts;
DROP POLICY IF EXISTS "attempts_update_own" ON public.attempts;

-- Users can only access their own attempts
CREATE POLICY "attempts_select_own"
ON public.attempts FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

CREATE POLICY "attempts_insert_own"
ON public.attempts FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "attempts_update_own"
ON public.attempts FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);


-- ============================================================
-- TICKETS TABLE
-- ============================================================
ALTER TABLE public.tickets ENABLE ROW LEVEL SECURITY;

-- Drop existing policies
DROP POLICY IF EXISTS "tickets_select_own" ON public.tickets;
DROP POLICY IF EXISTS "tickets_insert_own" ON public.tickets;
DROP POLICY IF EXISTS "tickets_admin_select_all" ON public.tickets;
DROP POLICY IF EXISTS "tickets_admin_update" ON public.tickets;

-- Users can view/create their own tickets
CREATE POLICY "tickets_select_own"
ON public.tickets FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

CREATE POLICY "tickets_insert_own"
ON public.tickets FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

-- Admins can view all tickets
CREATE POLICY "tickets_admin_select_all"
ON public.tickets FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.users u 
    WHERE u.id = auth.uid() AND u.role = 'admin'
  )
);

-- Admins can update all tickets
CREATE POLICY "tickets_admin_update"
ON public.tickets FOR UPDATE
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.users u 
    WHERE u.id = auth.uid() AND u.role = 'admin'
  )
);


-- ============================================================
-- VERIFICATION QUERY
-- ============================================================
-- Run this after to verify RLS is enabled:
-- 
-- SELECT schemaname, tablename, rowsecurity
-- FROM pg_tables
-- WHERE schemaname = 'public' 
-- AND tablename IN ('users', 'mocks', 'attempts', 'tickets');
--
-- All tables should show rowsecurity = true
