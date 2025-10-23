# 🎛️ Feature Toggles - MockExamify

## Hidden Features (For Future Release)

This document tracks features that are implemented but temporarily hidden from users.

---

## 📊 Answer Confidence Tracking

**Status:** 🔴 Hidden (Planned for future release)
**File:** `app_pages/exam.py` (lines 414-424)
**Feature:** Allows students to rate their confidence (0-100%) when answering questions

### Description
This feature adds an optional confidence slider below each question, asking students:
> "💡 Answer Confidence (Optional)
> How confident are you in this answer?"

**Purpose:**
- Track student confidence alongside correctness
- Identify knowledge gaps (low confidence + correct answers)
- Detect overconfidence (high confidence + incorrect answers)
- Provide insights for adaptive learning

### Why Hidden?
- Simplify initial user experience
- Focus on core exam functionality first
- Will enable when analytics features are expanded

### How to Enable

**Step 1:** Open `app_pages/exam.py`

**Step 2:** Find lines 414-424 and uncomment:

```python
# FEATURE HIDDEN: Answer confidence tracking
# Hiding for future release - uncomment to enable
with st.expander("💡 Answer Confidence (Optional)", expanded=False):
    confidence = st.slider(
        "How confident are you in this answer?",
        0,
        100,
        50,
        help="This helps us understand your learning progress",
        key=f"confidence_{question_index}",
    )
```

**Step 3:** Restart the app

**Step 4:** Test with a practice exam

### Backend Support

**Database:**
- ✅ `attempts` table supports storing confidence data
- ✅ Field: `confidence_level` (integer 0-100)
- ⚠️ Currently not being saved (frontend disabled)

**Analytics:**
- ⚠️ Analytics dashboard has confidence visualization code
- ⚠️ Will need testing when feature is re-enabled

### Future Enhancements

When re-enabling this feature, consider:

1. **Make it optional per exam**
   - Let instructors toggle confidence tracking on/off per mock exam
   - Add setting in exam creation: "Track student confidence?"

2. **Enhanced analytics**
   - Confidence vs. correctness correlation
   - Overconfidence/underconfidence reports
   - Trend analysis over time

3. **Adaptive learning**
   - Flag questions where students are consistently overconfident
   - Suggest review for low-confidence correct answers
   - Adjust difficulty based on confidence patterns

### Last Modified
- **Date:** 2025-10-23
- **Action:** Hidden from student exam interface
- **Reason:** Simplify UX for initial release

---

## 📋 Feature Roadmap

| Feature | Status | Priority | Target Release |
|---------|--------|----------|----------------|
| Answer Confidence Tracking | 🔴 Hidden | Medium | v1.1 |
| Explanations for Answers | ✅ Active | High | v1.0 |
| Question Flagging | ✅ Active | High | v1.0 |
| Time Tracking per Question | ⚠️ Partial | Low | v1.2 |
| Hint System | ⚠️ Not Started | Medium | v1.2 |

---

## 🔧 Developer Notes

### Adding New Hidden Features

When hiding a feature for future release:

1. **Comment out the UI code** with clear markers:
   ```python
   # FEATURE HIDDEN: [Feature Name]
   # Hiding for [reason] - uncomment to enable
   # [commented code here]
   ```

2. **Document in this file** with:
   - Location (file and line numbers)
   - Purpose and description
   - Why it's hidden
   - How to re-enable
   - Backend support status

3. **Test that app works without it**
   - Ensure no broken dependencies
   - Verify no errors in console
   - Check that feature gracefully handles missing data

4. **Update commit message** mentioning hidden feature

### Re-enabling Features

Before re-enabling:
1. Review this documentation
2. Test in development environment
3. Check database schema compatibility
4. Update analytics if applicable
5. Add to release notes
6. Update user documentation

---

**Last Updated:** 2025-10-23
