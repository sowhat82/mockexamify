# Fix for Ticket Response Failure in Production

## Problem
Admin cannot reply to tickets in production. Error: `column tickets.responses does not exist`

## Root Cause
The `tickets` table in the production Supabase database is missing several columns that the application expects, including the critical `responses` column needed to store ticket replies.

## Solution
Run the SQL migration to add all missing columns.

## Steps to Fix

### 1. Go to Supabase SQL Editor
1. Open your Supabase dashboard: https://supabase.com/dashboard
2. Select your project: `mgdgovkyomfkcljutcsj`
3. Click on "SQL Editor" in the left sidebar

### 2. Run the Migration
1. Click "New Query"
2. Copy and paste the contents of `fix_tickets_table_schema.sql`
3. Click "Run" or press Ctrl+Enter

### 3. Verify
The script will output the current schema of the tickets table. Verify that you see the new columns:
- `responses` (JSONB)
- `description` (TEXT)
- `user_email` (VARCHAR)
- `category` (VARCHAR)
- `priority` (VARCHAR)
- `browser` (VARCHAR)
- `device` (VARCHAR)
- `error_message` (TEXT)
- `affected_exam` (VARCHAR)
- `email_updates` (BOOLEAN)
- `attachment_url` (TEXT)

### 4. Test
1. Wait for Streamlit Cloud to redeploy (or it may already be deployed)
2. Go to https://wantamock.streamlit.app/
3. Login as admin
4. Try replying to a ticket
5. It should now work!

## What This Migration Does
- Adds all missing columns to the tickets table
- Sets appropriate defaults for new columns
- Creates indexes for better query performance
- Updates existing tickets to have empty arrays for responses
- Is safe to run multiple times (uses `IF NOT EXISTS` and `ADD COLUMN IF NOT EXISTS`)

## Technical Details
The application code was trying to:
1. Fetch a ticket's `responses` field
2. Append a new response to the array
3. Update the ticket with the new responses array

But the `responses` column didn't exist in the database, causing a 400 error from the Supabase API.
