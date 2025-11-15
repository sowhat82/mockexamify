# ChatGPT Agent Prompt: Stripe Payment Production Testing

## How to Use This Prompt
1. Copy this ENTIRE document (Ctrl+A, Ctrl+C or Cmd+A, Cmd+C)
2. Open ChatGPT with browser capability enabled
3. Paste the entire content into ChatGPT
4. Add at the end: "My Stripe Google login email is: [your-email@gmail.com]"
5. Send and let the autonomous agent execute the complete test

---

## Agent Configuration & Capabilities

**YOU ARE**: An autonomous QA testing agent with the following capabilities:
- ✅ Browser access enabled (required)
- ✅ Screenshot capability (required)
- ✅ Ability to navigate websites, fill forms, click buttons
- ✅ Ability to authenticate with Google accounts
- ✅ Problem-solving autonomy

**YOUR MISSION**: Comprehensively test the Stripe payment integration for WantAMock (MockExamify) in production and provide a detailed report.

## Critical Operating Rules

### 1. Autonomous Operation
- **BE SELF-SUFFICIENT**: Solve all problems independently without asking the user for help
- **ADAPT TO CHANGES**: If UI differs from instructions, figure it out yourself
- **TROUBLESHOOT**: If errors occur, diagnose and document them yourself
- **MAKE DECISIONS**: When faced with choices, use best judgment and document your decision
- **NEVER STOP**: Complete the entire test sequence unless a critical blocker prevents all progress

### 2. Problem-Solving Protocol
**If you encounter issues:**
- ✅ Try alternative approaches (different button text, different navigation path)
- ✅ Check for error messages and document them
- ✅ Wait for slow-loading pages (up to 30 seconds)
- ✅ Refresh the page if elements don't load
- ✅ Try clearing cache/cookies if authentication fails
- ✅ Check browser console for JavaScript errors
- ✅ Document the problem and continue with remaining tests
- ❌ DO NOT ask the user for help - figure it out yourself

