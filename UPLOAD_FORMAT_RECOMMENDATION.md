# WantAMock/MockExamify Database Schema Analysis & Upload Format Recommendation

## Executive Summary

**Classification:** **Hybrid Model (C + Embedded Context)**
- Primarily **fully standalone questions** with optional embedded scenarios
- Questions contain self-sufficient context via the `scenario` field
- No separate context block table or context_id grouping

**Recommended Upload Format:** **Structured JSON with Context Embedding**

---

## 1. COMPLETE DATABASE SCHEMA

### 1.1 Core Tables for Exam Questions

#### Table: `pool_questions`
**Purpose:** Individual questions within question pools (normalized storage)

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | gen_random_uuid() | Primary key |
| `pool_id` | UUID | NO | - | FK to question_pools(id), ON DELETE CASCADE |
| `question_text` | TEXT | NO | - | The question text |
| `choices` | JSONB | NO | - | Array of answer choices (stringified JSON) |
| `correct_answer` | INTEGER | NO | - | Index of correct answer (0-based) |
| `explanation` | TEXT | YES | NULL | AI-generated explanation |
| `difficulty` | VARCHAR(50) | YES | 'medium' | Difficulty level |
| `topic_tags` | JSONB | YES | '[]'::jsonb | Array of topic tags |
| **`source_file`** | VARCHAR(255) | YES | NULL | Original filename for tracking |
| `upload_batch_id` | UUID | YES | NULL | Groups questions from same upload |
| `uploaded_at` | TIMESTAMPTZ | NO | NOW() | Upload timestamp |
| **`is_duplicate`** | BOOLEAN | YES | FALSE | Duplicate detection flag |
| `duplicate_of` | UUID | YES | NULL | FK to pool_questions(id) if duplicate |
| `similarity_score` | DECIMAL(5,2) | YES | NULL | AI similarity score (0-100) |
| `times_shown` | INTEGER | YES | 0 | Usage statistics |
| `times_correct` | INTEGER | YES | 0 | Usage statistics |
| `times_incorrect` | INTEGER | YES | 0 | Usage statistics |
| `created_at` | TIMESTAMPTZ | NO | NOW() | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NO | NOW() | Last update timestamp |

**Indexes:**
- `idx_pool_questions_pool_id` ON pool_id
- `idx_pool_questions_batch` ON upload_batch_id
- `idx_pool_questions_duplicate` ON is_duplicate
- `idx_pool_questions_source` ON source_file

**Constraints:**
- CASCADE DELETE when parent pool is deleted
- RLS enabled (see section 5)

---

#### Table: `question_pools`
**Purpose:** Master table for question pools (e.g., "CACS2 Paper 2")

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | gen_random_uuid() | Primary key |
| `pool_name` | VARCHAR(255) | NO | - | Unique pool identifier |
| `description` | TEXT | YES | NULL | Pool description |
| `category` | VARCHAR(100) | YES | NULL | Category classification |
| `total_questions` | INTEGER | YES | 0 | Auto-updated count |
| `unique_questions` | INTEGER | YES | 0 | Auto-updated (non-duplicates) |
| `last_updated` | TIMESTAMPTZ | YES | NOW() | Last modification |
| `created_at` | TIMESTAMPTZ | YES | NOW() | Creation timestamp |
| `created_by` | UUID | YES | NULL | FK to users(id) |
| `is_active` | BOOLEAN | YES | TRUE | Active/inactive flag |

**Indexes:**
- `idx_question_pools_name` ON pool_name
- `idx_question_pools_category` ON category
- `idx_question_pools_active` ON is_active

**Constraints:**
- UNIQUE constraint on `pool_name`
- RLS enabled

**Triggers:**
- Auto-update pool statistics when pool_questions changes

---

#### Table: `upload_batches`
**Purpose:** Track each file upload batch for audit trail

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | gen_random_uuid() | Primary key |
| `pool_id` | UUID | NO | - | FK to question_pools(id) CASCADE |
| `filename` | VARCHAR(255) | NO | - | Original filename |
| `questions_count` | INTEGER | YES | 0 | Total questions in upload |
| `duplicates_found` | INTEGER | YES | 0 | Number of duplicates detected |
| `unique_added` | INTEGER | YES | 0 | New questions added |
| `upload_status` | VARCHAR(50) | YES | 'processing' | processing/completed/failed |
| `error_message` | TEXT | YES | NULL | Error details if failed |
| `uploaded_by` | UUID | YES | NULL | FK to users(id) |
| `uploaded_at` | TIMESTAMPTZ | YES | NOW() | Upload timestamp |

