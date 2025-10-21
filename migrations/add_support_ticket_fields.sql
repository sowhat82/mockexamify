-- Migration: add optional fields to support_tickets

ALTER TABLE support_tickets
    ADD COLUMN IF NOT EXISTS user_email VARCHAR(255);

ALTER TABLE support_tickets
    ADD COLUMN IF NOT EXISTS priority VARCHAR(20) DEFAULT 'Medium';

ALTER TABLE support_tickets
    ADD COLUMN IF NOT EXISTS category VARCHAR(100) DEFAULT 'Other';

ALTER TABLE support_tickets
    ADD COLUMN IF NOT EXISTS attachment_url TEXT;

-- Responses stored as JSONB array on support_tickets for simple use-case
ALTER TABLE support_tickets
    ADD COLUMN IF NOT EXISTS responses JSONB DEFAULT '[]'::jsonb;

-- Ensure default indexes exist for faster searches on priority/category
CREATE INDEX IF NOT EXISTS idx_support_tickets_priority ON support_tickets(priority);
CREATE INDEX IF NOT EXISTS idx_support_tickets_category ON support_tickets(category);
