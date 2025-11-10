-- Fix RLS policies for user registration
-- This allows the service role (backend) to create new users
-- while preventing regular authenticated users from creating users

-- Drop existing insert policy if it exists
DROP POLICY IF EXISTS "users_insert_service_role" ON public.users;

-- Allow service role to insert new users (for registration)
-- Service role bypasses RLS, but we add this for clarity
CREATE POLICY "users_insert_service_role"
ON public.users FOR INSERT
TO service_role
WITH CHECK (true);

-- Note: Regular authenticated users cannot insert into users table
-- This is intentional - only the backend (using service role) can create users
