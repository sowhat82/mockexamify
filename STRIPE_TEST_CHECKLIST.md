# Stripe Production Test Checklist

Quick reference checklist for manual or ChatGPT-assisted testing.

## Pre-Test Setup
- [ ] Have Stripe Google account credentials ready
- [ ] Decide: Complete real payment ($9.99) or inspect only?
- [ ] Prepare screenshot tool
- [ ] Estimated time: 30-40 minutes

---

## Application Testing (wantamock.streamlit.app)

### 1. Account Creation
- [ ] Navigate to https://wantamock.streamlit.app
- [ ] Click "✨ Create Account" tab
- [ ] Create test account: `test.stripe.[random]@[domain].com`
- [ ] Account created successfully
- [ ] Shows 1 free credit
- [ ] 📸 Screenshot: Dashboard with credit balance

### 2. Credit Packages
- [ ] Navigate to "Purchase Credits"
- [ ] Page loads without errors
- [ ] Shows 4 packages (Starter, Popular, Premium, Unlimited)
- [ ] Prices correct: S$9.99, S$19.99, S$34.99, S$59.99
- [ ] 📸 Screenshot: Credit packages page

### 3. Checkout Session
- [ ] Click "🛒 Purchase Starter Pack"
- [ ] Success message appears
- [ ] Checkout URL displayed
- [ ] URL starts with `https://checkout.stripe.com/c/pay/`
- [ ] Response time < 5 seconds
- [ ] 📸 Screenshot: Checkout URL displayed

### 4. Stripe Checkout Page
- [ ] Click checkout link
- [ ] Redirects to Stripe checkout
- [ ] Shows "WantAMock" or "MockExamify"
- [ ] Product: "Starter Pack"
- [ ] Price: S$9.99
- [ ] Description: "10 credits - Perfect for trying out our platform"
- [ ] Email pre-filled correctly
- [ ] Secure (https://)
- [ ] 📸 Screenshot: Stripe checkout page

### 5. Payment Decision
**Choose ONE:**

**Option A: Complete Payment (if authorized)**
- [ ] Enter real payment card
- [ ] Complete payment
- [ ] Redirects to success page
- [ ] Shows: "🎉 Payment successful!"
- [ ] Credits updated: 11 credits (1+10)
- [ ] Balloons animation
- [ ] 📸 Screenshot: Success page
- [ ] 📸 Screenshot: Updated credit balance

**Option B: Inspection Only**
- [ ] Review checkout page thoroughly
- [ ] Close without payment
- [ ] Return to app manually
- [ ] App continues to work
- [ ] Credits unchanged (still 1)

### 6. Cancellation Test
- [ ] Create another checkout session
- [ ] Click checkout link
- [ ] Close Stripe page immediately
- [ ] Return to app
- [ ] App works normally
- [ ] No error state

---

## Stripe Dashboard Audit (dashboard.stripe.com)

### 7. Login
- [ ] Go to https://dashboard.stripe.com
- [ ] Sign in with Google
- [ ] Dashboard loads successfully
- [ ] Switch to "Live mode" (toggle top-right)

### 8. Account Activation
- [ ] No "Activate your account" warnings
- [ ] Settings → Business settings → Business details
- [ ] Business name: ✅ Set
- [ ] Business type: ✅ Selected
- [ ] Country: ✅ Set
- [ ] Support phone: ✅ Set
- [ ] Website: ✅ https://wantamock.streamlit.app
- [ ] 📸 Screenshot: Business details (mask sensitive info)

### 9. Bank Account ⚠️ CRITICAL
- [ ] Settings → Bank accounts and scheduling
- [ ] Bank account connected: ✅ YES / ❌ NO
- [ ] If NO: **FLAG AS CRITICAL - Cannot receive payments!**
- [ ] If YES: Status shows "Active" or "Verified"
- [ ] Payout schedule: Daily/Weekly/Monthly
- [ ] 📸 Screenshot: Bank account status (mask account number)

### 10. API Keys
- [ ] Developers → API keys
- [ ] In "Live mode"
- [ ] Publishable key: `pk_live_51S1Oq...`
- [ ] Secret key: `sk_live_51S1Oq...` (partially hidden)
- [ ] ⚠️ DO NOT copy or screenshot full secret key

### 11. Payment Methods
- [ ] Settings → Payment methods
- [ ] Credit cards enabled (Visa, Mastercard, Amex)
- [ ] Note other enabled methods: _________________
- [ ] 📸 Screenshot: Payment methods

### 12. Webhooks
- [ ] Developers → Webhooks
- [ ] Check configuration:

**If webhook exists:**
- [ ] Endpoint URL: `https://wantamock.streamlit.app/api/stripe/webhook`
- [ ] Status: Enabled
- [ ] Events: `checkout.session.completed`
- [ ] 📸 Screenshot: Webhook config

**If no webhook:**
- [ ] Note: "No webhooks configured (expected)"
- [ ] This is OK - app uses redirect verification

### 13. Payment Record (if payment completed)
- [ ] Payments → Filter by today
- [ ] Find test payment
- [ ] Amount: S$9.99
- [ ] Status: Succeeded
- [ ] Customer email matches
- [ ] Click payment → View metadata
- [ ] Metadata contains:
  - [ ] `user_id`: Test user ID
  - [ ] `package_key`: "starter"
  - [ ] `credits`: "10"
  - [ ] `app_name`: "MockExamify"
- [ ] 📸 Screenshot: Payment record
- [ ] 📸 Screenshot: Payment metadata

### 14. Products
- [ ] Products
- [ ] Note: Products may be dynamically created
- [ ] 📸 Screenshot: Products page

---

## Test Report

### Summary Checklist
- [ ] All application tests completed
- [ ] All dashboard audits completed
- [ ] All screenshots collected
- [ ] Issues documented

### Critical Issues Found
```
[ ] None
[ ] Bank account not connected (CRITICAL)
[ ] API keys missing
[ ] Other: ___________________
```

### Major Issues Found
```
[ ] None
[ ] Issue: ___________________
```

### Minor Issues Found
```
[ ] None
[ ] Issue: ___________________
```

### Overall Assessment
```
[ ] ✅ Production Ready - No issues found
[ ] ⚠️ Production Ready - With minor issues (list above)
[ ] ❌ NOT Production Ready - Critical issues must be fixed
```

### Recommendations
```
1. ___________________________________
2. ___________________________________
3. ___________________________________
```

---

## Test Completion

**Test Date**: _______________
**Tested By**: _______________
**Payment Completed**: YES / NO
**Transaction ID** (if applicable): _______________
**Test Account Email**: _______________
**Test Duration**: ___________ minutes

**Sign-off**:
- [ ] Report complete
- [ ] Screenshots attached
- [ ] Issues documented
- [ ] Recommendations provided
- [ ] Test account credentials saved securely

---

## Quick Status Indicators

Use these for your report:

| Status | Meaning |
|--------|---------|
| ✅ | Pass / Working / Complete |
| ⚠️ | Warning / Partial / Needs Attention |
| ❌ | Fail / Missing / Critical Issue |
| ⏭️ | Skipped / Not Applicable |
| 📸 | Screenshot Required |

---

## Next Steps After Testing

If all tests pass:
1. ✅ Production is ready for real customers
2. Share test results with stakeholders
3. Monitor first real customer payment closely
4. Set up payment monitoring/alerts

If issues found:
1. Fix critical issues immediately
2. Re-test after fixes
3. Document all changes
4. Schedule follow-up testing

---

**READY TO BEGIN TESTING**
