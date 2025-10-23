-- Add fields for pro-rata refund tracking to attempts table
-- Run this migration to support pro-rata refunds for incomplete exams

-- Add credits_paid column to track how much was paid for the attempt
ALTER TABLE attempts
ADD COLUMN IF NOT EXISTS credits_paid INTEGER DEFAULT 0;

-- Add questions_submitted column to track progress for pro-rata calculation
ALTER TABLE attempts
ADD COLUMN IF NOT EXISTS questions_submitted INTEGER DEFAULT 0;

-- Add helpful comment
COMMENT ON COLUMN attempts.credits_paid IS 'Number of credits paid for this attempt (for pro-rata refunds)';
COMMENT ON COLUMN attempts.questions_submitted IS 'Number of questions submitted so far (for progress tracking)';
