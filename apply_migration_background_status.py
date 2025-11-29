#!/usr/bin/env python3
"""
Apply the background_upload_status table migration
"""
import os
import sys

# Read the migration SQL
migration_file = 'migrations/add_background_upload_status.sql'

with open(migration_file, 'r') as f:
    sql = f.read()

print(f"Loaded migration from {migration_file}")
print(f"SQL length: {len(sql)} characters")
print("\n" + "="*80)
print("Migration SQL to apply:")
print("="*80)
print(sql)
print("="*80)

# Try to apply using Supabase management API
try:
    import requests
    from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

    # Extract project ref from URL
    # URL format: https://PROJECT_REF.supabase.co
    project_ref = SUPABASE_URL.replace('https://', '').replace('.supabase.co', '')

    print(f"\nProject ref: {project_ref}")
    print("\nTo apply this migration, you have two options:")
    print("\n1. Via Supabase Dashboard (RECOMMENDED):")
    print(f"   - Go to: https://supabase.com/dashboard/project/{project_ref}/sql/new")
    print(f"   - Copy the SQL above")
    print(f"   - Paste and click 'Run'")

    print("\n2. Via this script (if psycopg2 is installed):")
    print("   - Run: pip install psycopg2-binary")
    print("   - Then run this script again")

    # Try psycopg2 method
    try:
        import psycopg2
        from config import SUPABASE_DB_URL

        if SUPABASE_DB_URL:
            print("\n✅ Database connection available!")
            print("\nApplying migration...")

            conn = psycopg2.connect(SUPABASE_DB_URL)
            cur = conn.cursor()
            cur.execute(sql)
            conn.commit()
            cur.close()
            conn.close()

            print("✅ Migration applied successfully!")
            sys.exit(0)
        else:
            print("\n⚠️  SUPABASE_DB_URL not configured")

    except ImportError:
        print("\n⚠️  psycopg2 not installed (this is fine, use option 1 above)")
    except Exception as e:
        print(f"\n❌ Error applying migration: {e}")
        print("\nPlease use option 1 (Supabase Dashboard) to apply the migration")

except Exception as e:
    print(f"\nError: {e}")
    print("\nPlease copy the SQL above and run it in Supabase SQL Editor")