**Indexes:**
- `idx_upload_batches_pool` ON pool_id
- `idx_upload_batches_status` ON upload_status

---

#### Table: `mocks`
**Purpose:** Mock exam templates (legacy structure, questions stored as JSONB)

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | gen_random_uuid() | Primary key |
| `title` | VARCHAR(255) | NO | - | Mock exam title |
| `description` | TEXT | NO | - | Description |
| **`questions_json`** | JSONB | NO | - | Entire question array in JSON |
| `price_credits` | INTEGER | YES | 1 | Cost to take exam |
| `explanation_enabled` | BOOLEAN | YES | TRUE | Enable AI explanations |
| `time_limit_minutes` | INTEGER | YES | 60 | Time limit |
| `category` | VARCHAR(100) | YES | 'General' | Category |
| `difficulty` | VARCHAR(20) | YES | 'medium' | Difficulty |
| `is_active` | BOOLEAN | YES | TRUE | Active flag |
| `creator_id` | UUID | YES | NULL | FK to users(id) |
| `created_at` | TIMESTAMPTZ | NO | NOW() | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NO | NOW() | Update timestamp |

**Note:** The `questions_json` field stores the entire question array as JSONB, including scenarios embedded in each question object.

---

#### Table: `duplicate_cache`
**Purpose:** Cache AI duplicate detection results (expensive operations)

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | UUID | NO | gen_random_uuid() | Primary key |
| `question1_id` | UUID | NO | - | FK to pool_questions(id) CASCADE |
| `question2_id` | UUID | NO | - | FK to pool_questions(id) CASCADE |
| `similarity_score` | DECIMAL(5,2) | NO | - | AI similarity (0-100) |
| `is_duplicate` | BOOLEAN | NO | - | Duplicate flag |
| `ai_reasoning` | TEXT | YES | NULL | AI's explanation |
| `checked_at` | TIMESTAMPTZ | YES | NOW() | Check timestamp |

**Constraints:**
- UNIQUE(question1_id, question2_id)

**Indexes:**
- `idx_duplicate_cache_q1` ON question1_id
- `idx_duplicate_cache_q2` ON question2_id

---

## 2. SQL MIGRATIONS SUMMARY

### Applied Migrations:

1. **`database_schema_question_pools.sql`**
   - Created question pool system
   - Added duplicate detection infrastructure
   - Created upload batch tracking
   - Added triggers for auto-updating pool statistics

2. **`enable_rls_question_pools.sql`**
   - Enabled RLS on all question pool tables
   - Created admin-only policies for CRUD operations
   - Public read access to active pools for authenticated users

3. **`add_support_ticket_fields.sql`**
   - Enhanced support ticket tracking (not directly related to questions)

4. **`fix_pool_questions_mobile.sql` / `fix_admin_pool_questions_access.sql`**
   - Fixed RLS policies for admin access
   - Ensured service role can bypass RLS

5. **`add_attempt_pro_rata_fields.sql`**
   - Added pro-rata credit calculation for attempts

---

## 3. ROW LEVEL SECURITY (RLS) POLICIES

### `question_pools` Table Policies:

| Policy | Operation | Role | Condition |
|--------|-----------|------|-----------|
| `question_pools_read_active` | SELECT | anon, authenticated | is_active = TRUE |
| `question_pools_admin_insert` | INSERT | authenticated | user.role = 'admin' |
| `question_pools_admin_update` | UPDATE | authenticated | user.role = 'admin' |
| `question_pools_admin_delete` | DELETE | authenticated | user.role = 'admin' |

### `pool_questions` Table Policies:

| Policy | Operation | Role | Condition |
|--------|-----------|------|-----------|
| `pool_questions_read` | SELECT | authenticated | pool.is_active = TRUE |
| `pool_questions_admin_insert` | INSERT | authenticated | user.role = 'admin' |
| `pool_questions_admin_update` | UPDATE | authenticated | user.role = 'admin' |
| `pool_questions_admin_delete` | DELETE | authenticated | user.role = 'admin' |

**Service Role Override:** Admin client uses service role key to bypass RLS for admin operations.

