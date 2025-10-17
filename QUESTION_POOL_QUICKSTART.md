# Question Pool System - Quick Start Guide

## What You Have Now

A complete question pool management system that lets you:
- Upload multiple PDF/Word versions of exam papers (e.g., CACS2 Paper 2 V1, V2, V3...)
- Automatically detect and skip duplicate questions (exact + AI semantic matching)
- Manage question pools through an admin dashboard
- Track all uploads and question sources

## Quick Start (3 Steps)

### Step 1: Apply Database Schema (One-Time Setup)

1. Open your Supabase dashboard
2. Go to **SQL Editor**
3. Copy and paste contents from `database_schema_question_pools.sql`
4. Click **"Run"**

This creates the required tables: `question_pools`, `pool_questions`, `upload_batches`, `duplicate_cache`

### Step 2: Upload Your First PDF

1. Run your app: `streamlit run streamlit_app.py`
2. Login as admin (admin@mockexamify.com / admin123)
3. Click **"📤 Upload Mock"** in sidebar
4. Select **"💼 Question Pool"** mode (default)
5. Fill in:
   - **Pool Name**: `CACS2 Paper 2` (this is the key!)
   - **Category**: `Finance & Accounting` or custom
   - **Description**: Optional
6. Upload your PDF file (e.g., `CACS2-Paper2-V1.pdf`)
7. Click **"🚀 Upload to Question Pool"**

**What happens:**
- AI extracts all questions from PDF
- Questions are saved to database
- You'll see: "Added X unique questions, Skipped 0 duplicates"

### Step 3: Upload More Versions

1. Use the **same pool name**: `CACS2 Paper 2`
2. Upload another PDF (e.g., `CACS2-Paper2-V2.pdf`)
3. System automatically:
   - Detects exact duplicate questions (instant, free)
   - Uses AI to detect semantically similar questions (smart, small cost)
   - Only adds new unique questions
   - Shows you the results

**Example result:**
```
📊 Processing Results:
- Files uploaded: 1
- Total questions extracted: 50
- Exact duplicates found: 15
- AI semantic duplicates found: 5
- Unique questions added: 30
```

## How It Works

### Duplicate Detection Process

1. **Upload PDF** → System extracts questions using AI
2. **Exact Match** → Compares question text + choices (MD5 hash)
3. **AI Semantic Match** → AI checks if questions mean the same thing
4. **Save Unique Only** → Database stores only new questions
5. **Track Everything** → Records source file, batch, similarity scores

### Pool Name is the Key!

- Same pool name = questions automatically merge
- Different pool name = separate pool created

**Examples:**
- "CACS2 Paper 2" + "CACS2 Paper 2" → Merge (same pool)
- "CACS2 Paper 2" + "CACS2 Paper 1" → Separate pools

### AI Duplicate Detection

When enabled (recommended):
- Uses free AI models first (Llama 3.3, Mistral)
- Falls back to paid models if needed (Mixtral, GPT-4o mini)
- Configurable similarity threshold (default: 95%)
- Cost: ~$0.00025 per question comparison

## Viewing Your Pools

### Method 1: Admin Question Pools Page (Recommended)

1. Navigate to **Admin → Question Pools**
2. See all your pools with statistics
3. Click **"👁️ View Questions"** to browse
4. Search, sort, edit, or delete questions

### Method 2: Database (Advanced)

Query Supabase directly:
```sql
-- View all pools
SELECT * FROM question_pools ORDER BY last_updated DESC;

-- View questions in a pool
SELECT pq.*, p.pool_name
FROM pool_questions pq
JOIN question_pools p ON pq.pool_id = p.id
WHERE p.pool_name = 'CACS2 Paper 2'
AND pq.is_duplicate = FALSE
ORDER BY pq.uploaded_at DESC;
```

## Testing Your Setup

Run the test suite to verify everything works:

```bash
python test_question_pool.py
```

