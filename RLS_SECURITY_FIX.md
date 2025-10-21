# RLS Security Fix Guide

## Problem
Supabase detected that Row Level Security (RLS) is not enabled on the following tables:
- `public.users`
- `public.mocks`
- `public.attempts`
- `public.tickets`

This is a **CRITICAL SECURITY ISSUE** that exposes your data to unauthorized access.

## Quick Fix (Recommended)

### Option 1: Using Supabase Dashboard (Easiest)

1. **Open Supabase SQL Editor**
   - Go to: https://supabase.com/dashboard/project/mgdgovkyomfkcljutcsj/sql/new

2. **Copy and paste the entire content from `database_rls_policies.sql`**

3. **Click "RUN" to execute**

4. **Verify RLS is enabled:**
   ```sql
   SELECT schemaname, tablename, rowsecurity
   FROM pg_tables
   WHERE schemaname = 'public'
   AND tablename IN ('users', 'mocks', 'attempts', 'tickets');
   ```
   All tables should show `rowsecurity = true`

5. **Check policies are created:**
   - Go to: Database > Policies in Supabase Dashboard
   - You should see policies for each table

### Option 2: Using Direct Database Connection

If you have the Postgres connection string (service role):

1. **Add to your `streamlit-secrets.toml`:**
   ```toml
   SUPABASE_DB_URL = "postgres://postgres:[YOUR-PASSWORD]@db.mgdgovkyomfkcljutcsj.supabase.co:5432/postgres"
   ```

2. **Install psycopg2:**
   ```bash
   pip install psycopg2-binary
   ```

3. **Run the apply script:**
   ```bash
   python apply_supabase_sql.py
   ```

## Understanding the RLS Policies

### Users Table
- ✅ Users can only read/update their own data
- ✅ Protected by `auth.uid()` matching

### Mocks Table
- ✅ Public can view active mocks (is_active = true)
- ✅ Only admins can create/update mocks
- ✅ Protected by role check

### Attempts Table
- ✅ Users can only access their own exam attempts
- ✅ Protected by user_id matching

### Tickets Table
- ✅ Users can only view/create their own tickets
- ✅ Admins can view all tickets
- ✅ Protected by user_id and role checks

## Verification Steps

After applying the SQL:

1. **Check RLS is enabled:**
   ```sql
   SELECT tablename, rowsecurity
   FROM pg_tables
   WHERE schemaname = 'public';
   ```

2. **List all policies:**
   ```sql
   SELECT schemaname, tablename, policyname, permissive, roles, cmd
   FROM pg_policies
   WHERE schemaname = 'public'
   ORDER BY tablename, policyname;
   ```

3. **Test with your app:**
   - Try logging in as a regular user
   - Verify you can only see your own data
   - Try admin functions with admin account

## Security Benefits

✅ **Data Isolation**: Users can only access their own data
✅ **Admin Controls**: Only admins can manage mocks
✅ **Authentication Required**: Most operations require auth
✅ **Supabase Compliance**: Meets security linter requirements

## Troubleshooting

### "Permission denied" errors after enabling RLS
- This is expected! It means RLS is working
- Make sure your app uses authenticated requests
- Check that `auth.uid()` is being passed correctly

### Policies not applying
- Verify you're using the service role key for setup
- Check that auth is working in your app
- Review policy conditions match your use case

### Admin can't access data
- Verify admin user has `role = 'admin'` in users table
- Check admin policies include role check
- Make sure you're authenticated as admin

## Migration Checklist

- [ ] Backup your database (Supabase does this automatically)
- [ ] Apply RLS policies via SQL Editor
- [ ] Verify RLS is enabled on all tables
- [ ] Test login and basic operations
- [ ] Test admin functions
- [ ] Verify security warnings are cleared
- [ ] Monitor application logs for permission errors

## Support

If you encounter issues:
1. Check Supabase Dashboard > Database > Policies
2. Review logs in Supabase Dashboard > Logs
3. Test with a simple query in SQL Editor first
4. Verify your auth tokens are valid

---

**Priority**: CRITICAL - Apply immediately
**Estimated Time**: 5-10 minutes
**Risk Level**: Low (policies are permissive for existing functionality)
