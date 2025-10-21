-- Question Pool System Schema Enhancement
-- Add these tables to your existing Supabase database

-- Question Pools table (one pool per topic, e.g., "CACS2 Paper 2")
CREATE TABLE IF NOT EXISTS question_pools (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    pool_name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    category VARCHAR(100),
    total_questions INTEGER DEFAULT 0,
    unique_questions INTEGER DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE
);

-- Individual Questions table (normalized storage)
CREATE TABLE IF NOT EXISTS pool_questions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    pool_id UUID REFERENCES question_pools(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    choices JSONB NOT NULL, -- Array of answer choices
    correct_answer INTEGER NOT NULL, -- Index of correct answer
    explanation TEXT,
    difficulty VARCHAR(50) DEFAULT 'medium',
    topic_tags JSONB DEFAULT '[]'::jsonb, -- Array of topic tags

    -- Source tracking
    source_file VARCHAR(255), -- Original PDF filename
    upload_batch_id UUID, -- Groups questions from same upload
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Duplicate detection
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_of UUID REFERENCES pool_questions(id),
    similarity_score DECIMAL(5,2), -- AI similarity score (0-100)

    -- Metadata
    times_shown INTEGER DEFAULT 0,
    times_correct INTEGER DEFAULT 0,
    times_incorrect INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Upload Batches table (track each PDF upload)
CREATE TABLE IF NOT EXISTS upload_batches (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    pool_id UUID REFERENCES question_pools(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    questions_count INTEGER DEFAULT 0,
    duplicates_found INTEGER DEFAULT 0,
    unique_added INTEGER DEFAULT 0,
    upload_status VARCHAR(50) DEFAULT 'processing', -- processing, completed, failed
    error_message TEXT,
    uploaded_by UUID REFERENCES users(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Duplicate Detection Cache (AI comparisons are expensive, cache results)
CREATE TABLE IF NOT EXISTS duplicate_cache (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    question1_id UUID REFERENCES pool_questions(id) ON DELETE CASCADE,
    question2_id UUID REFERENCES pool_questions(id) ON DELETE CASCADE,
    similarity_score DECIMAL(5,2) NOT NULL,
    is_duplicate BOOLEAN NOT NULL,
    ai_reasoning TEXT, -- Why AI marked as duplicate/not
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(question1_id, question2_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_question_pools_name ON question_pools(pool_name);
CREATE INDEX IF NOT EXISTS idx_question_pools_category ON question_pools(category);
CREATE INDEX IF NOT EXISTS idx_question_pools_active ON question_pools(is_active);

CREATE INDEX IF NOT EXISTS idx_pool_questions_pool_id ON pool_questions(pool_id);
CREATE INDEX IF NOT EXISTS idx_pool_questions_batch ON pool_questions(upload_batch_id);
CREATE INDEX IF NOT EXISTS idx_pool_questions_duplicate ON pool_questions(is_duplicate);
CREATE INDEX IF NOT EXISTS idx_pool_questions_source ON pool_questions(source_file);

CREATE INDEX IF NOT EXISTS idx_upload_batches_pool ON upload_batches(pool_id);
CREATE INDEX IF NOT EXISTS idx_upload_batches_status ON upload_batches(upload_status);

CREATE INDEX IF NOT EXISTS idx_duplicate_cache_q1 ON duplicate_cache(question1_id);
CREATE INDEX IF NOT EXISTS idx_duplicate_cache_q2 ON duplicate_cache(question2_id);

-- Function to update pool statistics
CREATE OR REPLACE FUNCTION update_pool_stats(p_pool_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE question_pools
    SET
        total_questions = (
            SELECT COUNT(*)
            FROM pool_questions
            WHERE pool_id = p_pool_id
        ),
        unique_questions = (
            SELECT COUNT(*)
            FROM pool_questions
            WHERE pool_id = p_pool_id AND is_duplicate = FALSE
        ),
        last_updated = NOW()
    WHERE id = p_pool_id;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update pool stats when questions change
CREATE OR REPLACE FUNCTION trigger_update_pool_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        PERFORM update_pool_stats(OLD.pool_id);
    ELSE
        PERFORM update_pool_stats(NEW.pool_id);
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER pool_questions_stats_trigger
AFTER INSERT OR UPDATE OR DELETE ON pool_questions
FOR EACH ROW EXECUTE FUNCTION trigger_update_pool_stats();

-- Comments for documentation
COMMENT ON TABLE question_pools IS 'Master table for question pools (e.g., "CACS2 Paper 2")';
COMMENT ON TABLE pool_questions IS 'Individual questions within each pool';
COMMENT ON TABLE upload_batches IS 'Tracks each PDF upload batch for audit trail';
COMMENT ON TABLE duplicate_cache IS 'Caches AI duplicate detection results to avoid re-processing';

COMMENT ON COLUMN pool_questions.similarity_score IS 'AI-calculated similarity (0-100). >95 = likely duplicate';
COMMENT ON COLUMN pool_questions.is_duplicate IS 'TRUE if question is duplicate of another';
COMMENT ON COLUMN pool_questions.duplicate_of IS 'References the original question if this is a duplicate';
