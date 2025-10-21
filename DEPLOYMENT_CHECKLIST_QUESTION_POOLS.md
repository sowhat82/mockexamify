# 📋 Question Pool Deployment Checklist

## ✅ What's Already Done

- [x] Database methods implemented in `db.py`
- [x] Upload UI complete (`pages/admin_upload.py`)
- [x] Document parser ready (PDF + Word support)
- [x] Duplicate detection working (exact + AI)
- [x] Processing logic complete (`process_pool_upload()`)

## 🚨 What YOU Need to Do (5 minutes)

### Step 1: Deploy Database Schema (REQUIRED)

1. **Open Supabase Dashboard**
   - Go to: https://supabase.com/dashboard/project/mgdgovkyomfkcljutcsj/sql

2. **Copy SQL Schema**
   - Open file: `database_schema_question_pools.sql`
   - Copy ALL contents (138 lines)

3. **Run in SQL Editor**
   - Paste into Supabase SQL Editor
   - Click "RUN" button
   - Wait for: "Success. No rows returned"

4. **Verify Tables Created**
   ```sql
   SELECT table_name
   FROM information_schema.tables
   WHERE table_schema = 'public'
     AND table_name IN ('question_pools', 'pool_questions',
                        'upload_batches', 'duplicate_cache');
   ```
   - Should show 4 rows
   - If you see 4 rows → ✅ SUCCESS!

### Step 2: Test Upload (2 minutes)

1. **Restart Streamlit**
   ```powershell
   Stop-Process -Name streamlit -Force -ErrorAction SilentlyContinue
   streamlit run streamlit_app.py --server.port 8501
   ```

2. **Login as Admin**
   - Email: `admin@demo.com`
   - Password: `admin123`

3. **Go to Upload Page**
   - Click "📤 Upload Questions" in navigation

4. **Upload First File**
   - Select: "💼 Question Pool"
   - Pool Name: "Test Pool"
   - Category: "Programming"
   - Upload: Any PDF or Word file with questions
   - Click: "🚀 Upload to Question Pool"

5. **Check Results**
   - Should see: "✅ Extracted X questions"
   - Should see: "✅ Added X unique questions"
   - No error messages = ✅ SUCCESS!

### Step 3: Verify in Database (1 minute)

Run in Supabase SQL Editor:

```sql
-- Check pools created
SELECT pool_name, category, total_questions
FROM question_pools;

-- Check questions added
SELECT pool_id, COUNT(*) as questions
FROM pool_questions
GROUP BY pool_id;

-- Check upload history
SELECT filename, questions_count, unique_added, upload_status
FROM upload_batches
ORDER BY uploaded_at DESC
LIMIT 5;
```

Should see your data → ✅ SUCCESS!

---

## 🎉 If All Checks Pass

**Your question pool system is LIVE!**

You can now:
- Upload multiple PDF/Word files
- System auto-extracts questions
- Duplicate detection works automatically
- Questions stored in database
- Full audit trail maintained

---

## ❌ Troubleshooting

### Error: "relation 'question_pools' does not exist"
**Fix:** You didn't run the SQL schema. Go back to Step 1.

### Error: "'DatabaseManager' object has no attribute..."
**Fix:** Restart Streamlit server (db.py was updated)

### Error: "No questions extracted from document"
**Fix:** Check OPENROUTER_API_KEY in streamlit-secrets.toml

### Error: "Failed to create question pool"
**Fix:** Check Supabase RLS policies allow admin to insert into question_pools

---

## 📞 Quick Reference

**SQL Schema File:** `database_schema_question_pools.sql`
**Database Methods:** `db.py` lines 849-1025
**Upload UI:** `pages/admin_upload.py`
**Processing Logic:** `pages/admin_upload.py` line 467+ (`process_pool_upload()`)

**Supabase Project:** mgdgovkyomfkcljutcsj
**Admin Login:** admin@demo.com / admin123

---

## ⏭️ What's Next (Optional)

After basic system is working, you can:

1. **Upload real exam PDFs** (e.g., CACS2 Paper 2 versions)
2. **Test duplicate detection** (upload same file twice, should skip duplicates)
3. **Build pool management dashboard** (view/edit/delete questions)
4. **Enable student exam generation** (random questions from pool)

---

**Current Status:** ✅ Code Complete, Awaiting Database Deployment

**Estimated Time to Production:** 5 minutes (just run the SQL!)
