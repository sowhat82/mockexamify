-- Enable RLS for Question Pool Tables
-- Fixes Supabase linter errors for pool_questions, question_pools, upload_batches, duplicate_cache

-- ====================
-- QUESTION_POOLS TABLE
-- ====================
ALTER TABLE IF EXISTS public.question_pools ENABLE ROW LEVEL SECURITY;

-- Public/authenticated can view active question pools
CREATE POLICY IF NOT EXISTS "question_pools_read_active"
ON public.question_pools FOR SELECT
TO anon, authenticated
USING (is_active = true);

-- Only admins can insert question pools
CREATE POLICY IF NOT EXISTS "question_pools_admin_insert"
ON public.question_pools FOR INSERT
TO authenticated
WITH CHECK (EXISTS (
  SELECT 1 FROM public.users u WHERE u.id = auth.uid() AND u.role = 'admin'
));

-- Only admins can update question pools
CREATE POLICY IF NOT EXISTS "question_pools_admin_update"
ON public.question_pools FOR UPDATE
TO authenticated
USING (EXISTS (
  SELECT 1 FROM public.users u WHERE u.id = auth.uid() AND u.role = 'admin'
));

-- Only admins can delete question pools
CREATE POLICY IF NOT EXISTS "question_pools_admin_delete"
ON public.question_pools FOR DELETE
TO authenticated
USING (EXISTS (
  SELECT 1 FROM public.users u WHERE u.id = auth.uid() AND u.role = 'admin'
));


-- ====================
-- POOL_QUESTIONS TABLE
-- ====================
ALTER TABLE IF EXISTS public.pool_questions ENABLE ROW LEVEL SECURITY;

-- Authenticated users can view non-duplicate questions from active pools
CREATE POLICY IF NOT EXISTS "pool_questions_read"
ON public.pool_questions FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM public.question_pools qp
    WHERE qp.id = pool_questions.pool_id
    AND qp.is_active = true
  )
);

-- Only admins can insert questions
CREATE POLICY IF NOT EXISTS "pool_questions_admin_insert"
ON public.pool_questions FOR INSERT
TO authenticated
WITH CHECK (EXISTS (
  SELECT 1 FROM public.users u WHERE u.id = auth.uid() AND u.role = 'admin'
));

-- Only admins can update questions
CREATE POLICY IF NOT EXISTS "pool_questions_admin_update"
ON public.pool_questions FOR UPDATE
TO authenticated
USING (EXISTS (
  SELECT 1 FROM public.users u WHERE u.id = auth.uid() AND u.role = 'admin'
));

-- Only admins can delete questions
CREATE POLICY IF NOT EXISTS "pool_questions_admin_delete"
ON public.pool_questions FOR DELETE
TO authenticated
USING (EXISTS (
  SELECT 1 FROM public.users u WHERE u.id = auth.uid() AND u.role = 'admin'
));


-- ====================
-- UPLOAD_BATCHES TABLE
-- ====================
ALTER TABLE IF EXISTS public.upload_batches ENABLE ROW LEVEL SECURITY;

-- Only admins can view upload batches
CREATE POLICY IF NOT EXISTS "upload_batches_admin_read"
ON public.upload_batches FOR SELECT
TO authenticated
USING (EXISTS (
  SELECT 1 FROM public.users u WHERE u.id = auth.uid() AND u.role = 'admin'
));

-- Only admins can insert upload batches
CREATE POLICY IF NOT EXISTS "upload_batches_admin_insert"
ON public.upload_batches FOR INSERT
TO authenticated
WITH CHECK (EXISTS (
  SELECT 1 FROM public.users u WHERE u.id = auth.uid() AND u.role = 'admin'
));

-- Only admins can update upload batches
CREATE POLICY IF NOT EXISTS "upload_batches_admin_update"
ON public.upload_batches FOR UPDATE
TO authenticated
USING (EXISTS (
  SELECT 1 FROM public.users u WHERE u.id = auth.uid() AND u.role = 'admin'
));

-- Only admins can delete upload batches
CREATE POLICY IF NOT EXISTS "upload_batches_admin_delete"
ON public.upload_batches FOR DELETE
TO authenticated
USING (EXISTS (
  SELECT 1 FROM public.users u WHERE u.id = auth.uid() AND u.role = 'admin'
));


-- ====================
-- DUPLICATE_CACHE TABLE
-- ====================
ALTER TABLE IF EXISTS public.duplicate_cache ENABLE ROW LEVEL SECURITY;

-- Only admins can view duplicate cache
CREATE POLICY IF NOT EXISTS "duplicate_cache_admin_read"
ON public.duplicate_cache FOR SELECT
TO authenticated
USING (EXISTS (
  SELECT 1 FROM public.users u WHERE u.id = auth.uid() AND u.role = 'admin'
));

-- Only admins can insert into duplicate cache
CREATE POLICY IF NOT EXISTS "duplicate_cache_admin_insert"
ON public.duplicate_cache FOR INSERT
TO authenticated
WITH CHECK (EXISTS (
  SELECT 1 FROM public.users u WHERE u.id = auth.uid() AND u.role = 'admin'
));

-- Only admins can update duplicate cache
CREATE POLICY IF NOT EXISTS "duplicate_cache_admin_update"
ON public.duplicate_cache FOR UPDATE
TO authenticated
USING (EXISTS (
  SELECT 1 FROM public.users u WHERE u.id = auth.uid() AND u.role = 'admin'
));

-- Only admins can delete from duplicate cache
CREATE POLICY IF NOT EXISTS "duplicate_cache_admin_delete"
ON public.duplicate_cache FOR DELETE
TO authenticated
USING (EXISTS (
  SELECT 1 FROM public.users u WHERE u.id = auth.uid() AND u.role = 'admin'
));


-- ====================
-- VERIFICATION
-- ====================
-- Run this query to verify RLS is enabled:
-- SELECT schemaname, tablename, rowsecurity
-- FROM pg_tables
-- WHERE schemaname = 'public'
-- AND tablename IN ('question_pools', 'pool_questions', 'upload_batches', 'duplicate_cache');
