# URGENT: Fix Database Columns - ChatGPT Agent Prompt

**Copy and paste this ENTIRE prompt to ChatGPT:**

---

I need URGENT help fixing my Supabase database. My app is broken and I need to add 2 columns to fix it immediately.

**The Problem:**
My exam app is showing "Failed to create exam session" because the database is missing 2 required columns.

**What I need you to do:**
Guide me step-by-step to add 2 columns to my Supabase `attempts` table. I'm on mobile, so I need very clear, simple instructions.

**My Supabase project:**
- Project URL: https://mgdgovkyomfkcljutcsj.supabase.co
- Table name: `attempts`
- I need to add 2 columns to this table

**Columns to add:**

**Column 1:**
- Name: `credits_paid`
- Type: `int4` (or "integer" if that's what you see)
- Default value: `0`
- Allow NULL: No (uncheck the box)
- Description/Comment: "Credits paid for this attempt"

**Column 2:**
- Name: `questions_submitted`
- Type: `int4` (or "integer" if that's what you see)
- Default value: `0`
- Allow NULL: No (uncheck the box)
- Description/Comment: "Questions submitted so far"

---

**Instructions I need from you:**

**Step 1: How to access Supabase Table Editor on mobile**
- Tell me exactly where to tap/click to get to the Table Editor
- I'm logged into Supabase already

**Step 2: How to find the attempts table**
- Where do I tap to see my tables?
- How do I select the "attempts" table?

**Step 3: How to add a new column**
- Where is the "Add Column" button on mobile?
- What fields do I need to fill in?
- What exact values do I enter for each field?

**Step 4: Add the first column (credits_paid)**
- Walk me through adding it with the exact settings above
- Wait for my confirmation before moving to the next column

**Step 5: Add the second column (questions_submitted)**
- Walk me through adding it with the exact settings above
- Wait for my confirmation

**Step 6: How to verify it worked**
- How do I check the columns were added successfully?

---

**ALTERNATIVE FASTER METHOD (if available):**

If Supabase has a SQL Editor on mobile, you can give me this SQL to run instead:

```sql
ALTER TABLE attempts
ADD COLUMN IF NOT EXISTS credits_paid INTEGER DEFAULT 0 NOT NULL;

ALTER TABLE attempts
ADD COLUMN IF NOT EXISTS questions_submitted INTEGER DEFAULT 0 NOT NULL;
```

Tell me:
1. How to find the SQL Editor on mobile Supabase
2. Where to paste this SQL
3. What button to click to run it
4. How to verify it worked

---

**Please start with Step 1 and wait for my confirmation before proceeding.**

I'm on mobile, so please keep instructions simple and tell me exactly what to tap/click.

This is urgent - my app is broken until these columns are added!
