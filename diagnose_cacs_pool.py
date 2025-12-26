#!/usr/bin/env python3
"""Diagnose CACS Paper 1 pool question availability"""

from db import DatabaseManager

def diagnose():
    db = DatabaseManager()

    # Get CACS Paper 1 pool
    pools_result = db.admin_client.table("question_pools").select("*").ilike("pool_name", "%CACS Paper 1%").execute()

    if not pools_result.data:
        print("❌ CACS Paper 1 pool not found!")
        return

    pool = pools_result.data[0]
    pool_id = pool['id']
    pool_name = pool['pool_name']

    print(f"✅ Found pool: {pool_name}")
    print(f"   Pool ID: {pool_id}")

    # Get all questions from pool
    all_questions = db.admin_client.table("pool_questions").select("id, is_duplicate").eq("pool_id", pool_id).execute()

    print(f"\n📊 Total questions in pool: {len(all_questions.data)}")

    # Count duplicates
    duplicates = [q for q in all_questions.data if q.get("is_duplicate") == True]
    non_duplicates = [q for q in all_questions.data if q.get("is_duplicate") == False]
    null_duplicates = [q for q in all_questions.data if q.get("is_duplicate") is None]

    print(f"   - Non-duplicates (is_duplicate=False): {len(non_duplicates)}")
    print(f"   - Duplicates (is_duplicate=True): {len(duplicates)}")
    print(f"   - NULL is_duplicate: {len(null_duplicates)}")

    # Try the actual query used by get_random_pool_questions
    test_query = db.admin_client.table("pool_questions").select("*").eq("pool_id", pool_id).eq("is_duplicate", False).execute()

    print(f"\n🔍 Questions returned by get_random_pool_questions query: {len(test_query.data)}")

    if len(test_query.data) == 0:
        print("\n⚠️  ISSUE FOUND: No questions with is_duplicate=False!")
        print("   This is why students see 'No questions available'")

        # Check if questions have NULL is_duplicate
        if len(null_duplicates) > 0:
            print(f"\n💡 Solution: {len(null_duplicates)} questions have NULL is_duplicate field")
            print("   Need to set is_duplicate=False for these questions")
    else:
        print(f"\n✅ Query working correctly - should return {len(test_query.data)} questions")

if __name__ == "__main__":
    diagnose()
