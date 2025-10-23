# Corrupted Questions Report - CACS Paper 2

## 🔍 Issue Summary

**Pool:** CACS Paper 2
**Upload Date:** October 17, 2025
**Total Questions:** 85
**Affected Questions:** Q50-Q85 (36 questions)
**Problem:** Answer choices showing as `["A", "B", "C", "D"]` instead of actual text

## 📊 Detailed Analysis

### What's Working
- ✅ **Questions 1-49:** All have correct, detailed answer choices
- ✅ **Question text:** All 85 questions have proper question text
- ✅ **Correct answer indices:** All questions have valid correct answer indices

### What's Corrupted
- ❌ **Questions 50-85:** Answer choices are placeholders `["A", "B", "C", "D"]`
- The actual answer text is missing from the database
- This affects 36 questions (42.4% of the pool)

### Examples of Corrupted Questions

**Q50:**
```
Question: "Even risk‑free securities must offer a small positive return above zero to compe..."
Choices: ["A", "B", "C", "D"]  ❌ Should be actual answer text
Correct Answer: 1
```

**Q85:**
```
Question: "As above, a bond issued by a blue‑chip company with semi‑annual coupons satisfie..."
Choices: ["A", "B", "C", "D"]  ❌ Should be actual answer text
Correct Answer: 0
```

## 🔍 Root Cause Analysis

### What Happened
The document parser processes large documents in chunks (~8000 characters each). During the upload:

1. **Chunk 1 (Q1-Q49):** ✅ Processed successfully
2. **Chunk 2+ (Q50-Q85):** ❌ Parser encountered issues
   - Possible OCR errors in that section
   - API timeout or rate limit hit
   - Chunk boundary split questions incorrectly
   - AI returned placeholder data when it couldn't parse properly

### Evidence
- Upload batch: `57b496e3-1c2e-491f-9a24-d5224d166900`
- All 85 questions uploaded in single batch
- Corruption pattern starts exactly at Q50
- No error logs recorded in the upload batch

## 🔧 Solution Options

### Option 1: Re-upload the Original Document (RECOMMENDED)

**Pros:**
- Cleanest solution
- Ensures all questions are extracted correctly
- Preserves original formatting and context

**Steps:**
1. Locate the original CACS Paper 2 document (PDF/DOCX)
2. Go to Admin Dashboard → Upload Questions
3. Select the existing "CACS Paper 2" pool
4. Upload the document again
5. System will detect duplicates and only update corrupted questions

**Note:** The deduplication system will keep Q1-Q49 unchanged and only update Q50-Q85.

---

### Option 2: Manual Editing via Admin Dashboard

**Pros:**
- No need for original file
- Precise control over each question

**Cons:**
- Time-consuming (36 questions to edit)
- Need to have the correct answer choices from source material

**Steps:**
1. Open original exam document/answer key
2. Go to Admin Dashboard → Question Pool Management
3. Click "View Questions" on CACS Paper 2
4. For each corrupted question (Q50-Q85):
   - Click "Edit"
   - Replace choices with actual answer text from source
   - Save

**Estimated time:** ~30-45 minutes for 36 questions

---

### Option 3: Batch Fix Script (If Source Data Available)

If you have the correct answer choices in a structured format (JSON, CSV, etc.), we can create a batch update script.

**Requirements:**
- Correct answer choices for Q50-Q85
- Format: Question number → Answer choices array

**Example input format:**
```json
{
  "50": ["Risk premium", "Inflation protection", "Time value", "Liquidity premium"],
  "51": ["Beta coefficient", "Standard deviation", "Alpha ratio", "Sharpe measure"],
  ...
}
```

---

## 📋 Affected Questions List

```
Q50, Q51, Q52, Q53, Q54, Q55, Q56, Q57, Q58, Q59,
Q60, Q61, Q62, Q63, Q64, Q65, Q66, Q67, Q68, Q69,
Q70, Q71, Q72, Q73, Q74, Q75, Q76, Q77, Q78, Q79,
Q80, Q81, Q82, Q83, Q84, Q85
```

## 🎯 Recommended Action

**Best approach:** Re-upload the original document

If you have the original CACS Paper 2 document:
1. Go to: http://localhost:8501
2. Navigate to Admin Dashboard → Upload Questions
3. Select existing pool: "CACS Paper 2"
4. Upload the document
5. System will intelligently update only the corrupted questions

This takes ~2-5 minutes and ensures accuracy.

## 📞 Need Help?

**If you need a batch fix script:**
- Provide the correct answer choices for Q50-Q85
- I can create a script to update them all at once

**If you want to manually edit:**
- Navigate to Question Pool Management
- Click "View Questions" → "Edit" for each Q50-Q85
- Replace `["A", "B", "C", "D"]` with actual text

**If you're re-uploading:**
- Just upload the document again to the same pool
- Deduplication will handle the rest

---

## 📁 Related Files

- **Investigation script:** `investigate_question_choices.py`
- **Upload batch checker:** `check_upload_batch.py`
- **Diagnostic tool:** `diagnose_pool_questions.py`

---

**Report Generated:** 2025-10-23
**Status:** Awaiting fix action
