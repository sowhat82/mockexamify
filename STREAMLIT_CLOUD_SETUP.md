# Streamlit Cloud Setup Instructions

## Required Secrets Configuration

To enable user registration on Streamlit Cloud, you MUST configure the following secrets:

### 1. Add SUPABASE_SERVICE_KEY to Streamlit Secrets

1. Go to https://app.streamlit.io/
2. Navigate to your app settings
3. Click on "Secrets" in the left sidebar
4. Add the following secret:

```toml
SUPABASE_SERVICE_KEY = "your-service-role-key-here"
```

### 2. Get Your Service Role Key from Supabase

1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to Project Settings → API
4. Copy the **service_role** key (NOT the anon key!)
   - ⚠️ **WARNING**: The service_role key bypasses Row Level Security - keep it secret!

### 3. Apply RLS Policy Fix

Run the SQL script `fix_user_registration_rls.sql` in your Supabase SQL Editor:

1. Go to https://supabase.com/dashboard
2. Select your project
3. Click "SQL Editor" in the left sidebar
4. Click "New Query"
5. Copy and paste the contents of `fix_user_registration_rls.sql`
6. Click "Run"

This script creates an INSERT policy for the users table that allows the service role to create new users.

### 4. Verify Configuration

After adding the secret and applying the SQL:

1. Wait 1-2 minutes for Streamlit Cloud to redeploy
2. Try registering a new user on your live site
3. If you still see errors, check the Streamlit Cloud logs for details

## Current Secrets Needed

```toml
# Required for database access
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key"
SUPABASE_SERVICE_KEY = "your-service-role-key"  # ← REQUIRED FOR REGISTRATION

# Required for payments
STRIPE_SECRET_KEY = "sk_live_..."
STRIPE_PUBLISHABLE_KEY = "pk_live_..."
STRIPE_WEBHOOK_SECRET = "whsec_..."

# Required for AI features
OPENROUTER_API_KEY = "sk-or-..."

# Application security
SECRET_KEY = "your-random-secret-key"
ENVIRONMENT = "production"
```

## Troubleshooting

### Error: "Database admin access not configured"
- The `SUPABASE_SERVICE_KEY` is not set in Streamlit secrets
- Solution: Add the service role key as shown above

### Error: "new row violates row-level security policy"
- The service role key is set but RLS policy is blocking inserts
- Solution: Run the `fix_user_registration_rls.sql` script

### Error: "Registration error: ..."
- Check Streamlit Cloud logs for the full error message
- Ensure your Supabase database has a `users` table with the correct schema
