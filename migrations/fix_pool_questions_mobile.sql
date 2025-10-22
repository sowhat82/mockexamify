-- Fix Pool Questions Access
-- Run in Supabase SQL Editor

DROP POLICY IF EXISTS
"pool_questions_read"
ON pool_questions;

CREATE POLICY
"pool_questions_users"
ON pool_questions
FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1
    FROM question_pools
    WHERE id = pool_questions.pool_id
    AND is_active = true
  )
  AND NOT EXISTS (
    SELECT 1 FROM users
    WHERE id = auth.uid()
    AND role = 'admin'
  )
);

CREATE POLICY
"pool_questions_admin_all"
ON pool_questions
FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM users
    WHERE id = auth.uid()
    AND role = 'admin'
  )
);
