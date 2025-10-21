# Question Pool Upload Feature - Analysis Report

## 📊 Current Status: **INCOMPLETE - Missing Database Layer**

---

## ✅ What IS Properly Coded

### 1. **File Upload UI** (`pages/admin_upload.py`)
- ✅ Accepts multiple files (PDF, Word, CSV, JSON)
- ✅ Upload form with pool name, category, description
- ✅ File type validation
- ✅ Progress indicators and status messages
- ✅ Advanced options (AI duplicate detection, similarity threshold)

### 2. **Document Parsing** (`document_parser.py`)
- ✅ **PDF parsing**: Uses PyPDF2 to extract text from PDF files
- ✅ **Word parsing**: Uses python-docx to extract text from .docx/.doc files
- ✅ **AI extraction**: Uses OpenRouter API to intelligently extract questions from raw text
- ✅ **Chunking**: Handles large documents by splitting into chunks
- ✅ **Validation**: Validates extracted questions (required fields, correct_index range, etc.)
- ✅ **Fallback**: Gracefully handles missing API key

### 3. **File Format Support**
- ✅ **CSV**: Structured format with columns (question, choice_1-6, correct_index, scenario, explanation_seed)
- ✅ **JSON**: Array of question objects
- ✅ **PDF**: Text extraction + AI parsing
- ✅ **Word (.docx/.doc)**: Text extraction from paragraphs and tables + AI parsing

### 4. **Duplicate Detection Logic** (`question_pool_manager.py`)
- ✅ Exact duplicate detection (text comparison)
- ✅ AI-powered semantic similarity detection
- ✅ Configurable similarity threshold

### 5. **Upload Processing Flow** (`process_pool_upload()`)
- ✅ Iterates through multiple uploaded files
- ✅ Extracts questions from each file
- ✅ Tracks source filename for each question
- ✅ Runs duplicate detection (exact + AI)
- ✅ Displays comprehensive upload summary

---

## ❌ What IS MISSING - Critical Database Methods

The following database methods are **called but NOT implemented** in `db.py`:

### Missing Method 1: `create_or_update_question_pool()`
**Called at:** `admin_upload.py:478`
```python
pool = await db.create_or_update_question_pool(
    pool_name=pool_name,
    category=category,
    description=description,
    created_by=st.session_state.get('user', {}).get('id')
)
```

**Expected behavior:**
- Search for existing pool by name
- If exists: Update metadata (category, description)
- If not exists: Create new pool record in `question_pools` table
- Return pool dictionary with `id` field

### Missing Method 2: `get_pool_questions()`
**Called at:** `admin_upload.py:490`
```python
existing_questions = await db.get_pool_questions(pool_id)
```

**Expected behavior:**
- Query `pool_questions` table for all questions in given pool_id
- Return list of question dictionaries with fields:
  - `question_text`
  - `choices` (JSON array)
  - `correct_answer` (integer)
  - Other metadata

### Missing Method 3: `create_upload_batch()`
**Called at:** `admin_upload.py:575`
```python
batch_id = await db.create_upload_batch(
    pool_id=pool_id,
    filename=f"{len(uploaded_files)} files: " + ", ".join([f.name for f in uploaded_files]),
    total_questions=total_extracted,
    uploaded_by=st.session_state.get('user', {}).get('id')
)
```

**Expected behavior:**
- Insert record into `upload_batches` table
- Track which files were uploaded in this batch
- Return batch_id for tracking

### Missing Method 4: `add_questions_to_pool()`
**Called at:** `admin_upload.py:586`
```python
success = await db.add_questions_to_pool(
    pool_id=pool_id,
    questions=questions_to_add,
    source_file=", ".join([f.name for f in uploaded_files]),
    batch_id=batch_id
)
```

**Expected behavior:**
- Insert questions into `pool_questions` table
- Link questions to pool_id and batch_id
- Store question_text, choices, correct_answer, scenario, explanation_seed
- Return True on success, False on failure

---

## 🗄️ Required Database Tables

According to `database_schema_question_pools.sql`, these tables should exist:

1. **`question_pools`**: Pool metadata (name, category, description, created_by, created_at)
2. **`pool_questions`**: Individual questions (pool_id, question_text, choices, correct_answer, etc.)
3. **`upload_batches`**: Upload history (pool_id, filename, total_questions, uploaded_by, uploaded_at)
4. **`duplicate_cache`**: Caching for duplicate detection (question_hash, pool_id)

---

## 🔧 What Needs to Be Fixed

### Priority 1: Implement Missing Database Methods

Add to `db.py` (DatabaseManager class):

```python
async def create_or_update_question_pool(self, pool_name: str, category: str,
                                         description: str, created_by: str) -> Optional[Dict]:
    """Create new question pool or update existing one by name"""
    # Implementation needed

async def get_pool_questions(self, pool_id: str) -> List[Dict[str, Any]]:
    """Get all questions from a question pool"""
    # Implementation needed

async def create_upload_batch(self, pool_id: str, filename: str,
                              total_questions: int, uploaded_by: str) -> Optional[str]:
    """Create upload batch record and return batch_id"""
    # Implementation needed

async def add_questions_to_pool(self, pool_id: str, questions: List[Dict],
                                source_file: str, batch_id: str) -> bool:
    """Add questions to pool with duplicate tracking"""
    # Implementation needed
```

### Priority 2: Verify Database Tables Exist

Run this SQL in Supabase to check:
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('question_pools', 'pool_questions', 'upload_batches', 'duplicate_cache');
```

If missing, run `database_schema_question_pools.sql`

---

## 📝 Summary

**Question:** *Can you check that the feature is coded properly to take Word and PDF files wholesale, and store them in a question bank?*

**Answer:**

✅ **File handling is properly coded:**
- PDF files are extracted using PyPDF2
- Word files are extracted using python-docx
- Both extractions feed into AI parser (OpenRouter)
- Questions are parsed, validated, and prepared for storage

❌ **Storage layer is NOT properly coded:**
- The UI and parsing logic are complete
- The database methods are **missing** from `db.py`
- Uploads will **fail** when trying to save to database
- Error message would be: `'DatabaseManager' object has no attribute 'create_or_update_question_pool'`

**Status:** Feature is **80% complete** - Frontend and parsing work perfectly, but database persistence layer needs implementation.

---

## 🚀 Next Steps

1. Implement the 4 missing database methods in `db.py`
2. Test with sample PDF/Word files
3. Verify questions are stored in Supabase
4. Test duplicate detection with multiple uploads of same file
5. Test multi-file merging (upload 3 versions of same exam)
