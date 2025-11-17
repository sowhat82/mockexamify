# Email Notification Setup Guide

This guide explains how to configure email notifications for WantAMock.

## Overview

Email notifications are sent for:
- New support tickets (to admin)
- Payment confirmations (future)
- User signups (future)

## Gmail SMTP Setup (Recommended for Testing)

### Step 1: Enable 2-Factor Authentication

1. Go to your Google Account: https://myaccount.google.com/
2. Navigate to Security → 2-Step Verification
3. Follow the prompts to enable 2FA if not already enabled

### Step 2: Create App Password

1. Go to https://myaccount.google.com/apppasswords
2. Select app: "Mail"
3. Select device: "Other" (enter "WantAMock")
4. Click "Generate"
5. Copy the 16-character password (e.g., "abcd efgh ijkl mnop")

### Step 3: Add to Environment Variables (Localhost)

Create a `.env` file in your project root or add to your existing one:

```env
# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
```

Replace:
- `your.email@gmail.com` with your Gmail address
- `your-16-char-app-password` with the app password from Step 2 (remove spaces)

### Step 4: Add to Streamlit Cloud Secrets

For production deployment on Streamlit Cloud:

1. Go to your app dashboard: https://share.streamlit.io/
2. Click on your app → Settings → Secrets
3. Add the following to your `secrets.toml`:

```toml
# Email Configuration
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USER = "your.email@gmail.com"
SMTP_PASSWORD = "your-16-char-app-password"
```

## Alternative SMTP Providers

### SendGrid (Better for Production)

1. Sign up at https://sendgrid.com/ (Free tier: 100 emails/day)
2. Create an API key
3. Use these settings:

```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

### AWS SES (Cheapest for Scale)

1. Sign up for AWS SES
2. Verify your email
3. Create SMTP credentials
4. Use the credentials provided by AWS

## Testing the Email System

### Test on Localhost

1. Set up your `.env` file with SMTP credentials
2. Run the app: `streamlit run streamlit_app.py`
3. Submit a support ticket
4. Check the terminal logs for:
   - "Email sent successfully..." (if SMTP configured)
   - "SMTP not configured..." (if not configured - this is OK for testing)

### Verify Email Sent

Check your `alvincheong@u.nus.edu` inbox for:
- Subject: "🎫 New [Priority] Support Ticket: [Subject]"
- Beautiful HTML formatted email with ticket details

## Troubleshooting

### "SMTP not configured"
This is normal if you haven't set up SMTP yet. The app will still work, just won't send emails. The logs will show what email would have been sent.

### "Authentication failed"
- Double-check your app password (no spaces)
- Make sure 2FA is enabled on your Google account
- Try generating a new app password

### "Connection refused"
- Check your SMTP_HOST and SMTP_PORT
- Make sure your firewall isn't blocking port 587
- Try port 465 with SSL instead

### Gmail "Less secure app" error
Don't use "less secure apps" - always use App Passwords with 2FA enabled.

## Security Notes

- ✅ **Never commit SMTP credentials to git**
- ✅ Use `.env` for localhost (add `.env` to `.gitignore`)
- ✅ Use Streamlit Secrets for production
- ✅ Use App Passwords, not your main Gmail password
- ✅ Rotate credentials periodically

## Email Template Customization

The email templates are in `email_utils.py`:
- HTML template with WantAMock branding
- Automatic formatting of ticket priority (High = red, Medium = orange, Low = green)
- Responsive design for mobile email clients

To customize, edit the `send_support_ticket_notification()` function in `email_utils.py`.

## Admin Email Address

Currently set to: `alvincheong@u.nus.edu`

To change, edit the `ADMIN_EMAIL` constant in `email_utils.py`:

```python
ADMIN_EMAIL = "your-new-admin-email@example.com"
```
