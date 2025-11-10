-- Verify RLS policies are set up correctly
-- Run this in Supabase SQL Editor to check current policies

-- Check if RLS is enabled on users table
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename = 'users';

-- List all policies on users table
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE schemaname = 'public'
AND tablename = 'users';

-- Check if the service role policy exists
SELECT policyname
FROM pg_policies
WHERE schemaname = 'public'
AND tablename = 'users'
AND policyname = 'users_insert_service_role';
