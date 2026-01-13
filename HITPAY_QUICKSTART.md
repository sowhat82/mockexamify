# HitPay PayNow - Quick Start Guide

## 5-Minute Setup for Localhost Testing

### Step 1: Database Migration (2 minutes)

1. Go to your Supabase dashboard
2. Click "SQL Editor"
3. Copy and paste this SQL:

```sql
ALTER TABLE payments
ADD COLUMN IF NOT EXISTS hitpay_payment_id TEXT,
ADD COLUMN IF NOT EXISTS payment_method TEXT DEFAULT 'stripe';

CREATE INDEX IF NOT EXISTS idx_payments_hitpay_id
ON payments(hitpay_payment_id);
```

4. Click "Run"
5. Verify: Should see "Success. No rows returned"

### Step 2: Get HitPay Keys (3 minutes)

1. Go to https://www.hitpayapp.com/ and sign up
2. Complete verification (may take a few hours/days for approval)
3. Once approved, go to Settings → Payment Gateway → API Keys
4. Copy:
   - **API Key** (starts with `pk_test_` or `pk_live_`)
   - **Salt** (for webhook verification)

### Step 3: Add to Secrets (1 minute)

Edit `.streamlit/secrets.toml`:

```toml
# Add these lines (keep your existing Stripe keys)
ENABLE_HITPAY = true
HITPAY_API_KEY = "paste_your_api_key_here"
HITPAY_SALT = "paste_your_salt_here"
```

### Step 4: Restart App

```bash
# Kill the app (Ctrl+C in terminal)
streamlit run streamlit_app.py
```

### Step 5: Test

1. Open http://localhost:8501
2. Log in
3. Go to "Purchase Credits"
4. You should see **TWO buttons** for each package:
   - 💳 Credit Card (Stripe)
   - 📱 PayNow (SG) (HitPay)
5. Click "📱 PayNow (SG)" for Starter Pack
6. You'll be redirected to HitPay
7. Scan the QR code with your banking app
8. Complete payment
9. Check if credits are added!

---

## To Disable (Go Back to Stripe Only)

Edit `.streamlit/secrets.toml`:

```toml
ENABLE_HITPAY = false
```

Restart app → PayNow buttons disappear!

---

## Troubleshooting

**"PayNow button doesn't show"**
- Check `ENABLE_HITPAY = true` (not "True", must be lowercase)
- Restart app after changing secrets
- Check logs for HitPay initialization errors

**"HitPay account not approved yet"**
- You can still test the UI with `ENABLE_HITPAY = true`
- API calls will fail until account is approved
- Usually takes 1-2 business days for approval

**"Webhook not working"**
- For localhost, you need ngrok (see main setup instructions)
- For production, webhook URL must be HTTPS
- Check HitPay dashboard → Webhooks → Logs

---

## Full Documentation

- **Complete Setup**: `HITPAY_SETUP_INSTRUCTIONS.md`
- **Overview**: `HITPAY_INTEGRATION_SUMMARY.md`
- **Database**: `HITPAY_DATABASE_MIGRATION.md`

---

## What Was Changed

**New Files:**
- `hitpay_utils.py` (payment logic)

**Modified Files:**
- `config.py` (+3 lines)
- `api.py` (+1 webhook endpoint)
- `db.py` (+2 methods)
- `app_pages/purchase_credits.py` (+ PayNow UI)

**All changes are feature-flagged** - setting `ENABLE_HITPAY = false` makes the app behave exactly as before!

---

## Need Help?

1. Check `HITPAY_SETUP_INSTRUCTIONS.md` for detailed troubleshooting
2. Check HitPay docs: https://docs.hitpayapp.com/
3. Contact HitPay support: support@hit-pay.com
