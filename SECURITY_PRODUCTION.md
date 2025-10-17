# Security & Production Deployment Guide

## ⚠️ CRITICAL: Quick Login Feature Security

### Overview
The Quick Login feature provides one-click admin/user login for **LOCAL TESTING ONLY**.

### Security Safeguards

The quick login buttons will **ONLY** appear when **ALL THREE** conditions are met:

```python
is_localhost = config.API_BASE_URL == "http://localhost:8000"
is_dev_env = config.ENVIRONMENT == "development"
is_demo = config.DEMO_MODE

# ALL THREE must be true
if is_localhost and is_dev_env and is_demo:
    # Show quick login buttons
```

### Triple Protection

1. **Localhost Check**: `API_BASE_URL` must be `http://localhost:8000`
2. **Development Environment**: `ENVIRONMENT` must be `development`
3. **Demo Mode**: `DEMO_MODE` must be `true`

### Production Configuration

When deploying to production, your `.env` file should have:

```env
ENVIRONMENT=production
DEMO_MODE=false
API_BASE_URL=https://yourdomain.com
```

With these settings, quick login buttons will **NEVER** appear, even if someone tries to manipulate the code.

---

## 🚀 Production Deployment Checklist

### Before Deploying to GitHub/Live Server

#### 1. Environment Variables
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEMO_MODE=false`
- [ ] Set `API_BASE_URL` to your actual domain (e.g., `https://mockexamify.com`)

#### 2. Credentials
- [ ] Change `ADMIN_PASSWORD` from default `admin123` to secure password
- [ ] Use production Stripe keys (`sk_live_...` not `sk_test_...`)
- [ ] Generate strong random `SECRET_KEY` (32+ characters)
- [ ] Verify Supabase credentials are for production database

#### 3. Security
- [ ] Ensure `.env` file is in `.gitignore` (NEVER commit to GitHub)
- [ ] Remove any test/debug code
- [ ] Verify all API keys are secure
- [ ] Enable HTTPS on your domain

#### 4. Testing
- [ ] Test that quick login buttons do NOT appear
- [ ] Test normal login works correctly
- [ ] Test all features in production environment
- [ ] Verify payment processing with real Stripe account

---

## 🔒 Environment File Security

### .env File (Never Commit!)

Your `.env` file contains sensitive credentials and must **NEVER** be committed to GitHub.

**Verify `.gitignore` includes:**
```
.env
.env.local
.env.production
*.env
```

### Streamlit Secrets (For Streamlit Cloud)

If deploying to Streamlit Cloud, add secrets through the web interface at:
Settings → Secrets

```toml
# Streamlit secrets.toml format
ENVIRONMENT = "production"
DEMO_MODE = "false"
API_BASE_URL = "https://yourdomain.com"

SUPABASE_URL = "your_url"
SUPABASE_KEY = "your_key"

STRIPE_SECRET_KEY = "sk_live_..."
STRIPE_PUBLISHABLE_KEY = "pk_live_..."

ADMIN_EMAIL = "admin@yourdomain.com"
ADMIN_PASSWORD = "secure_password_here"
```

---

## 🧪 Testing Production Configuration Locally

To test that quick login is properly disabled:

1. Create a temporary `.env.production` file:
```env
ENVIRONMENT=production
DEMO_MODE=false
API_BASE_URL=https://mockexamify.com
```

2. Temporarily copy it to `.env`
3. Run your app
4. **Verify quick login buttons do NOT appear**
5. Restore your local `.env` for development

---

## 📝 Development vs Production

### Development (.env)
```env
ENVIRONMENT=development
DEMO_MODE=true
API_BASE_URL=http://localhost:8000
ADMIN_PASSWORD=admin123  # OK for local testing
STRIPE_SECRET_KEY=sk_test_...  # Test keys
```
**Result**: Quick login buttons **VISIBLE** ✅

### Production (.env or Streamlit Secrets)
```env
ENVIRONMENT=production
DEMO_MODE=false
API_BASE_URL=https://mockexamify.com
ADMIN_PASSWORD=SecurePassword123!  # Strong password
STRIPE_SECRET_KEY=sk_live_...  # Live keys
```
**Result**: Quick login buttons **HIDDEN** ✅

---

## 🚨 Emergency: If Quick Login Appears in Production

If you accidentally see quick login in production:

1. **Immediately check environment variables**:
   - Verify `DEMO_MODE=false`
   - Verify `ENVIRONMENT=production`
   - Verify `API_BASE_URL` is not localhost

2. **Redeploy with correct configuration**

3. **Verify the fix**:
   - Load homepage
   - Go to login page
   - Confirm no quick login buttons

---

## 🔐 Password Security

### Admin Password Guidelines

**DO NOT use default password in production!**

Good password examples:
- `Mck3x@m1fy!Adm1n2024`
- `SecureP@ssw0rd#Admin`
- Use a password manager to generate

**Change password immediately after deployment**

---

## 📊 Monitoring

### Check Logs Regularly

Monitor for:
- Unauthorized login attempts
- API errors
- Payment failures
- Unusual traffic patterns

### Audit Admin Actions

Periodically review:
- Admin login times
- File uploads
- Question pool modifications
- User management actions

---

## 🛡️ Additional Security Measures

### 1. Rate Limiting
Consider adding rate limiting to prevent brute force attacks:
- Login attempts
- API calls
- File uploads

### 2. Two-Factor Authentication
Future enhancement: Add 2FA for admin accounts

### 3. IP Whitelisting
Optionally restrict admin access to specific IP ranges

### 4. Audit Logging
Log all admin actions with timestamps

---

## 📚 References

- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)
- [Supabase Security Best Practices](https://supabase.com/docs/guides/platform/going-into-prod)
- [Stripe Production Checklist](https://stripe.com/docs/keys#test-live-modes)

---

## ✅ Final Verification

Before going live, verify:

- [ ] Quick login buttons do NOT appear on login page
- [ ] Environment is set to `production`
- [ ] Demo mode is disabled
- [ ] All production credentials are configured
- [ ] `.env` file is NOT in GitHub
- [ ] Admin password is secure
- [ ] Stripe is in live mode
- [ ] All features work correctly
- [ ] HTTPS is enabled
- [ ] Database backups are configured

---

**Last Updated**: 2025-10-15
**Version**: 1.0.0

**Remember**: When in doubt, test locally with production settings first!