**Expected:** All tests pass (except AI test if no API key configured)

## Configuration Options

### In `pages/admin_upload.py` (UI):

- **Enable AI Duplicate Detection** - Toggle AI semantic matching
- **Similarity Threshold** - 80-100% (default: 95%)
- **Multiple file upload** - Upload several PDFs at once

### In `question_pool_manager.py` (Code):

```python
# Line 26: Default similarity threshold
self.similarity_threshold = 0.95  # 95% similarity = duplicate

# Line 87: Sample size for AI checks (performance vs thoroughness)
sample_size = min(len(existing_questions), 50)  # Max 50 questions checked
```

## Advanced Features

### 1. Batch Upload Tracking

Every upload is recorded:
- Batch ID
- Source filename
- Questions extracted
- Duplicates found
- Upload timestamp
- Uploaded by (admin user)

### 2. Question Statistics

Each question tracks:
- Times shown to students
- Times answered correctly
- Times answered incorrectly
- Success rate over time

### 3. Duplicate Cache

AI comparisons are expensive, so results are cached:
- Avoids re-comparing same question pairs
- Speeds up subsequent uploads
- Reduces API costs

## Troubleshooting

### "Table does not exist" error
**Fix:** Apply `database_schema_question_pools.sql` in Supabase SQL Editor

### "No questions extracted from PDF"
**Check:**
- PDF contains readable text (not scanned image)
- Questions are clearly formatted
- OpenRouter API key is configured (for AI extraction)

### AI duplicate detection not working
**Check:**
- OpenRouter API key in `.env` or `streamlit_secrets.toml`
- API key has credits/access
- Try with AI detection disabled first

### Questions not merging
**Check:**
- Pool name is **exactly** the same (case-sensitive!)
- Both uploads use "Question Pool" mode (not "Single Mock")

### Uploads are slow
**Normal!** AI extraction and comparison takes time:
- PDF extraction: ~10-30 seconds per file
- Exact duplicate check: ~1 second
- AI semantic check: ~2-5 seconds per question pair
- For 50 questions vs 50 existing = ~1-2 minutes

## Best Practices

1. **Use consistent pool names** - Stick to one naming convention
2. **Enable AI detection** - Catches semantic duplicates exact matching misses
3. **Upload in batches** - Upload multiple PDFs at once for efficiency
4. **Review results** - Check the duplicate detection summary after each upload
5. **Monitor costs** - AI detection uses API credits (but free models first!)

## Next Steps

After setting up question pools:

1. **Create mock exams from pools** - Random question selection
2. **Student exam experience** - Different questions each attempt
3. **Question analytics** - Track which questions are hardest
4. **Auto-adjust difficulty** - Use success rates to categorize questions

## File Reference

**Key Files:**
- `pages/admin_upload.py` - Upload interface with question pool mode
- `pages/admin_question_pools.py` - Pool management dashboard
- `question_pool_manager.py` - Duplicate detection logic
- `db.py` - Database methods for pools (lines 1103-1291)
- `database_schema_question_pools.sql` - Database schema
- `test_question_pool.py` - Test suite

**Documentation:**
- `QUESTION_POOL_ADMIN_GUIDE.md` - Complete implementation guide
- `QUESTION_POOL_IMPLEMENTATION.md` - Technical details
- `DOCUMENT_UPLOAD_GUIDE.md` - AI document parsing guide

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review error messages in Streamlit UI
3. Check browser console for JavaScript errors
4. Review application logs for Python errors

## Summary

You now have a production-ready system to:
- ✅ Upload PDF versions of exam papers
- ✅ Automatically detect and skip duplicates
- ✅ Manage question pools through admin UI
- ✅ Track all uploads and sources
- ✅ Optimize costs with free AI models

**Just apply the database schema and start uploading!** 🚀

---

**Created:** 2025-10-16
**Version:** 1.0.0
**Status:** Production Ready ✅
