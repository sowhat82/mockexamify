# 🚀 Quick Fix: Apply RLS Migration Now

## Diagnosis Complete! ✅

**Problem Confirmed:**
- Your pool "CACS Paper 2" has **85 questions** in the database
- RLS (Row Level Security) policies are blocking admin access
- This causes "No questions found" to display

## Apply Fix in 2 Minutes

### Step 1: Open Supabase SQL Editor

Click this link:
**https://app.supabase.com/project/mgdgovkyomfkcljutcsj/sql/new**

### Step 2: Copy & Paste This SQL

```sql
-- Fix Admin Access to Pool Questions
DROP POLICY IF EXISTS "pool_questions_read" ON public.pool_questions;

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

### Step 3: Run the SQL

Click the **Run** button (or press `Ctrl+Enter`)

### Step 4: Verify

Refresh your admin dashboard and view the pool - all 85 questions should now be visible!

---

## Alternative: Command Line Fix

If you prefer using the command line, get your database password from:
https://app.supabase.com/project/mgdgovkyomfkcljutcsj/settings/database

Then run:
```bash
DB_PASSWORD='your-password' bash fix_pool_questions.sh
```

---

## Need More Details?

See [FIX_POOL_QUESTIONS_DISPLAY.md](FIX_POOL_QUESTIONS_DISPLAY.md) for full documentation.
