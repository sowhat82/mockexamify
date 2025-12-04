-- Create reported_questions table to track user-reported corrupted/impossible questions

CREATE TABLE IF NOT EXISTS reported_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES pool_questions(id) ON DELETE CASCADE,
    reported_by UUID REFERENCES users(id) ON DELETE SET NULL,
    mock_id UUID,  -- Optional: track which mock attempt this was from
    report_reason TEXT,  -- Optional reason provided by user
    reported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'resolved', 'dismissed')),
    admin_notes TEXT,  -- Admin can add notes when reviewing
    reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes for faster querying
CREATE INDEX IF NOT EXISTS idx_reported_questions_question_id ON reported_questions(question_id);
CREATE INDEX IF NOT EXISTS idx_reported_questions_status ON reported_questions(status);
CREATE INDEX IF NOT EXISTS idx_reported_questions_reported_at ON reported_questions(reported_at DESC);

-- RLS Policies
ALTER TABLE reported_questions ENABLE ROW LEVEL SECURITY;

-- Users can insert their own reports
CREATE POLICY "Users can report questions"
    ON reported_questions
    FOR INSERT
    TO authenticated
    WITH CHECK (reported_by = auth.uid());

-- Users can view their own reports
CREATE POLICY "Users can view their own reports"
    ON reported_questions
    FOR SELECT
    TO authenticated
    USING (reported_by = auth.uid());

-- Admins can view all reports
CREATE POLICY "Admins can view all reports"
    ON reported_questions
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.id = auth.uid()
            AND users.role = 'admin'
        )
    );

-- Admins can update reports (review, add notes, change status)
CREATE POLICY "Admins can update reports"
    ON reported_questions
    FOR UPDATE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.id = auth.uid()
            AND users.role = 'admin'
        )
    );

-- Create a view for admin dashboard with question details
CREATE OR REPLACE VIEW reported_questions_with_details AS
SELECT
    rq.*,
    pq.question_text,
    pq.choices,
    pq.correct_answer,
    pq.pool_id,
    qp.pool_name,
    u.email as reporter_email
FROM reported_questions rq
LEFT JOIN pool_questions pq ON rq.question_id = pq.id
LEFT JOIN question_pools qp ON pq.pool_id = qp.id
LEFT JOIN users u ON rq.reported_by = u.id
ORDER BY rq.reported_at DESC;

-- Grant access to the view for authenticated users
GRANT SELECT ON reported_questions_with_details TO authenticated;
