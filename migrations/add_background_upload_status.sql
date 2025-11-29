-- Create background_upload_status table for tracking background OCR uploads
CREATE TABLE IF NOT EXISTS background_upload_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pool_id UUID REFERENCES question_pools(id) ON DELETE CASCADE,
    pool_name TEXT NOT NULL,
    filename TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
    total_pages INTEGER,
    current_page INTEGER,
    questions_found INTEGER,
    valid_questions INTEGER,
    healed_count INTEGER DEFAULT 0,
    skipped_count INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Create index for faster queries by pool_id
CREATE INDEX IF NOT EXISTS idx_background_upload_status_pool_id ON background_upload_status(pool_id);

-- Create index for faster queries by status
CREATE INDEX IF NOT EXISTS idx_background_upload_status_status ON background_upload_status(status);

-- Create index for faster queries by started_at (to get latest)
CREATE INDEX IF NOT EXISTS idx_background_upload_status_started_at ON background_upload_status(started_at DESC);

-- Enable RLS
ALTER TABLE background_upload_status ENABLE ROW LEVEL SECURITY;

-- Policy: Admins can do everything
CREATE POLICY "Admins can manage background upload status"
ON background_upload_status
FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM users
        WHERE users.id = auth.uid()
        AND users.role = 'admin'
    )
);

-- Policy: Service role can do everything (for background processor)
CREATE POLICY "Service role can manage background upload status"
ON background_upload_status
FOR ALL
TO service_role
USING (true);

COMMENT ON TABLE background_upload_status IS 'Tracks status of background OCR upload processes';
COMMENT ON COLUMN background_upload_status.status IS 'Current status: running, completed, or failed';
COMMENT ON COLUMN background_upload_status.total_pages IS 'Total number of pages to process';
COMMENT ON COLUMN background_upload_status.current_page IS 'Current page being processed';
COMMENT ON COLUMN background_upload_status.healed_count IS 'Number of questions healed by AI';
COMMENT ON COLUMN background_upload_status.skipped_count IS 'Number of questions skipped (invalid or incomplete)';
