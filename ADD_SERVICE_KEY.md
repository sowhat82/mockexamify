# ✅ Final Step: Add Supabase Service Role Key

## ✨ Good News!

The RLS policies have been applied successfully, and I've updated the code to use a **Supabase Service Role Key** for admin operations. This will bypass RLS checks and allow admins to see all question pools.

## 🔑 What You Need to Do

Add your Supabase Service Role Key to the `.env` file. This key has special permissions that bypass Row Level Security policies.

### Step 1: Get Your Service Role Key

1. Go to: https://app.supabase.com/project/mgdgovkyomfkcljutcsj/settings/api

2. Scroll down to the **"Project API keys"** section

3. Find the **"service_role" key** (NOT the anon key!)
   - It should be labeled: `service_role` `secret`
   - ⚠️ **Warning:** This is a sensitive key - keep it secure!

4. Click the copy button to copy the key

### Step 2: Add to .env File

1. Open the `.env` file in your project root

2. Find this line:
```env
# SUPABASE_SERVICE_KEY=your-service-key-here
```

3. Uncomment it and replace with your actual key:
```env
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3M...your-actual-key-here
```

### Step 3: Restart the App

```bash
# Stop the app if running (Ctrl+C)
# Then restart:
bash run_all.sh
```

### Step 4: Test It!

1. Open your admin dashboard: http://localhost:8501
2. Navigate to "Question Pool Management"
3. Click "View Questions" on "CACS Paper 2"
4. 🎉 You should now see all 85 questions!

---

## 🔧 Code Changes Made

I've already updated the code for you:

### 1. **config.py**
Added support for the service role key:
```python
SUPABASE_SERVICE_KEY = get_secret("SUPABASE_SERVICE_KEY", "")
```

### 2. **db.py**
- Created an `admin_client` using the service role key
- Updated all question pool methods to use `admin_client`:
  - `get_all_question_pools()`
  - `get_pool_questions()`
  - `get_random_pool_questions()`

These changes allow admin operations to bypass RLS policies.

---

## ⚠️ Security Notes

**The service role key:**
- Has **full access** to your database (bypasses all RLS)
- Should **NEVER** be exposed to the frontend
- Should **NEVER** be committed to git (already in .gitignore)
- Should only be used server-side for admin operations

**Current implementation is secure because:**
- The key is only stored in `.env` (server-side)
- Only used in backend database operations
- Never sent to the browser
- Protected by `.gitignore`

---

## 🔍 Verification

After adding the key and restarting, you should see this in the logs:
```
INFO:db:Admin client initialized with service role key
```

If you see this instead:
```
WARNING:db:No service role key found - admin operations may fail due to RLS
```

Then the key wasn't loaded properly - check that:
1. The key is on the correct line in `.env`
2. The line is not commented out (no `#` at the start)
3. There are no extra spaces or quotes
4. You restarted the app after adding the key

---

## 🎯 Quick Reference

**Where to get the key:**
https://app.supabase.com/project/mgdgovkyomfkcljutcsj/settings/api

**What to add to .env:**
```env
SUPABASE_SERVICE_KEY=your-actual-service-role-key
```

**How to restart:**
```bash
bash run_all.sh
```

**Where to test:**
http://localhost:8501 → Question Pool Management → View Questions

---

## ❓ Troubleshooting

**Q: I added the key but still see "No questions found"**
- Make sure you restarted the app
- Check the logs for "Admin client initialized with service role key"
- Verify the key is correct (copy-paste from Supabase)

**Q: The logs show "No service role key found"**
- Check that the line in `.env` is uncommented
- Make sure there's no space before `SUPABASE_SERVICE_KEY`
- Restart the app

**Q: I get an error about invalid JWT**
- You may have copied the wrong key - use the `service_role` key, not the `anon` key
- Make sure you copied the entire key (they're long!)

---

🎉 **Once you add the service role key and restart, everything will work!**