---

## 4. ACTUAL DATA STRUCTURE ANALYSIS

### Sample `pool_questions` Record:

```json
{
  "id": "fab6da54-fdb5-4992-a3a3-324ab12d8ab3",
  "pool_id": "8a032a2a-9d71-476b-81d3-7980fac9ec8e",
  "question_text": "The portfolio's upfront loading fee is:",
  "choices": "[\"The fee deducted upfront...\", \"The fee deducted when...\", ...]",
  "correct_answer": 2,
  "explanation": "Let's break down the correct answer...",
  "difficulty": "medium",
  "topic_tags": null,
  "source_file": "CACS2_Mock_Paper1_QA_Explanations.docx",
  "upload_batch_id": "57b496e3-1c2e-491f-9a24-d5224d166900",
  "uploaded_at": "2025-10-17T15:57:10.19672+00:00",
  "is_duplicate": false,
  "duplicate_of": null,
  "similarity_score": null,
  "times_shown": 0,
  "times_correct": 0,
  "times_incorrect": 0,
  "created_at": "2025-10-17T15:57:10.196723+00:00",
  "updated_at": "2025-10-17T15:57:10.116239+00:00"
}
```

**Key Observations:**
- `choices` is stored as **stringified JSON array**
- `topic_tags` can be null
- No separate `scenario` field in pool_questions table (context embedded in question_text)

---

## 5. HOW THE SYSTEM HANDLES DIFFERENT QUESTION TYPES

### Case Study / Term Sheet Questions

**Current Implementation:** Embedded in `question_text` or AI extraction with `scenario` field

#### From `document_parser.py` AI Prompt:

The system instructs AI to:
1. **Extract term sheets/case studies** as contextual blocks
2. **Attach context to related questions** via `scenario` field
3. Questions like "What is the return of this HSI RAN?" are **valid** if they include the term sheet in their scenario

#### Example AI Output Format:

```json
[
  {
    "question": "What is the maximum return of this product?",
    "choices": ["5%", "10%", "15%", "20%"],
    "correct_index": 2,
    "scenario": "ABC Range Accrual Note: Principal $100,000, Tenor: 2 years, Reference Index: HSI, Coupon: 7.5% p.a. if HSI stays within range, Maximum Return: 15% p.a.",
    "explanation_seed": "Term sheet specifies maximum return"
  },
  {
    "question": "If the HSI breaches the barrier, what happens?",
    "choices": ["Full principal loss", "Partial principal loss", "No coupon payment", "Early redemption"],
    "correct_index": 2,
    "scenario": "ABC Range Accrual Note: Principal $100,000, Tenor: 2 years, Reference Index: HSI, Coupon: 7.5% p.a. if HSI stays within range, Maximum Return: 15% p.a.",
    "explanation_seed": "Barrier breach affects coupon"
  }
]
```

**Storage in Database:**
- The `scenario` field content is either:
  - Embedded into `question_text` during upload, OR
  - Stored separately in mocks `questions_json` structure

**Note:** The `pool_questions` table does NOT have a dedicated `scenario` column in the current schema, but the upload process can embed scenario context into `question_text`.

---

### Image-Based Questions

**Current Status:** **NOT SUPPORTED** in current schema

- No `image_url` or `image_data` field in `pool_questions`
- Would require schema migration to add image support
- Potential columns:
  - `image_url` TEXT (for external hosting)
  - `image_data` BYTEA or JSONB (for base64 or metadata)
  - `has_image` BOOLEAN flag

---

### Multi-Part Question Flows

**Current Status:** **NOT EXPLICITLY SUPPORTED** but can be simulated

- No `parent_question_id` or `question_group_id` field
- No explicit ordering mechanism beyond database insertion order
- Can be simulated by:
  - Using `topic_tags` to group related questions
  - Embedding context in `scenario` field
  - Relying on `uploaded_at` timestamp for ordering

---

## 6. SYSTEM CLASSIFICATION

**Type: D) Hybrid or Custom Model**

Specifically: **Hybrid - Standalone with Optional Embedded Context**

### Characteristics:

1. ✅ **Fully Standalone Questions**
   - Each question in `pool_questions` is self-contained
   - `question_text` + `choices` + `correct_answer` = complete question

2. ✅ **Optional Context Embedding**
   - AI extraction adds `scenario` field to questions that reference context
   - Scenario is **duplicated** across multiple questions (not normalized)
   - No separate context block table

