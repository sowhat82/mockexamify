# ChatGPT Agent Prompt: Fix Supabase RLS Policies

Copy and paste this entire prompt into ChatGPT:

---

**Role:** You are a Supabase database administrator helping me fix Row Level Security (RLS) policies.

**Context:**
- I have a Supabase project with ID: `mgdgovkyomfkcljutcsj`
- My Supabase project URL: `https://mgdgovkyomfkcljutcsj.supabase.co`
- I have a question pool called "CACS Paper 2" with 85 questions
- The questions exist in the database but aren't visible in the admin dashboard
- Diagnosis confirms this is an RLS policy issue preventing admin users from viewing pool questions

**Problem:**
The current RLS policy `pool_questions_read` on the `pool_questions` table is too restrictive. It prevents admin users from viewing questions even though they should have full access.

**Solution Required:**
I need to apply a SQL migration that:
1. Drops the overly restrictive `pool_questions_read` policy
2. Creates two new policies:
   - `pool_questions_users_read`: Allows regular users to see questions from active pools only
   - `pool_questions_admin_read_all`: Allows admin users to see ALL questions from any pool

**SQL to Execute:**

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

-- Verification query
SELECT COUNT(*) FROM pool_questions;
```

**Your Task:**

Please guide me step-by-step to apply this SQL migration. Here's what I need:

1. **Direct me to the Supabase SQL Editor:**
   - The URL should be: `https://app.supabase.com/project/mgdgovkyomfkcljutcsj/sql/new`
   - Confirm I should go there

2. **Provide the exact steps:**
   - What to click
   - Where to paste the SQL
   - How to execute it
   - What success looks like

3. **Verification steps:**
   - How to verify the policies were created
   - How to check that questions are now accessible
   - What query to run to confirm the fix worked

4. **Troubleshooting:**
   - If I see any errors, help me interpret them
   - Common issues and how to resolve them

5. **Post-fix actions:**
   - Should I refresh my application?
   - Any caching to clear?
   - How to verify in the admin dashboard

**Expected Outcome:**
After applying this fix, when I log in to my admin dashboard at `http://localhost:8501` and navigate to "Question Pool Management" → View "CACS Paper 2" pool, I should see all 85 questions displayed instead of "No questions found in this pool".

**Additional Information:**
- Project is running in development mode (not demo mode)
- Using Supabase for authentication and database
- Admin user role is stored in the `users` table with field `role = 'admin'`
- The app is a Streamlit application called MockExamify

**Please start by:**
1. Confirming you understand the task
2. Providing me with the first step to take

---

**Optional: If you have MCP or browser tools enabled, you could potentially:**
- Open the Supabase dashboard for me
- Navigate to the SQL editor
- Execute the SQL (if I provide credentials)

Otherwise, just guide me through the manual steps clearly.

Begin now!
