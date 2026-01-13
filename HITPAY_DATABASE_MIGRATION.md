# HitPay Database Migration

## Required Database Changes

To support HitPay (PayNow) payments, you need to add new columns to the `payments` table in Supabase.

### SQL Migration Script

Run this SQL in your Supabase SQL Editor:

```sql
-- Add HitPay payment support to payments table
ALTER TABLE payments
ADD COLUMN IF NOT EXISTS hitpay_payment_id TEXT,
ADD COLUMN IF NOT EXISTS payment_method TEXT DEFAULT 'stripe';

-- Add index for HitPay payment ID lookups
CREATE INDEX IF NOT EXISTS idx_payments_hitpay_id
ON payments(hitpay_payment_id);

-- Add comment for documentation
COMMENT ON COLUMN payments.hitpay_payment_id IS 'HitPay payment request ID for PayNow payments';
COMMENT ON COLUMN payments.payment_method IS 'Payment method used: stripe, paynow, etc.';

-- Update existing records to have payment_method = 'stripe'
UPDATE payments
SET payment_method = 'stripe'
WHERE payment_method IS NULL AND stripe_session_id IS NOT NULL;
```

### Verification

After running the migration, verify it worked:

```sql
-- Check columns exist
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'payments'
AND column_name IN ('hitpay_payment_id', 'payment_method');

-- Should return 2 rows showing the new columns
```

### Rollback (if needed)

If you need to rollback the changes:

```sql
-- Remove HitPay columns
ALTER TABLE payments
DROP COLUMN IF EXISTS hitpay_payment_id,
DROP COLUMN IF EXISTS payment_method;

-- Drop index
DROP INDEX IF EXISTS idx_payments_hitpay_id;
```

## Notes

- The `hitpay_payment_id` column stores the HitPay payment request ID
- The `payment_method` column distinguishes between 'stripe' and 'paynow' payments
- Existing Stripe payments will be marked with `payment_method = 'stripe'`
- Both columns are nullable to maintain backward compatibility
- The index on `hitpay_payment_id` ensures fast lookups during webhook processing

## Testing

After migration, test by:
1. Creating a test PayNow payment (if HitPay is enabled)
2. Checking the payments table to see if the record is created correctly
3. Verifying the webhook can find the payment by `hitpay_payment_id`