3. ❌ **No Context Block + Child Questions**
   - No separate `case_studies` or `context_blocks` table
   - No FK linking questions to shared contexts

4. ❌ **No context_id Grouping**
   - No `context_id` field in questions table
   - Context is embedded, not referenced

### Rationale:

The system treats **context as question metadata** rather than a first-class entity. This approach:
- ✅ Simplifies querying (one table lookup)
- ✅ Avoids JOIN complexity
- ✅ Works well for duplicate detection (full context comparison)
- ❌ Results in data duplication (same scenario stored N times)
- ❌ Harder to update shared contexts

---

## 7. CURRENT UPLOAD WORKFLOW

### Supported Formats:

1. **CSV** - Structured tabular format
2. **JSON** - Structured JSON array
3. **PDF** - OCR + AI extraction
4. **DOCX/DOC** - Text extraction + AI parsing

### CSV Upload Structure:

```csv
question,choice_1,choice_2,choice_3,choice_4,correct_index,scenario,explanation_seed
"What is 2+2?","3","4","5","6",1,"Basic math","Addition"
```

### JSON Upload Structure:

```json
[
  {
    "question": "What is the output of print(2 + 2)?",
    "choices": ["3", "4", "5", "6"],
    "correct_index": 1,
    "scenario": "Basic arithmetic in Python",
    "explanation_seed": "Addition operator"
  }
]
```

### PDF/DOCX AI Extraction:

- Text extracted via PyPDF2 or python-docx
- AI called with extraction prompt (see section 5)
- Returns JSON array with same structure as above
- AI automatically:
  - Detects term sheets/case studies
  - Attaches scenarios to related questions
  - Fixes OCR errors
  - Validates finance domain (rejects trivia/programming)

---

## 8. RECOMMENDED UPLOAD FORMAT

### 🏆 **Primary Recommendation: Structured JSON with Context Embedding**

**Why JSON?**
1. ✅ **Native JSONB Storage** - Supabase stores `choices` and `topic_tags` as JSONB
2. ✅ **Context Flexibility** - Can embed complex scenarios without escaping issues
3. ✅ **Validation** - JSON schemas can validate structure before upload
4. ✅ **AI-Friendly** - Current AI extraction already outputs JSON
5. ✅ **No Parsing Ambiguity** - Unlike CSV with commas/quotes in text
6. ✅ **Extensibility** - Easy to add new fields (tags, difficulty, etc.)
7. ✅ **Image Support Ready** - Can add image fields when schema updated

---

### 📋 **Recommended JSON Schema**

```json
{
  "pool_name": "CMFAS CM-SIP",
  "category": "Finance & Accounting",
  "description": "Module 6A Questions",
  "questions": [
    {
      "question": "What is the maximum return of this HSI Range Accrual Note?",
      "choices": [
        "5% per annum",
        "10% per annum",
        "15% per annum",
        "20% per annum"
      ],
      "correct_index": 2,
      "scenario": "HSI Range Accrual Note Details:\n- Principal: $100,000\n- Tenor: 2 years\n- Reference Index: HSI\n- Coupon: 7.5% p.a. if HSI stays within range (18,000 - 22,000)\n- Barrier: None\n- Maximum Return: 15% p.a.",
      "explanation_seed": "Term sheet specifies 15% maximum return",
      "difficulty": "medium",
      "topic_tags": ["structured products", "range accrual", "HSI"],
      "source_reference": "Module 6A Part 3, Page 12"
    },
    {
      "question": "If the HSI closes at 23,000 on any observation date, what happens to the coupon?",
      "choices": [
        "Full coupon paid",
        "No coupon for that day",
        "Reduced coupon paid",
        "Principal is at risk"
      ],
      "correct_index": 1,
      "scenario": "HSI Range Accrual Note Details:\n- Principal: $100,000\n- Tenor: 2 years\n- Reference Index: HSI\n- Coupon: 7.5% p.a. if HSI stays within range (18,000 - 22,000)\n- Barrier: None\n- Maximum Return: 15% p.a.",
      "explanation_seed": "HSI outside range = no coupon for that day",
      "difficulty": "medium",
      "topic_tags": ["structured products", "range accrual", "coupon"],
      "source_reference": "Module 6A Part 3, Page 12"
    }
  ]
}
```

