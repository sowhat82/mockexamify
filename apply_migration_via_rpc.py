#!/usr/bin/env python3
"""
Apply SQL migration using Supabase client
This script attempts to apply RLS policy changes via Supabase
"""

import os
import sys
from supabase import create_client

def main():
    # Read environment
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("ERROR: Missing SUPABASE_URL or SUPABASE_KEY")
        sys.exit(1)

    # Read migration file
    sql_file = "migrations/fix_admin_pool_questions_access.sql"
    if not os.path.exists(sql_file):
        print(f"ERROR: Migration file not found: {sql_file}")
        sys.exit(1)

    with open(sql_file, 'r') as f:
        sql = f.read()

    print(f"Migration file: {sql_file}")
    print(f"Supabase URL: {supabase_url}")
    print("\nTo apply this migration, you need to:")
    print("1. Go to your Supabase Dashboard: https://app.supabase.com")
    print(f"2. Select your project: mgdgovkyomfkcljutcsj")
    print("3. Navigate to SQL Editor (in the left sidebar)")
    print("4. Paste the following SQL and click 'Run':")
    print("\n" + "="*60)
    print(sql)
    print("="*60)
    print("\nAlternatively, if you have the database password:")
    print("1. Get your database password from Supabase Dashboard -> Project Settings -> Database")
    print("2. Add to .env file: SUPABASE_DB_URL=postgresql://postgres:[PASSWORD]@db.mgdgovkyomfkcljutcsj.supabase.co:5432/postgres")
    print("3. Run: SQL_FILE=migrations/fix_admin_pool_questions_access.sql python apply_supabase_sql.py")

if __name__ == "__main__":
    main()
