# ChatGPT Agent Prompt: Add Pro-Rata Refund Columns to Attempts Table

Copy and paste this entire prompt to ChatGPT:

---

I need you to help me add two new columns to my Supabase database table called `attempts`.

**Context:**
- I'm implementing a pro-rata refund system for incomplete exams
- When students abandon an exam, they get refunded based on how many questions they completed
- I need to track: (1) how many credits they paid, and (2) how many questions they submitted

**Your task:**
Guide me step-by-step through adding these columns via the Supabase dashboard:

**Columns to add:**
1. Column name: `credits_paid`
   - Type: `int4` (integer)
   - Default value: `0`
   - Nullable: No
   - Description: "Number of credits paid for this attempt (for pro-rata refunds)"

2. Column name: `questions_submitted`
   - Type: `int4` (integer)
   - Default value: `0`
   - Nullable: No
   - Description: "Number of questions submitted so far (for progress tracking)"

**Instructions for you to provide:**
1. Walk me through accessing the Supabase Table Editor
2. Show me exactly where to click to add a new column
3. Tell me exactly what values to enter in each field
4. Include screenshots descriptions if helpful
5. After adding columns, help me verify they were created correctly

**My Supabase project URL:** https://mgdgovkyomfkcljutcsj.supabase.co

Please start with step 1 and wait for my confirmation before proceeding to the next step.

---

**Alternative SQL Method:**

If you prefer, you can also run this SQL directly in the Supabase SQL Editor:

```sql
-- Add fields for pro-rata refund tracking to attempts table
ALTER TABLE attempts
ADD COLUMN IF NOT EXISTS credits_paid INTEGER DEFAULT 0;

ALTER TABLE attempts
ADD COLUMN IF NOT EXISTS questions_submitted INTEGER DEFAULT 0;

-- Add helpful comments
COMMENT ON COLUMN attempts.credits_paid IS 'Number of credits paid for this attempt (for pro-rata refunds)';
COMMENT ON COLUMN attempts.questions_submitted IS 'Number of questions submitted so far (for progress tracking)';
```

Guide me through:
1. Finding the SQL Editor in Supabase
2. Pasting and running this SQL
3. Verifying the columns were created successfully
