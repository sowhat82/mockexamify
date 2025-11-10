-- Fix tickets table schema to match application requirements
-- Adds missing columns needed for support ticket functionality

-- Add responses column (JSONB array for storing ticket responses)
ALTER TABLE public.tickets
ADD COLUMN IF NOT EXISTS responses JSONB DEFAULT '[]'::jsonb;

-- Add description column (some tickets use 'description' instead of 'message')
ALTER TABLE public.tickets
ADD COLUMN IF NOT EXISTS description TEXT;

-- Add user_email column for quick reference
ALTER TABLE public.tickets
ADD COLUMN IF NOT EXISTS user_email VARCHAR(255);

-- Add category column
ALTER TABLE public.tickets
ADD COLUMN IF NOT EXISTS category VARCHAR(100) DEFAULT 'General';

-- Add priority column
ALTER TABLE public.tickets
ADD COLUMN IF NOT EXISTS priority VARCHAR(50) DEFAULT 'Medium';

-- Add browser column for technical details
ALTER TABLE public.tickets
ADD COLUMN IF NOT EXISTS browser VARCHAR(255);

-- Add device column for technical details
ALTER TABLE public.tickets
ADD COLUMN IF NOT EXISTS device VARCHAR(255);

-- Add error_message column for technical details
ALTER TABLE public.tickets
ADD COLUMN IF NOT EXISTS error_message TEXT;

-- Add affected_exam column
ALTER TABLE public.tickets
ADD COLUMN IF NOT EXISTS affected_exam VARCHAR(255);

-- Add email_updates column
ALTER TABLE public.tickets
ADD COLUMN IF NOT EXISTS email_updates BOOLEAN DEFAULT true;

-- Add attachment_url column
ALTER TABLE public.tickets
ADD COLUMN IF NOT EXISTS attachment_url TEXT;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_tickets_responses ON public.tickets USING GIN (responses);
CREATE INDEX IF NOT EXISTS idx_tickets_category ON public.tickets(category);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON public.tickets(priority);
CREATE INDEX IF NOT EXISTS idx_tickets_user_email ON public.tickets(user_email);

-- Update existing tickets to have empty array for responses if NULL
UPDATE public.tickets
SET responses = '[]'::jsonb
WHERE responses IS NULL;

-- Verify the columns were added
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'tickets'
ORDER BY ordinal_position;
