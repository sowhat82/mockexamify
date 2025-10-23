#!/usr/bin/env python3
"""
Check upload batch information for CACS Paper 2
to understand what went wrong during upload
"""

import asyncio
from typing import Dict, List, Any


async def check_upload_info():
    """Check upload batch details"""
    print("🔍 Checking Upload Batch Information")
    print("=" * 70)
    print()

    from db import db

    # Get the CACS Paper 2 pool
    pools = await db.get_all_question_pools()
    cacs_pool = next((p for p in pools if "CACS" in p['pool_name']), None)

    if not cacs_pool:
        print("❌ CACS Paper 2 pool not found")
        return

    pool_id = cacs_pool['id']
    print(f"📚 Pool: {cacs_pool['pool_name']}")
    print(f"   ID: {pool_id}")
    print(f"   Created: {cacs_pool.get('created_at', 'Unknown')}")
    print(f"   Total Questions: {cacs_pool.get('total_questions', 0)}")
    print(f"   Unique Questions: {cacs_pool.get('unique_questions', 0)}")
    print()

    # Check if there's upload_batches table
    try:
        result = db.admin_client.table("upload_batches").select("*").eq("pool_id", pool_id).execute()

        if result.data:
            print(f"📦 Found {len(result.data)} upload batch(es):")
            for batch in result.data:
                print(f"\n   Batch ID: {batch.get('id')}")
                print(f"   Uploaded: {batch.get('uploaded_at', 'Unknown')}")
                print(f"   Source File: {batch.get('source_file', 'Unknown')}")
                print(f"   Questions Count: {batch.get('questions_count', 0)}")
                print(f"   Status: {batch.get('status', 'Unknown')}")
                if batch.get('error_log'):
                    print(f"   ⚠️  Errors: {batch.get('error_log')}")
        else:
            print("   ℹ️  No upload batch records found")
    except Exception as e:
        print(f"   ℹ️  Could not access upload_batches table: {e}")

    print()
    print("=" * 70)
    print()
    print("💡 Analysis:")
    print("   - The corruption pattern (Q50-85) suggests chunked processing")
    print("   - The AI likely encountered issues with the second chunk")
    print("   - Possible causes:")
    print("     • OCR errors in that section of the document")
    print("     • API timeout or rate limit")
    print("     • Chunk boundary split questions incorrectly")
    print("     • AI returned placeholder data due to parsing failure")
    print()
    print("🔧 Recommended Solutions:")
    print("   1. Re-upload the original document (best option)")
    print("   2. Manually edit the 36 corrupted questions in admin dashboard")
    print("   3. Use a fix script to batch-update questions (if source available)")
    print()


if __name__ == "__main__":
    asyncio.run(check_upload_info())