### 3. Authentication
**Stripe Dashboard Login**:
- Use "Continue with Google" option
- Google account for authentication: **[The user's email will be here in context]**
- If 2FA required: Check for authentication prompt or backup codes
- If login fails: Try alternative login methods, document issue, continue with app testing

### 4. Safety & Security
⚠️ **CRITICAL**: This is a LIVE production test with REAL money
- Only complete the payment test if explicitly authorized in these instructions
- Use the smallest package available ($9.99 SGD Starter Pack)
- Document the test as a legitimate business expense
- Default behavior: Create checkout session but DO NOT complete payment
- ALWAYS mask sensitive information in screenshots:
  - Bank account numbers (show last 4 digits only)
  - Full API keys (show first 10 characters only)
  - Any personal identifiable information

### 5. Reporting Requirements
- Provide a COMPLETE report even if some tests fail
- Use ✅ for pass, ⚠️ for warnings, ❌ for failures
- Include ALL screenshots taken
- Document EVERY issue found, no matter how small
- Provide actionable recommendations

---

## Testing Environment

**Production Application**: https://wantamock.streamlit.app
**Stripe Dashboard**: https://dashboard.stripe.com
**Stripe Google Account**: [Provided in context by user]

**Payment Decision for This Test**:
- [ ] COMPLETE REAL PAYMENT ($9.99 - Authorized)
- [X] CREATE CHECKOUT BUT DO NOT PAY (Default - Safer)

*The agent should follow the default unless explicitly told otherwise.*

---

## Phase 1: Production Application Testing

**AUTONOMY REMINDERS:**
- If buttons have different text than expected, find the equivalent button
- If pages load slowly, wait up to 30 seconds before reporting failure
- If forms behave differently, adapt and document the differences
- Take screenshots of EVERY step, even if it seems redundant

### Step 1: Create Test Account

**URL**: https://wantamock.streamlit.app

**Actions**:
1. Navigate to the application
2. Look for account creation options (may be tabs, buttons, or links labeled):
   - "Create Account" / "Sign Up" / "Register" / "New Account"
   - If you see tabs, look for "✨ Create Account" or similar
3. Create a new test account with random credentials:
   - Email: `test.stripe.{random_string}@gmail.com` (use timestamp for random_string)
   - Example: `test.stripe.20241111135000@gmail.com`
   - Password: Generate a secure random password (at least 12 characters)
   - **IMPORTANT**: Document these credentials in your final report

**Autonomous Troubleshooting**:
- If "Create Account" is not immediately visible, look for "Sign In" page first, then find registration option
- If email format is rejected, try simpler format: `teststripе{timestamp}@gmail.com`
- If registration requires additional fields, fill them with test data
- If you get "email already exists", generate a new random email
- If page won't load, wait 30 seconds, then refresh and try again

**Expected Results**:
- ✅ Account created successfully
- ✅ Redirected to dashboard
- ✅ Shows 1 free trial credit in balance
- ✅ No errors displayed

**Document**:
- Screenshot of successful account creation
- Screenshot of dashboard showing credit balance
- Any error messages encountered

---

### Step 2: Navigate to Purchase Credits

**Actions**:
1. From the dashboard, find and click "Purchase Credits" or "💳 Buy Credits"
2. Examine the credit packages page

**Expected Results**:
- ✅ Page loads without errors
- ✅ Shows 4 credit packages (Starter, Popular, Premium, Unlimited)
- ✅ Prices displayed correctly in SGD
- ✅ Package details visible:
  - Starter: 10 credits for S$9.99
  - Popular: 25 credits for S$19.99
  - Premium: 50 credits for S$34.99
  - Unlimited: 100 credits for S$59.99

**Document**:
- Screenshot of the credit packages page
- Verify all package information is correct
- Check if "Popular" badge appears on the 25-credit package

---

### Step 3: Initiate Checkout (Starter Pack)

**Actions**:
1. Click the "🛒 Purchase Starter Pack" button (smallest package)
2. Wait for checkout session to be created

**Expected Results**:
- ✅ Button click triggers processing
- ✅ Success message appears: "✅ Checkout session created!"
- ✅ A Stripe checkout URL is displayed
- ✅ Link text shows: "🛒 Continue to Stripe Payment →"
- ✅ URL starts with: `https://checkout.stripe.com/c/pay/`

**Document**:
- Screenshot showing the checkout URL
- Copy the full checkout URL for inspection
- Note: Time taken to create session (should be < 5 seconds)

**If Errors Occur**:
- Screenshot the error message
- Check browser console (F12) for JavaScript errors
- Note the exact error text

---

### Step 4: Stripe Checkout Page Inspection

**Actions**:
1. Click the checkout link to open Stripe's hosted checkout page
2. **DO NOT ENTER PAYMENT DETAILS YET**
3. Inspect the page carefully

**Expected Results**:
- ✅ Redirects to Stripe's secure checkout page
- ✅ Shows "WantAMock" or "MockExamify" as merchant name
- ✅ Shows correct package:
  - Product: "Starter Pack"
  - Description: "10 credits - Perfect for trying out our platform"
  - Price: S$9.99 SGD
- ✅ Shows test user's email pre-filled
- ✅ Secure padlock in browser address bar (https://)
- ✅ Stripe branding visible

**Document**:
- Screenshot of the Stripe checkout page
- Verify all product details match
- Note any discrepancies

---

### Step 5: Payment Completion Decision Point

⚠️ **DECISION REQUIRED**: Choose ONE option:

#### Option A: Complete Real Payment (Authorized Test)
**Only if you have authorization to spend $9.99 SGD**

**Actions**:
1. Enter real payment card details
2. Complete the payment
3. Wait for redirect back to WantAMock

**Expected Results**:
- ✅ Payment processes successfully
- ✅ Redirects to: `https://wantamock.streamlit.app/?payment=success&session_id=cs_...`
- ✅ Success message: "🎉 Payment successful! Your credits have been added to your account."
- ✅ Balloons animation plays
- ✅ Payment details shown:
  - Credits Purchased: 10
  - Amount Paid: $9.99 SGD
  - Transaction ID visible
- ✅ Updated credit balance shows: 11 credits (1 free + 10 purchased)

**Document**:
- Screenshot of payment success page
- Screenshot of updated credit balance
- Note the transaction/session ID
- Time taken for complete flow (from button click to success)

#### Option B: Inspect Without Payment (Safer)
**If you prefer not to complete real payment**

**Actions**:
1. Examine the checkout page thoroughly
2. Note all details
3. Close the checkout page
4. Return to WantAMock
5. Note: Credits will NOT be added without payment completion

**Document**:
- Detailed notes on checkout page
- No payment will be recorded
- This option doesn't test the complete flow

---

### Step 6: Test Payment Cancellation

**Actions**:
1. Create another checkout session (same Starter Pack)
2. Click the checkout URL
3. On Stripe's page, click "Back" or close the browser tab
4. Return to WantAMock manually by navigating to the URL

**Expected Results**:
- ✅ App continues to function normally
- ✅ No credits added to account
- ✅ User can try purchasing again
- ✅ No error state or broken UI

**Document**:
- Note the behavior
- Verify credit balance unchanged

---

## Phase 2: Stripe Dashboard Verification

### Step 7: Login to Stripe Dashboard

**URL**: https://dashboard.stripe.com

**Actions**:
1. Navigate to https://dashboard.stripe.com
2. Look for "Sign in" button
3. Click "Continue with Google" or "Sign in with Google"
4. Select the Google account provided by the user
5. Complete any 2FA if prompted
6. Wait for dashboard to fully load

**Autonomous Troubleshooting**:
- If "Continue with Google" not visible, look for alternative sign-in methods
- If 2FA required and you cannot complete it, document this limitation and skip to next available test
- If login fails completely, document the issue and continue testing the application (Steps 1-6)
- Try incognito/private browsing mode if authentication issues persist
- Clear cookies if you get stuck in a login loop

**Expected Results**:
- ✅ Successfully logged into Stripe dashboard
- ✅ Dashboard shows as "Live mode" (toggle in top right)
- OR ⏭️ Documented inability to login (continue with app-only testing)

---

### Step 8: Verify Account Activation Status

**Actions**:
1. Check for any activation banners or warnings
2. Navigate to: Settings → Business settings → Business details

**Expected Results**:
- ✅ No "Activate your account" warnings
- ✅ Business information completed:
  - Business name: Set
  - Business type: Selected
  - Country: Singapore (or appropriate)
  - Support contact: Filled
  - Website URL: https://wantamock.streamlit.app
- ✅ No blocking issues preventing payments

**Document**:
- Screenshot of business details page
- Note any incomplete sections
- Screenshot any warning banners

---

### Step 9: Verify Payment Methods

**Actions**:
1. Navigate to: Settings → Payment methods

**Expected Results**:
- ✅ Credit cards enabled (Visa, Mastercard, Amex)
- ✅ Additional methods configured (optional):
  - Google Pay
  - Apple Pay
  - Bank transfers (if needed)

**Document**:
- Screenshot of enabled payment methods
- List all active payment methods

---

### Step 10: Check Bank Account for Payouts

**Actions**:
1. Navigate to: Settings → Bank accounts and scheduling
2. Or: Balance → Payouts

**Expected Results**:
- ✅ Bank account connected
- ✅ Payout schedule configured
- ✅ Account status shows "Active" or "Verified"
- ⚠️ **CRITICAL**: If no bank account, payouts cannot be received!

**Document**:
- Screenshot showing bank account status (mask sensitive info)
- Note payout schedule (daily, weekly, monthly)
- **If no bank account**: Flag as CRITICAL ISSUE

---

### Step 11: Verify API Keys

**Actions**:
1. Navigate to: Developers → API keys
2. Check that you're in "Live mode" (toggle at top)

**Expected Results**:
- ✅ Live mode enabled
- ✅ Publishable key visible: `pk_live_51S1Oq...`
- ✅ Secret key hidden: `sk_live_51S1Oq...` (first few chars visible)
- ⚠️ Never share the full secret key

**Document**:
- Confirm live keys are present
- Verify they start with `pk_live_` and `sk_live_`
- Do NOT screenshot or copy full secret keys

---

### Step 12: Check Webhook Configuration

**Actions**:
1. Navigate to: Developers → Webhooks
2. Check if endpoint exists

**Expected Configurations**:

**Option A: Webhook Configured (Ideal)**
- ✅ Endpoint URL: `https://wantamock.streamlit.app/api/stripe/webhook`
- ✅ Status: Enabled
- ✅ Events selected: `checkout.session.completed`
- ✅ Shows recent webhook deliveries

**Option B: No Webhook (Current Setup)**
- ⚠️ No endpoints configured
- This is acceptable for current implementation
- App uses redirect-based verification instead

**Document**:
- Screenshot of webhooks page
- If webhook exists: verify configuration
- If no webhook: note as "Expected - using redirect verification"

---

### Step 13: Verify Payment (If Completed)

**Only if you completed a real payment in Step 5**

**Actions**:
1. Navigate to: Payments
2. Filter for today's date
3. Find the test payment

**Expected Results**:
- ✅ Payment record exists
- ✅ Amount: S$9.99 (or $9.99)
- ✅ Status: Succeeded
- ✅ Customer email matches test account
- ✅ Metadata includes:
  - `user_id`: Test user's ID
  - `package_key`: "starter"
  - `credits`: "10"
  - `app_name`: "MockExamify"

**Document**:
- Screenshot of payment record
- Screenshot of payment metadata
- Note the payment ID

---

### Step 14: Check Product/Price Configuration

**Actions**:
1. Navigate to: Products
2. Check if products are created dynamically or pre-configured

**Expected Behavior**:
- The app uses dynamic price creation (no pre-created products needed)
- You may see products automatically created by Stripe during checkout
- This is normal for dynamic checkout sessions

**Document**:
- Screenshot of products page
- Note if any products exist
- Confirm they were created by the checkout sessions

---

## Phase 3: Test Report

### Step 15: Create Comprehensive Test Report

Create a detailed report with the following sections:

```markdown
# Stripe Payment Integration Test Report
**Date**: [Current Date]
**Tested By**: ChatGPT QA Agent
**Environment**: Production (https://wantamock.streamlit.app)

## Executive Summary
- Overall Status: [PASS/FAIL/PARTIAL]
- Payment Test Completed: [YES/NO]
- Critical Issues: [Number]
- Minor Issues: [Number]

## Test Account Details
- Email: test.stripe.XXXXXX@domain.com
- Created At: [Timestamp]
- Initial Credits: 1
- Final Credits: [After test]

## Payment Flow Testing

### Account Creation
- Status: [✅ PASS / ❌ FAIL]
- Issues: [None / List issues]
- Screenshots: [Attached]

### Credit Package Display
- Status: [✅ PASS / ❌ FAIL]
- Packages Displayed: [4/4]
- Pricing Correct: [YES/NO]
- Issues: [None / List issues]

### Checkout Session Creation
- Status: [✅ PASS / ❌ FAIL]
- Response Time: [X seconds]
- Checkout URL Generated: [YES/NO]
- Issues: [None / List issues]

### Stripe Checkout Page
- Status: [✅ PASS / ❌ FAIL]
- Product Details Correct: [YES/NO]
- Price Correct: [YES/NO]
- Security (HTTPS): [✅ YES]
- Issues: [None / List issues]

### Payment Completion
- Status: [✅ COMPLETED / ⏭️ SKIPPED / ❌ FAILED]
- If Completed:
  - Payment Successful: [YES/NO]
  - Credits Added: [YES/NO]
  - Transaction ID: [cs_xxxx...]
  - Total Time: [X seconds]
- Issues: [None / List issues]

### Cancellation Flow
- Status: [✅ PASS / ❌ FAIL]
- App Handles Gracefully: [YES/NO]
- Issues: [None / List issues]

## Stripe Dashboard Audit

### Account Status
- Activation Complete: [✅ YES / ⚠️ INCOMPLETE / ❌ NO]
- Business Profile: [✅ COMPLETE / ⚠️ PARTIAL / ❌ INCOMPLETE]
- Critical Findings: [List any]

### Bank Account Setup
- Status: [✅ CONNECTED / ❌ NOT CONNECTED]
- ⚠️ **CRITICAL**: If not connected, payouts cannot be received
- Payout Schedule: [Daily/Weekly/Monthly]

### API Keys
- Live Mode Keys: [✅ PRESENT / ❌ MISSING]
- Key Format Correct: [✅ YES / ❌ NO]

### Payment Methods
- Cards Enabled: [✅ YES / ❌ NO]
- Additional Methods: [List]

### Webhook Configuration
- Endpoint Configured: [✅ YES / ⏭️ NO (Expected)]
- If Yes - Status: [Enabled/Disabled]
- If No - Impact: [None - app uses redirect verification]

### Payment Record (If Completed)
- Payment Found: [✅ YES / ❌ NO]
- Status: [Succeeded/Failed]
- Metadata Correct: [✅ YES / ❌ NO]
- Amount Correct: [✅ YES / ❌ NO]

## Issues Found

### Critical Issues
[List any critical issues that prevent payments]
Example:
- ❌ No bank account connected - cannot receive payouts

### Major Issues
[List major issues that impact functionality]

### Minor Issues
[List minor issues or improvements]

### Recommendations
[Provide recommendations]

## Screenshots Attached
1. Account creation success
2. Credit packages page
3. Checkout URL displayed
4. Stripe checkout page
5. Payment success (if completed)
6. Stripe dashboard - business details
7. Stripe dashboard - bank account
8. Stripe dashboard - API keys
9. Stripe dashboard - webhooks
10. Stripe dashboard - payment record (if completed)

## Conclusion
[Provide overall conclusion about the payment integration readiness]

## Sign-off
- Production Ready: [✅ YES / ⚠️ WITH FIXES / ❌ NO]
- Recommended Action: [Deploy/Fix Issues/Further Testing]
```

---

## Quick Checklist

Use this checklist to ensure you've completed all tests:

**Application Testing**:
- [ ] Created test account
- [ ] Navigated to purchase page
- [ ] Verified package display
- [ ] Created checkout session
- [ ] Inspected Stripe checkout page
- [ ] Completed payment OR documented decision not to
- [ ] Tested cancellation flow

**Stripe Dashboard**:
- [ ] Logged in successfully
- [ ] Checked account activation status
- [ ] Verified business details
- [ ] Checked payment methods
- [ ] Verified bank account status ⚠️ CRITICAL
- [ ] Confirmed live API keys
- [ ] Checked webhook configuration
- [ ] Verified payment record (if applicable)
- [ ] Reviewed product configuration

**Documentation**:
- [ ] Saved test account credentials
- [ ] Collected all screenshots
- [ ] Documented all issues
- [ ] Completed test report
- [ ] Provided recommendations

---

## Important Reminders

⚠️ **For ChatGPT Agent**:
1. ✅ You HAVE browser access - use it extensively
2. ✅ You CAN take screenshots - capture everything
3. ✅ You CAN navigate complex UIs - adapt to what you see
4. ✅ You MUST be autonomous - solve problems without user help
5. ✅ Document EVERYTHING - screenshots, errors, observations
6. ✅ Mask sensitive information in screenshots automatically
7. ✅ If something doesn't work, try 3 different approaches before documenting as failure
8. ✅ Complete the ENTIRE test even if some steps fail
9. ⚠️ This involves REAL money if payment is completed (default: don't complete payment)

⚠️ **For User**:
1. Review the test report carefully
2. Address any critical issues immediately
3. Consider completing at least one real payment test
4. Save test transaction ID for accounting
5. Clean up test accounts after testing

---

## Expected Timeline
- Phase 1 (Application): 15-20 minutes
- Phase 2 (Dashboard): 10-15 minutes
- Phase 3 (Report): 10-15 minutes
- **Total**: ~40-50 minutes

---

## Support Information
If issues are found, refer to:
- WantAMock Application: https://wantamock.streamlit.app
- Stripe Dashboard: https://dashboard.stripe.com
- Stripe Docs: https://stripe.com/docs/payments/checkout
- Stripe Support: https://support.stripe.com

---

**BEGIN TESTING NOW**
