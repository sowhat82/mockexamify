-- Fix security definer issue on reported_questions_with_details view
-- Change from SECURITY DEFINER (default in some cases) to SECURITY INVOKER
-- This ensures the view respects RLS policies of the querying user

-- Drop and recreate the view with explicit SECURITY INVOKER
DROP VIEW IF EXISTS reported_questions_with_details;

CREATE VIEW reported_questions_with_details
WITH (security_invoker = true)
AS
SELECT
    rq.id,
    rq.question_id,
    rq.reported_by,
    rq.mock_id,
    rq.report_reason,
    rq.reported_at,
    rq.status,
    rq.admin_notes,
    rq.reviewed_at,
    rq.reviewed_by,
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

-- Add comment explaining the security model
COMMENT ON VIEW reported_questions_with_details IS
'View combining reported questions with their details. Uses SECURITY INVOKER to respect RLS policies of the querying user. Admins should use service role to bypass RLS when needed.';
