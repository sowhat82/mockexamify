# HitPay PayNow Integration - Setup Instructions

## Overview
This document explains how to set up HitPay to accept PayNow payments alongside Stripe for your MockExamify application.

---

## What You Need to Do (Manual Steps)

### 1. Create HitPay Account
1. Go to https://www.hitpayapp.com/
2. Click "Sign Up" and create a business account
3. Complete business verification (UEN or personal IC)
4. **Note**: Personal accounts can receive payments, but corporate accounts get better rates

### 2. Get Your API Keys
After account approval:
1. Log in to HitPay Dashboard
2. Go to **Settings** → **Payment Gateway** → **API Keys**
3. Copy the following:
   - **API Key** (starts with something like `pk_live_...` or `pk_test_...`)
   - **Salt** (webhook signature verification)

### 3. Add Keys to Your Application

#### For Localhost Testing:
Create/edit `.streamlit/secrets.toml`:
```toml
# Existing Stripe keys...
STRIPE_SECRET_KEY = "sk_test_..."
STRIPE_WEBHOOK_SECRET = "whsec_..."

# New HitPay keys
HITPAY_API_KEY = "your_hitpay_api_key_here"
HITPAY_SALT = "your_hitpay_salt_here"
ENABLE_HITPAY = true  # Set to false to disable HitPay
```

#### For Production (Streamlit Cloud):
1. Go to your Streamlit Cloud dashboard
2. Click on your app → **Settings** → **Secrets**
3. Add the same keys as above

### 4. Configure Webhook in HitPay Dashboard
Once deployed:
1. Go to HitPay Dashboard → **Settings** → **Payment Gateway** → **Webhooks**
2. Add webhook URL: `https://your-app.streamlit.app/api/payments/hitpay-webhook`
3. For localhost testing: Use ngrok to expose localhost (see below)

### 5. (Optional) Set Up ngrok for Localhost Testing
To test PayNow webhooks on localhost:
```bash
# Install ngrok: https://ngrok.com/download
ngrok http 8501

# Copy the https URL (e.g., https://abc123.ngrok.io)
# Add webhook in HitPay: https://abc123.ngrok.io/api/payments/hitpay-webhook
```

---

## How to Enable/Disable HitPay

### To Enable PayNow:
In `.streamlit/secrets.toml`:
```toml
ENABLE_HITPAY = true
```
Users will see both Stripe and PayNow options.

### To Disable PayNow (Hide Everything):
```toml
ENABLE_HITPAY = false
```
OR simply remove `ENABLE_HITPAY` key entirely. Application will work exactly as before (Stripe only).

---

## Testing PayNow Payment Flow

### Test Mode (Sandbox):
1. HitPay provides test API keys (usually `pk_test_...`)
2. Use test keys in secrets.toml
3. Make a test purchase - HitPay will show test payment page
4. **Note**: Test mode may not generate real QR codes, check HitPay docs

### Live Mode:
1. Use live API keys (`pk_live_...`)
2. Make a small real payment (e.g., Starter Pack $9.99)
3. Scan QR with your banking app
4. Complete payment
5. Check if credits are added to your account

---

## HitPay Payment Flow (How It Works)

```
User clicks "Pay with PayNow"
    ↓
System creates HitPay payment request
    ↓
User sees HitPay page with PayNow QR code
    ↓
User scans QR with DBS/OCBC/UOB/etc app
    ↓
User completes payment in banking app
    ↓
HitPay detects payment (usually <5 seconds)
    ↓
HitPay sends webhook to your app
    ↓
Your app verifies webhook signature
    ↓
Your app adds credits to user account
    ↓
User sees updated credit balance
```

---

## Pricing Comparison

| Payment Method | Fee | Your Cost (Starter $9.99) |
|----------------|-----|---------------------------|
| Stripe (Cards) | 3.4% + $0.50 | **$0.84** (8.4%) |
| HitPay PayNow  | 1.5% | **$0.15** (1.5%) |
| **Savings**    | — | **$0.69 saved per transaction** |

---

## Troubleshooting

### PayNow option doesn't show up:
- Check `ENABLE_HITPAY = true` in secrets.toml
- Restart Streamlit app
- Check logs for HitPay initialization errors

### Payment completed but credits not added:
- Check application logs for webhook errors
- Verify webhook URL is correct in HitPay dashboard
- Check webhook signature (HITPAY_SALT) is correct
- Manually add credits to user (contact support)

### Webhook not received:
- Verify webhook URL is accessible (not localhost without ngrok)
- Check HitPay dashboard → Webhooks → Logs for delivery attempts
- Ensure URL ends with `/api/payments/hitpay-webhook`

### HitPay API errors:
- Verify API key is correct and active
- Check if account is approved/verified
- Check HitPay status page for outages

---

## Reverting Changes (Going Back to Stripe Only)

### Option 1: Disable via Config (Recommended)
```toml
ENABLE_HITPAY = false
```
All HitPay code remains in place but hidden from users.

### Option 2: Remove HitPay Code Entirely
```bash
git revert <commit-hash-of-hitpay-integration>
git push
```

---

## Support

- **HitPay Documentation**: https://docs.hitpayapp.com/
- **HitPay Support**: support@hit-pay.com
- **Stripe Documentation**: https://stripe.com/docs

---

## Security Notes

1. **Never commit API keys to git** - Always use secrets.toml or environment variables
2. **Verify webhook signatures** - Code automatically verifies HitPay webhooks using SALT
3. **Use HTTPS in production** - Webhooks only work with HTTPS URLs
4. **Monitor webhook logs** - Check for suspicious activity or failed verifications

---

## Next Steps After Setup

1. Test with small real payment in live mode
2. Monitor first few transactions closely
3. Check webhook logs in HitPay dashboard
4. Set up email notifications for failed webhooks
5. Gradually increase usage as confidence grows