---

### 🎯 **Field Specifications**

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `pool_name` | string | YES | Target pool identifier | "CMFAS CM-SIP" |
| `category` | string | NO | Pool category | "Finance & Accounting" |
| `description` | string | NO | Pool description | "Module 6A Questions" |
| `questions` | array | YES | Array of question objects | See below |

#### Question Object Fields:

| Field | Type | Required | Database Column | Notes |
|-------|------|----------|-----------------|-------|
| `question` | string | YES | `question_text` | The question text |
| `choices` | array[string] | YES | `choices` (JSONB) | 2-6 answer options |
| `correct_index` | integer | YES | `correct_answer` | 0-based index (0-5) |
| `scenario` | string | NO | Embedded in `question_text` | Context/case study |
| `explanation_seed` | string | NO | Not stored in pool_questions | Hint for AI explanation generation |
| `difficulty` | string | NO | `difficulty` | "easy", "medium", "hard" |
| `topic_tags` | array[string] | NO | `topic_tags` (JSONB) | Categorization tags |
| `source_reference` | string | NO | `source_file` metadata | Page/section reference |

---

### 📦 **Alternative Format: Enhanced CSV**

**When to Use:** Bulk uploads without complex scenarios

**Structure:**

```csv
question,choice_1,choice_2,choice_3,choice_4,correct_index,scenario,difficulty,topic_tags,source_reference
"What is 2+2?","3","4","5","6",1,"","easy","['basic math','arithmetic']","Page 1"
"Calculate Sharpe ratio: Return=12%, Risk-free=2%, StdDev=8%","1.00","1.25","1.50","1.75",1,"Portfolio metrics: Return 12%, StdDev 8%, Risk-free 2%","medium","['risk metrics','sharpe ratio']","Page 15"
```

**Limitations:**
- ❌ Difficult to embed multi-line scenarios
- ❌ Comma/quote escaping issues
- ❌ Array fields need JSON string encoding
- ✅ Familiar for non-technical users
- ✅ Easy Excel export

---

### 🎨 **Future-Proof Format: Extended JSON with Images**

**For when image support is added:**

```json
{
  "pool_name": "CACS2 Paper 2",
  "questions": [
    {
      "question": "What type of chart is shown?",
      "choices": ["Bar chart", "Candlestick chart", "Line chart", "Histogram"],
      "correct_index": 1,
      "image": {
        "type": "base64",
        "data": "data:image/png;base64,iVBORw0KGgoAAAANS...",
        "alt_text": "Candlestick chart showing HSBC stock performance"
      },
      "correct_index": 1
    }
  ]
}
```

---

## 9. IMPLEMENTATION GUIDE FOR AI AGENTS

### Step 1: Validate Input Format

```python
import json
from typing import Dict, List

def validate_upload_json(data: Dict) -> tuple[bool, str]:
    """Validate JSON upload format"""
    if "pool_name" not in data:
        return False, "Missing required field: pool_name"

    if "questions" not in data or not isinstance(data["questions"], list):
        return False, "Missing or invalid questions array"

    for i, q in enumerate(data["questions"]):
        # Required fields
        if "question" not in q:
            return False, f"Question {i}: Missing 'question' field"
        if "choices" not in q or len(q["choices"]) < 2:
            return False, f"Question {i}: Need at least 2 choices"
        if "correct_index" not in q:
            return False, f"Question {i}: Missing 'correct_index'"

        # Validate correct_index
        if not (0 <= q["correct_index"] < len(q["choices"])):
            return False, f"Question {i}: Invalid correct_index"

    return True, "Valid"
```

### Step 2: Transform to Database Format

```python
def transform_to_db_format(upload_data: Dict) -> Dict:
    """Transform upload JSON to database insertion format"""

    pool_data = {
        "pool_name": upload_data["pool_name"],
        "category": upload_data.get("category"),
        "description": upload_data.get("description"),
    }

    questions_data = []
    for q in upload_data["questions"]:
        # Embed scenario into question_text if provided
        question_text = q["question"]
        if q.get("scenario"):
            question_text = f"CONTEXT: {q['scenario']}\n\nQUESTION: {question_text}"

        questions_data.append({
            "question_text": question_text,
            "choices": json.dumps(q["choices"]),  # Stringify for JSONB
            "correct_answer": q["correct_index"],
            "difficulty": q.get("difficulty", "medium"),
            "topic_tags": q.get("topic_tags", []),
            "source_file": upload_data.get("source_file", "api_upload.json"),
        })

    return {
        "pool": pool_data,
        "questions": questions_data
    }
```

