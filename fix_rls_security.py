"""
Fix RLS Security Issues - Apply Row Level Security to Supabase Database
This script enables RLS and creates policies for all public tables
"""
import os
import sys
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Get authenticated Supabase client"""
    try:
        import config
        url = config.get_secret("SUPABASE_URL")
        # Use service role key for admin operations
        key = config.get_secret("SUPABASE_SERVICE_ROLE_KEY", None)
        if not key:
            # Fallback to anon key (less powerful but might work for some operations)
            key = config.get_secret("SUPABASE_KEY")
            print("⚠️  Using anon key - you may need service role key for full RLS setup")
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        sys.exit(1)
    
    return create_client(url, key)

def enable_rls_via_api():
    """Enable RLS using Supabase client SQL execution"""
    supabase = get_supabase_client()
    
    # Read the RLS policies SQL file
    sql_file = "database_rls_policies.sql"
    if not os.path.exists(sql_file):
        print(f"❌ RLS policies file not found: {sql_file}")
        return False
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print("📋 RLS Policies to apply:")
    print("=" * 60)
    print(sql_content)
    print("=" * 60)
    
    print("\n⚠️  IMPORTANT: You need to run this SQL manually in Supabase SQL Editor")
    print("\n📝 Steps to fix RLS security:")
    print("1. Go to: https://supabase.com/dashboard/project/mgdgovkyomfkcljutcsj/sql/new")
    print("2. Copy the SQL from 'database_rls_policies.sql'")
    print("3. Paste and run it in the SQL Editor")
    print("4. Verify policies are created in Database > Policies")
    
    return True

def verify_rls_status():
    """Check if RLS is enabled (requires direct DB access)"""
    print("\n🔍 To verify RLS is enabled after applying:")
    print("Run this query in Supabase SQL Editor:")
    print("""
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('users', 'mocks', 'attempts', 'tickets');
    """)
    print("\nAll tables should show 'rowsecurity = true'")

if __name__ == "__main__":
    print("🔒 MockExamify RLS Security Fix")
    print("=" * 60)
    
    enable_rls_via_api()
    verify_rls_status()
    
    print("\n✅ Next steps:")
    print("1. Apply the SQL in Supabase Dashboard")
    print("2. Run the verification query")
    print("3. Check that security warnings are resolved")
