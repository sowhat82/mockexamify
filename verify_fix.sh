#!/bin/bash

echo "=========================================="
echo "Verifying Bulk AI Fix Feature"
echo "=========================================="
echo ""

source venv/bin/activate

echo "1. Testing pattern detection on complaint question..."
echo "   (Should find 5 text/grammar error patterns)"
echo ""
python3 test_pattern_detection.py 2>&1 | grep -E "(Found|pattern|Type:|Description:)" | head -20

echo ""
echo "=========================================="
echo "2. Testing source file filtering..."
echo "   (Should show only same source questions checked)"
echo ""
python3 test_source_file_filtering.py 2>&1 | grep -E "(Expected Behavior|WILL BE CHECKED|Cost savings|SKIP)" | head -10

echo ""
echo "=========================================="
echo "3. Checking the actual complaint question..."
echo "   (Showing errors that will be fixed)"
echo ""
python3 find_complaint_question.py 2>&1 | grep -A 5 "ccd9e5eb" | head -15

echo ""
echo "=========================================="
echo "✅ VERIFICATION COMPLETE"
echo ""
echo "Next steps:"
echo "1. Start the app: streamlit run app.py"
echo "2. Go to Admin > Question Pools"
echo "3. View CACS Paper 1 questions"
echo "4. Select the complaint question"
echo "5. Click '🤖 AI Fix 1 Selected'"
echo "6. Watch it validate 61 questions from 'Khinloke 1 part 1.PDF'!"
echo "7. It will SKIP 131 questions from other source files"
echo "=========================================="