### Step 3: Upload to Supabase

```python
async def upload_to_supabase(pool_data: Dict, questions_data: List[Dict]):
    """Upload to Supabase with proper error handling"""

    # Step 1: Get or create pool
    pool_response = await db.admin_client.table('question_pools')\
        .select('*')\
        .eq('pool_name', pool_data['pool_name'])\
        .execute()

    if pool_response.data:
        pool_id = pool_response.data[0]['id']
    else:
        # Create new pool
        create_response = await db.admin_client.table('question_pools')\
            .insert(pool_data)\
            .execute()
        pool_id = create_response.data[0]['id']

    # Step 2: Create upload batch
    batch_response = await db.admin_client.table('upload_batches')\
        .insert({
            'pool_id': pool_id,
            'filename': pool_data.get('source_file', 'api_upload.json'),
            'questions_count': len(questions_data),
            'upload_status': 'processing'
        })\
        .execute()

    batch_id = batch_response.data[0]['id']

    # Step 3: Add batch_id and pool_id to questions
    for q in questions_data:
        q['pool_id'] = pool_id
        q['upload_batch_id'] = batch_id

    # Step 4: Bulk insert questions
    insert_response = await db.admin_client.table('pool_questions')\
        .insert(questions_data)\
        .execute()

    # Step 5: Update batch status
    await db.admin_client.table('upload_batches')\
        .update({
            'upload_status': 'completed',
            'unique_added': len(insert_response.data)
        })\
        .eq('id', batch_id)\
        .execute()

    return pool_id, batch_id
```

---

## 10. COMPLETE EXAMPLE: UPLOAD FILE

### File: `cmfas_module6a_upload.json`

```json
{
  "pool_name": "CMFAS CM-SIP",
  "category": "Finance & Accounting",
  "description": "Module 6A - Structured Investment Products",
  "source_file": "Module 6A Questions Part 3.pdf",
  "questions": [
    {
      "question": "What is the principal protection level of this equity-linked note?",
      "choices": [
        "100% principal protection at maturity",
        "90% principal protection at maturity",
        "No principal protection",
        "Principal protection only if barrier not breached"
      ],
      "correct_index": 0,
      "scenario": "ABC Equity-Linked Note:\n- Issuer: ABC Bank\n- Principal: USD 100,000\n- Tenor: 3 years\n- Reference Asset: HSBC Holdings Limited ordinary shares\n- Principal Protection: 100% at maturity\n- Participation Rate: 100%\n- Barrier: 60% of initial stock price\n- Initial Stock Price: HKD 65.00",
      "explanation_seed": "Term sheet explicitly states 100% principal protection at maturity",
      "difficulty": "easy",
      "topic_tags": ["equity-linked notes", "principal protection", "structured products"],
      "source_reference": "Page 12, Question 1"
    },
    {
      "question": "If HSBC's stock price falls to HKD 38.00 (58% of initial price) during the investment period, what happens at maturity?",
      "choices": [
        "Investor receives 100% principal back",
        "Investor receives physical delivery of HSBC shares",
        "Investor loses 42% of principal",
        "Note is automatically called early"
      ],
      "correct_index": 1,
      "scenario": "ABC Equity-Linked Note:\n- Issuer: ABC Bank\n- Principal: USD 100,000\n- Tenor: 3 years\n- Reference Asset: HSBC Holdings Limited ordinary shares\n- Principal Protection: 100% at maturity\n- Participation Rate: 100%\n- Barrier: 60% of initial stock price\n- Initial Stock Price: HKD 65.00\n\nAdditional Terms:\n- If stock price breaches 60% barrier at any time during tenor, principal protection is lost\n- Settlement at maturity: Physical delivery of shares if barrier breached, otherwise cash settlement",
      "explanation_seed": "Barrier breached (58% < 60%), triggers physical delivery instead of cash",
      "difficulty": "medium",
      "topic_tags": ["equity-linked notes", "barrier breach", "physical settlement"],
      "source_reference": "Page 12, Question 2"
    },
    {
      "question": "What is the upfront loading fee typically used for?",
      "choices": [
        "To pay for third-party administrative services",
        "To compensate the issuer for structuring the product",
        "To cover initial setup costs of the portfolio",
        "To pay professionals for ongoing portfolio management"
      ],
      "correct_index": 2,
      "scenario": null,
      "explanation_seed": "Loading fees are one-time charges for initial setup",
      "difficulty": "easy",
      "topic_tags": ["fees", "loading fee", "portfolio management"],
      "source_reference": "Page 15, Question 8"
    },
    {
      "question": "Calculate the Sharpe ratio for a portfolio with 12% annual return, 8% standard deviation, and 2% risk-free rate.",
      "choices": [
        "1.00",
        "1.25",
        "1.50",
        "1.75"
      ],
      "correct_index": 1,
      "scenario": "Portfolio Metrics:\n- Annual Return: 12%\n- Standard Deviation: 8%\n- Risk-Free Rate: 2%\n\nSharpe Ratio Formula: (Portfolio Return - Risk-Free Rate) / Standard Deviation",
      "explanation_seed": "Sharpe = (12% - 2%) / 8% = 10% / 8% = 1.25",
      "difficulty": "medium",
      "topic_tags": ["risk metrics", "sharpe ratio", "calculations"],
      "source_reference": "Page 18, Question 12"
    }
  ]
}
```

