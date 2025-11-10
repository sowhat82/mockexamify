-- Add responses column to tickets table
-- This column stores an array of response objects as JSONB
-- Each response has: responder (string), message (string), created_at (timestamp)

-- Add the responses column if it doesn't exist
ALTER TABLE public.tickets
ADD COLUMN IF NOT EXISTS responses JSONB DEFAULT '[]'::jsonb;

-- Add an index for better performance when querying responses
CREATE INDEX IF NOT EXISTS idx_tickets_responses ON public.tickets USING GIN (responses);

-- Update existing tickets to have empty array if NULL
UPDATE public.tickets
SET responses = '[]'::jsonb
WHERE responses IS NULL;

-- Verify the column was added
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'tickets'
AND column_name = 'responses';
