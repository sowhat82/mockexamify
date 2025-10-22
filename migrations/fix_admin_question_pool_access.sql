-- Fix Admin Access to Question Pools
-- Allows admins to view ALL question pools (including inactive ones)

-- Drop the restrictive read policy
DROP POLICY IF EXISTS "question_pools_read_active" ON public.question_pools;

-- Create separate policies for regular users and admins

-- 1. Regular users (non-admin) can only see active pools
CREATE POLICY "question_pools_users_read_active"
ON public.question_pools FOR SELECT
TO authenticated
USING (
  is_active = true
  AND NOT EXISTS (
    SELECT 1 FROM public.users u
    WHERE u.id = auth.uid()
    AND u.role = 'admin'
  )
);

-- 2. Admins can see ALL pools (active and inactive)
CREATE POLICY "question_pools_admin_read_all"
ON public.question_pools FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.users u
    WHERE u.id = auth.uid()
    AND u.role = 'admin'
  )
);

-- 3. Anonymous users can see active pools (for public browsing)
CREATE POLICY "question_pools_anon_read_active"
ON public.question_pools FOR SELECT
TO anon
USING (is_active = true);

-- Verification query (uncomment to test):
-- SELECT * FROM question_pools; -- Run this as admin to verify you see all pools