---

## 11. MIGRATION PATH FOR FUTURE ENHANCEMENTS

### Adding Image Support

```sql
-- Add image columns to pool_questions
ALTER TABLE pool_questions
ADD COLUMN image_url TEXT,
ADD COLUMN image_alt_text TEXT,
ADD COLUMN has_image BOOLEAN DEFAULT FALSE;

-- Create index for image queries
CREATE INDEX idx_pool_questions_has_image ON pool_questions(has_image) WHERE has_image = TRUE;
```

### Adding Shared Context Blocks (if needed)

```sql
-- Create context blocks table
CREATE TABLE context_blocks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    pool_id UUID REFERENCES question_pools(id) ON DELETE CASCADE,
    context_text TEXT NOT NULL,
    context_type VARCHAR(50), -- 'case_study', 'term_sheet', 'scenario'
    source_reference TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add context reference to pool_questions
ALTER TABLE pool_questions
ADD COLUMN context_id UUID REFERENCES context_blocks(id) ON DELETE SET NULL;

-- Create index
CREATE INDEX idx_pool_questions_context ON pool_questions(context_id);
```

---

## 12. SUMMARY & FINAL RECOMMENDATIONS

### ✅ **Primary Recommendation: Structured JSON Upload**

**Format:** JSON file with embedded scenarios (see section 10 for complete example)

**Advantages:**
1. ✅ Direct compatibility with current database structure
2. ✅ Supports complex scenarios without escaping issues
3. ✅ AI-friendly (matches current AI extraction output)
4. ✅ Extensible for future features (images, multi-part)
5. ✅ Validates easily with JSON schemas
6. ✅ No data loss from CSV limitations

**For Agents Generating Upload Files:**

```python
# Template for generating upload-ready JSON
def generate_upload_json(pool_name: str, questions: List[Dict]) -> Dict:
    return {
        "pool_name": pool_name,
        "category": "Finance & Accounting",  # Customize
        "description": f"{pool_name} Question Bank",
        "source_file": "generated_upload.json",
        "questions": [
            {
                "question": q["question"],
                "choices": q["choices"],  # Array of strings
                "correct_index": q["correct_index"],  # 0-based integer
                "scenario": q.get("scenario"),  # Optional string
                "explanation_seed": q.get("explanation_seed"),
                "difficulty": q.get("difficulty", "medium"),
                "topic_tags": q.get("topic_tags", []),
                "source_reference": q.get("source_reference")
            }
            for q in questions
        ]
    }
```

### 📋 **When to Use Alternative Formats:**

- **CSV:** Simple question banks without scenarios, non-technical users
- **PDF/DOCX:** When source documents already exist (will be AI-extracted to JSON internally)
- **Custom Schema:** Only if adding new features (images, multi-part) - propose schema first

### 🎯 **Next Steps for Implementation:**

1. **Generate JSON files** using the recommended schema
2. **Validate** using provided validation function
3. **Upload** via Supabase API using admin client
4. **Verify** questions appear in target pool
5. **Test** duplicate detection if uploading to existing pools

---

**End of Analysis**
