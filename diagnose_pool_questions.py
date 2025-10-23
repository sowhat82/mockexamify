#!/usr/bin/env python3
"""
Diagnostic script for pool questions display issue
Checks if questions exist and diagnoses RLS policy issues
"""

import os
import sys
import asyncio
from typing import Dict, List, Any


async def diagnose():
    """Run diagnostics on pool questions"""
    print("🔍 Diagnosing Pool Questions Display Issue")
    print("=" * 60)
    print()

    # Load environment
    from dotenv import load_dotenv
    load_dotenv()

    # Import database
    from db import db

    print("📊 Database Configuration:")
    print(f"   Demo Mode: {db.demo_mode}")
    print(f"   Client initialized: {db.client is not None}")
    print()

    # Check question pools
    print("📚 Checking Question Pools...")
    try:
        pools = await db.get_all_question_pools()
        print(f"   ✅ Found {len(pools)} question pool(s)")
        for pool in pools:
            print(f"      - {pool['pool_name']}: {pool.get('unique_questions', 0)} unique questions")
        print()
    except Exception as e:
        print(f"   ❌ Error loading pools: {e}")
        print()

    # Check pool questions
    if pools:
        print("🔍 Checking Questions in Each Pool...")
        for pool in pools:
            pool_id = pool['id']
            pool_name = pool['pool_name']

            try:
                questions = await db.get_pool_questions(pool_id)
                print(f"   Pool: {pool_name}")
                print(f"   ✅ Retrieved {len(questions)} question(s)")

                if len(questions) == 0:
                    print(f"   ⚠️  WARNING: No questions returned (but pool shows {pool.get('unique_questions', 0)} questions)")
                    print(f"   🔧 This indicates an RLS policy issue")
                    print()
            except Exception as e:
                print(f"   ❌ Error: {e}")
                print()
    else:
        print("   ℹ️  No pools to check")

    print()
    print("🔐 RLS Policy Diagnosis:")
    print("   The issue is likely caused by Row Level Security policies.")
    print("   The pool shows questions exist, but RLS prevents viewing them.")
    print()
    print("💡 Solution:")
    print("   Apply the RLS migration to fix admin access:")
    print("   1. See FIX_POOL_QUESTIONS_DISPLAY.md for instructions")
    print("   2. Use Supabase Dashboard SQL Editor (easiest)")
    print("   3. Or run: bash fix_pool_questions.sh")
    print()

    # Check for direct database connection
    print("🔌 Checking Direct Database Connection:")
    db_url = os.environ.get("SUPABASE_DB_URL", "")
    if db_url:
        print("   ✅ SUPABASE_DB_URL configured")
        print("   ℹ️  You can apply migrations via command line")
    else:
        print("   ℹ️  No SUPABASE_DB_URL configured")
        print("   ℹ️  Use Supabase Dashboard to apply migrations")
    print()

    print("=" * 60)
    print("✅ Diagnosis complete!")


if __name__ == "__main__":
    asyncio.run(diagnose())
