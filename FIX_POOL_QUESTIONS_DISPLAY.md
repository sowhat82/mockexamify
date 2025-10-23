# Fix: Pool Questions Not Displaying in Admin Dashboard

## Problem
When viewing question pools in the admin dashboard, you see "No questions found in this pool" even though questions have been uploaded.

## Root Cause
The Supabase Row Level Security (RLS) policies for the `pool_questions` table are too restrictive. The current policy prevents admins from viewing questions because it only allows viewing questions from active pools for regular authenticated users.

## Solution
Apply the RLS migration that creates separate policies for admins and regular users.

## Fix Instructions

### Option 1: Using Supabase Dashboard (Easiest)

1. Go to your Supabase Dashboard: https://app.supabase.com/project/mgdgovkyomfkcljutcsj

2. Navigate to **SQL Editor** (in the left sidebar)

3. Copy and paste this SQL:

```sql
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
```

4. Click **Run** or press `Ctrl+Enter`

5. Refresh your admin dashboard - questions should now be visible!

### Option 2: Using Command Line Script

1. Get your Supabase database password:
   - Go to: https://app.supabase.com/project/mgdgovkyomfkcljutcsj/settings/database
   - Scroll to "Connection string" section
   - Copy or reset your database password

2. Run the fix script:
```bash
DB_PASSWORD='your-password-here' bash fix_pool_questions.sh
```

Alternatively, add to your `.env` file:
```env
SUPABASE_DB_URL=postgresql://postgres.mgdgovkyomfkcljutcsj:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

Then run:
```bash
SQL_FILE=migrations/fix_admin_pool_questions_access.sql python apply_supabase_sql.py
```

## Verification

After applying the fix:

1. Log in to the admin dashboard
2. Navigate to "Question Pool Management"
3. Click "View Questions" on any pool
4. Questions should now be visible

You can also verify in Supabase SQL Editor:
```sql
-- Check RLS policies
SELECT schemaname, tablename, policyname
FROM pg_policies
WHERE tablename = 'pool_questions';

-- Count questions (as admin)
SELECT COUNT(*) FROM pool_questions;
```

## Technical Details

**What Changed:**
- Before: Single RLS policy that checked if pool is active
- After: Two separate policies:
  - `pool_questions_users_read`: Regular users see questions from active pools only
  - `pool_questions_admin_read_all`: Admins see ALL questions from any pool

**Why This Fixes It:**
The admin user's JWT token contains their role. The new policy checks if `auth.uid()` matches a user with `role = 'admin'` in the users table, and if so, grants access to all pool questions.

## Related Files
- Migration file: `migrations/fix_admin_pool_questions_access.sql`
- Admin dashboard: `app_pages/admin_question_pools.py`
- Database layer: `db.py` (see `get_pool_questions` method)
- Helper script: `fix_pool_questions.sh`

## Need Help?

If you continue to see issues after applying this fix:

1. Check that you're logged in as an admin user
2. Verify the RLS policies were created (see Verification section)
3. Check browser console for any JavaScript errors
4. Check Supabase logs for auth/policy errors
