-- Fix Admin Access to Pool Questions
-- Allows admins to view ALL pool questions

-- Drop the restrictive read policy
DROP POLICY IF EXISTS "pool_questions_read" ON public.pool_questions;

-- Create separate policies for regular users and admins

-- 1. Regular users can only see questions from active pools
CREATE POLICY "pool_questions_users_read"
ON public.pool_questions FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.question_pools qp
    WHERE qp.id = pool_questions.pool_id
    AND qp.is_active = true
  )
  AND NOT EXISTS (
    SELECT 1 FROM public.users u
    WHERE u.id = auth.uid()
    AND u.role = 'admin'
  )
);

-- 2. Admins can see ALL questions (from any pool)
CREATE POLICY "pool_questions_admin_read_all"
ON public.pool_questions FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.users u
    WHERE u.id = auth.uid()
    AND u.role = 'admin'
  )
);

-- Verification: Run as admin to see all questions
-- SELECT COUNT(*) FROM pool_questions;
