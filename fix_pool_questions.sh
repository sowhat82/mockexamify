#!/bin/bash
# Quick fix for pool questions display issue
# This script applies the RLS migration to allow admins to view all pool questions

echo "🔧 MockExamify - Fix Pool Questions Display"
echo "=========================================="
echo ""

# Check if database password is provided
if [ -z "$DB_PASSWORD" ]; then
    echo "To apply this fix, you need your Supabase database password."
    echo ""
    echo "📋 Steps to get your database password:"
    echo "1. Go to: https://app.supabase.com/project/mgdgovkyomfkcljutcsj/settings/database"
    echo "2. Scroll to 'Connection string' section"
    echo "3. Click 'Reset database password' if needed, or use existing password"
    echo ""
    echo "📝 Then run this script with your password:"
    echo "   DB_PASSWORD='your-password-here' bash fix_pool_questions.sh"
    echo ""
    echo "Or add to .env file:"
    echo "   SUPABASE_DB_URL=postgresql://postgres.mgdgovkyomfkcljutcsj:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    echo ""
    exit 1
fi

# Construct database URL
DB_URL="postgresql://postgres.mgdgovkyomfkcljutcsj:${DB_PASSWORD}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

# Export for Python script
export SUPABASE_DB_URL="$DB_URL"
export SQL_FILE="migrations/fix_admin_pool_questions_access.sql"

echo "✅ Applying migration..."
source venv/bin/activate
python apply_supabase_sql.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Success! Pool questions should now be visible in the admin dashboard."
    echo "🔄 Refresh your browser to see the changes."
else
    echo ""
    echo "❌ Migration failed. Please check the error message above."
fi
