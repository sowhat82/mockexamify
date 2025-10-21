-- Verify Question Pool Tables Were Created Successfully
-- Run this in Supabase SQL Editor to confirm everything is set up

-- 1. Check if all 4 tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('question_pools', 'pool_questions', 'upload_batches', 'duplicate_cache')
ORDER BY table_name;

-- Expected result: 4 rows showing all table names

-- 2. Check table structures
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('question_pools', 'pool_questions', 'upload_batches', 'duplicate_cache')
ORDER BY table_name, ordinal_position;

-- 3. Verify indexes were created
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('question_pools', 'pool_questions', 'upload_batches', 'duplicate_cache')
ORDER BY tablename, indexname;

-- 4. Check if trigger exists
SELECT
    trigger_name,
    event_object_table,
    action_statement
FROM information_schema.triggers
WHERE trigger_schema = 'public'
  AND trigger_name = 'pool_questions_stats_trigger';

-- 5. Check RLS (Row Level Security) status
SELECT
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('question_pools', 'pool_questions', 'upload_batches', 'duplicate_cache')
ORDER BY tablename;

-- If rowsecurity = false for any table, you may need to enable RLS and add policies
