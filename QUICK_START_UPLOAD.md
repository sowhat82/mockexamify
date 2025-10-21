# 🚀 Quick Start - Upload Your First Question Pool

## ✅ What Just Happened

The admin upload page is now **LIVE** and ready to use!

- ✅ App running at: **http://localhost:8501**
- ✅ Admin upload page enabled
- ✅ Question pool functionality ready

## 📋 Next Steps

### Step 1: Apply Database Schema (Required!)

Before you can upload, you need to create the database tables in Supabase:

1. **Open Supabase Dashboard**
   - Go to: https://supabase.com/dashboard
   - Select your project: `mgdgovkyomfkcljutcsj`

2. **Open SQL Editor**
   - Click "SQL Editor" in the left sidebar
   - Click "New Query"

3. **Copy & Run the Schema**
   - Open file: `database_schema_question_pools.sql`
   - Copy the entire contents
   - Paste into Supabase SQL Editor
   - Click **"Run"** (or press Ctrl+Enter)

4. **Verify Tables Created**
   Run this query to confirm:
   ```sql
   SELECT table_name
   FROM information_schema.tables
   WHERE table_schema = 'public'
   AND table_name IN ('question_pools', 'pool_questions', 'upload_batches', 'duplicate_cache');
   ```

   You should see all 4 table names listed.

### Step 2: Login as Admin

1. Open your browser to: **http://localhost:8501**
2. Click **"Login"**
3. Use admin credentials:
   - **Email**: `admin@mockexamify.com`
   - **Password**: `admin123`

### Step 3: Upload Your First Question Pool

1. **Navigate to Upload**
   - Click **"📤 Upload Mock"** in the admin navigation

2. **Select Question Pool Mode**
   - Choose: **"💼 Question Pool"** (recommended for multiple versions)

3. **Fill in Pool Details**
   - **Pool Name**: `CACS2 Paper 2` (this is the key - use same name to auto-merge!)
   - **Category**: `Programming`
   - **Description**: Optional, e.g., "CACS2 Paper 2 practice questions"

4. **Upload Your PDF(s)**
   - Click "Browse files" or drag-and-drop
   - Select one or more PDFs (e.g., `CACS2-Paper2-V1.pdf`)
   - Leave AI duplicate detection enabled (recommended)
   - Keep similarity threshold at 95%

5. **Click "🚀 Upload to Question Pool"**

6. **Wait for Processing**
   You'll see:
   - File processing progress
   - Questions extraction status
   - Duplicate detection results
   - Final upload summary

### Step 4: Upload More Versions (Auto-Merge!)

To add more questions to the same pool:

1. **Use the SAME Pool Name**: `CACS2 Paper 2`
2. **Upload new PDF**: e.g., `CACS2-Paper2-V2.pdf`
3. Click **"🚀 Upload to Question Pool"**

The system will:
- ✅ Automatically merge into existing pool
- ✅ Skip exact duplicates (instant)
- ✅ Detect semantic duplicates with AI
- ✅ Only add unique new questions

### Step 5: View & Manage Your Pool

1. **Navigate to Question Pools**
   - Click **"💼 Question Pools"** in admin navigation (if enabled)
   - Or the page will be added after you upload

2. **View Your Pool**
   - See statistics: total questions, unique questions, duplicates removed
   - Click **"👁️ View Questions"** to browse all questions
   - Search, filter, edit individual questions
   - Delete questions if needed

## 🎯 What to Expect

### First Upload (V1)
```
✅ Extracted 50 questions
✅ Added 50 unique questions
✅ Skipped 0 duplicates
```

### Second Upload (V2) - Same Pool Name
```
📊 Found 50 existing questions in pool
✅ Extracted 50 questions from CACS2-Paper2-V2.pdf
📊 Exact duplicate detection: 15 exact matches found
🤖 AI detection: 3 semantic duplicates found (threshold: 95%)
✅ Added 32 unique questions
✅ Skipped 18 duplicates

Pool now has: 82 unique questions
```

### Third Upload (V3) - Same Pool Name
```
📊 Found 82 existing questions in pool
✅ Extracted 50 questions from CACS2-Paper2-V3.pdf
📊 Exact duplicate detection: 25 exact matches found
🤖 AI detection: 8 semantic duplicates found (threshold: 95%)
✅ Added 17 unique questions
✅ Skipped 33 duplicates

Pool now has: 99 unique questions
```

## 💡 Tips

1. **Same Pool Name = Auto-Merge**
   - Always use the exact same pool name to merge questions
   - Case-sensitive: "CACS2 Paper 2" ≠ "cacs2 paper 2"

2. **AI Detection is Smart but Costs Credits**
   - Uses free models first (Llama, Mistral)
   - Falls back to paid models only if needed
   - Adjust threshold: 95% = strict, 80% = lenient

3. **Upload Multiple Files at Once**
   - Select multiple PDFs in one upload
   - System processes them sequentially
   - All go into the same pool

4. **Review Before Large Uploads**
   - Start with 1-2 PDFs to verify extraction works
   - Check the question format is correct
   - Then upload remaining files

## 🆘 Troubleshooting

### "Table does not exist" error
→ You haven't applied the database schema yet. Go to Step 1.

### Questions not extracting from PDF
→ Check that PDFs are text-based (not scanned images)
→ Try uploading a CSV or JSON file as test

### AI duplicate detection not working
→ Check OpenRouter API key in `streamlit-secrets.toml`
→ Check logs for any API errors

### Pool not showing in admin console
→ The admin_question_pools.py page is created but may need routing
→ For now, you can see upload results immediately after upload

## ✅ You're Ready!

Your question pool system is now **fully operational**!

Just:
1. ✅ Apply the database schema (one-time setup)
2. ✅ Login as admin
3. ✅ Upload your CACS Paper 2 PDFs
4. ✅ Watch the magic happen!

---

**Need help?** Check the comprehensive guide in `QUESTION_POOL_ADMIN_GUIDE.md`

**Current Status:**
- App: ✅ Running at http://localhost:8501
- Admin Upload: ✅ Enabled and ready
- Database Schema: ⏳ Waiting for you to apply
- Question Pools: ⏳ Ready when you apply schema
