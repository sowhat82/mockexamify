-- Fix Admin Question Pool Access
-- Run this in Supabase SQL Editor

DROP POLICY IF EXISTS
"question_pools_read_active"
ON question_pools;

CREATE POLICY
"question_pools_users_active"
ON question_pools
FOR SELECT
TO authenticated
USING (
  is_active = true
  AND NOT EXISTS (
    SELECT 1 FROM users
    WHERE id = auth.uid()
    AND role = 'admin'
  )
);

CREATE POLICY
"question_pools_admin_all"
ON question_pools
FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM users
    WHERE id = auth.uid()
    AND role = 'admin'
  )
);

CREATE POLICY
"question_pools_anon_active"
ON question_pools
FOR SELECT
TO anon
USING (is_active = true);
