#!/usr/bin/env python3
"""
Quick script to check if a file was successfully uploaded
"""
import sys
from db import db

if len(sys.argv) < 2:
    print("Usage: python check_upload_status.py <filename>")
    print("Example: python check_upload_status.py 'Module 6A Questions Part 3.pdf'")
    sys.exit(1)

filename = sys.argv[1]

# Check for questions from this file
result = db.admin_client.table('pool_questions').select('id, pool_id, source_file, uploaded_at').eq('source_file', filename).execute()

if result.data:
    print(f"✅ SUCCESS: Found {len(result.data)} questions from '{filename}'")
    print(f"\nUploaded at: {result.data[0]['uploaded_at']}")

    # Get pool name
    pool_result = db.admin_client.table('question_pools').select('pool_name').eq('id', result.data[0]['pool_id']).execute()
    if pool_result.data:
        print(f"Pool: {pool_result.data[0]['pool_name']}")
else:
    print(f"❌ FAILED: No questions found from '{filename}'")
    print("\nThis file was not successfully uploaded. Try uploading again.")
