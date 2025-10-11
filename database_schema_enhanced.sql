-- MockExamify Enhanced Database Schema for Production Demo MVP
-- Supporting IBF CACS 2 and CMFAS CM-SIP exam categories

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Exam Categories
CREATE TABLE IF NOT EXISTS exam_categories (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE CHECK (code IN ('CACS2', 'CMSIP')),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Topics (hierarchical structure)
CREATE TABLE IF NOT EXISTS topics (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    category_id UUID NOT NULL REFERENCES exam_categories(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    parent_topic_id UUID REFERENCES topics(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(category_id, code)
);

-- Mock Papers/Exams
CREATE TABLE IF NOT EXISTS mocks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    category_id UUID NOT NULL REFERENCES exam_categories(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    difficulty VARCHAR(10) NOT NULL CHECK (difficulty IN ('easy', 'medium', 'hard')),
    time_limit_minutes INTEGER NOT NULL DEFAULT 60,
    credits_cost INTEGER NOT NULL DEFAULT 1,
    active BOOLEAN NOT NULL DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Questions Bank
CREATE TABLE IF NOT EXISTS questions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    category_id UUID NOT NULL REFERENCES exam_categories(id) ON DELETE CASCADE,
    source VARCHAR(20) NOT NULL CHECK (source IN ('uploaded', 'ai_generated')),
    stem TEXT NOT NULL,
    choices JSONB NOT NULL, -- Array of choice objects: [{"text": "Choice A", "label": "A"}, ...]
    correct_index INTEGER NOT NULL CHECK (correct_index >= 0 AND correct_index < 4),
    explanation TEXT,
    scenario TEXT, -- Optional scenario/case study context
    difficulty VARCHAR(10) NOT NULL CHECK (difficulty IN ('easy', 'medium', 'hard')),
    primary_topic_id UUID REFERENCES topics(id),
    extra_topic_ids JSONB DEFAULT '[]'::jsonb, -- Array of additional topic UUIDs
    tags JSONB DEFAULT '[]'::jsonb, -- Array of tag strings
    source_doc_id UUID, -- Reference to uploads table
    variant_of_question_id UUID REFERENCES questions(id), -- For generated variants
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Papers (collections of questions)
CREATE TABLE IF NOT EXISTS papers (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    category_id UUID NOT NULL REFERENCES exam_categories(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    mode VARCHAR(10) NOT NULL CHECK (mode IN ('static', 'generated')),
    time_limit_minutes INTEGER NOT NULL DEFAULT 60,
    num_questions INTEGER NOT NULL DEFAULT 20,
    difficulty_mix JSONB DEFAULT '{"easy": 0.3, "medium": 0.5, "hard": 0.2}'::jsonb,
    topic_coverage JSONB DEFAULT '{}'::jsonb, -- Topic weights for generated papers
    active BOOLEAN NOT NULL DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Paper-Question relationships (for static papers)
CREATE TABLE IF NOT EXISTS paper_questions (
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL,
    PRIMARY KEY (paper_id, question_id),
    UNIQUE(paper_id, sequence_number)
);

-- File Uploads
CREATE TABLE IF NOT EXISTS uploads (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    category_id UUID NOT NULL REFERENCES exam_categories(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(10) NOT NULL CHECK (file_type IN ('pdf', 'docx', 'csv', 'json')),
    storage_url TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'parsed', 'failed')),
    parsed_summary JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Syllabus Documents
CREATE TABLE IF NOT EXISTS syllabus_docs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    category_id UUID NOT NULL REFERENCES exam_categories(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(10) NOT NULL CHECK (file_type IN ('pdf', 'docx', 'txt')),
    storage_url TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('indexed', 'failed', 'pending')),
    chunk_count INTEGER DEFAULT 0,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Syllabus Chunks (for AI context)
CREATE TABLE IF NOT EXISTS syllabus_chunks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    syllabus_doc_id UUID NOT NULL REFERENCES syllabus_docs(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    topic_guess VARCHAR(100), -- AI-guessed topic for this chunk
    token_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enhanced Attempts table
DROP TABLE IF EXISTS attempts CASCADE;
CREATE TABLE attempts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    mock_id UUID REFERENCES mocks(id), -- For backward compatibility
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    submitted_at TIMESTAMP WITH TIME ZONE,
    score FLOAT CHECK (score >= 0 AND score <= 100),
    time_seconds INTEGER,
    explanations_unlocked BOOLEAN NOT NULL DEFAULT false,
    pdf_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Detailed answer tracking
CREATE TABLE IF NOT EXISTS attempt_answers (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    attempt_id UUID NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    selected_index INTEGER CHECK (selected_index >= 0 AND selected_index < 4),
    is_correct BOOLEAN NOT NULL DEFAULT false,
    time_spent_seconds INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(attempt_id, question_id)
);

-- User Mastery Tracking
CREATE TABLE IF NOT EXISTS user_mastery (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    total_answered INTEGER NOT NULL DEFAULT 0,
    total_correct INTEGER NOT NULL DEFAULT 0,
    current_streak INTEGER NOT NULL DEFAULT 0,
    best_streak INTEGER NOT NULL DEFAULT 0,
    mastery_score FLOAT GENERATED ALWAYS AS (
        CASE 
            WHEN total_answered = 0 THEN 0
            ELSE (total_correct::float / total_answered::float) * 100
        END
    ) STORED,
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, topic_id)
);

-- Credits Ledger
CREATE TABLE IF NOT EXISTS credits_ledger (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    delta INTEGER NOT NULL, -- Positive for credits added, negative for credits spent
    reason VARCHAR(20) NOT NULL CHECK (reason IN ('purchase', 'exam', 'explanations', 'adjustment', 'signup_bonus')),
    meta JSONB DEFAULT '{}'::jsonb, -- Additional metadata (payment_id, exam_id, etc.)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enhanced tickets table (if not exists)
CREATE TABLE IF NOT EXISTS tickets (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    priority VARCHAR(10) NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    assigned_to UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add helpful indices
CREATE INDEX IF NOT EXISTS idx_questions_category_id ON questions(category_id);
CREATE INDEX IF NOT EXISTS idx_questions_primary_topic_id ON questions(primary_topic_id);
CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_questions_source ON questions(source);
CREATE INDEX IF NOT EXISTS idx_questions_active ON questions(active);

CREATE INDEX IF NOT EXISTS idx_papers_category_id ON papers(category_id);
CREATE INDEX IF NOT EXISTS idx_papers_active ON papers(active);

CREATE INDEX IF NOT EXISTS idx_attempts_user_id ON attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_attempts_paper_id ON attempts(paper_id);
CREATE INDEX IF NOT EXISTS idx_attempts_submitted_at ON attempts(submitted_at);

CREATE INDEX IF NOT EXISTS idx_attempt_answers_attempt_id ON attempt_answers(attempt_id);
CREATE INDEX IF NOT EXISTS idx_attempt_answers_question_id ON attempt_answers(question_id);

CREATE INDEX IF NOT EXISTS idx_user_mastery_user_id ON user_mastery(user_id);
CREATE INDEX IF NOT EXISTS idx_user_mastery_topic_id ON user_mastery(topic_id);
CREATE INDEX IF NOT EXISTS idx_user_mastery_score ON user_mastery(mastery_score);

CREATE INDEX IF NOT EXISTS idx_credits_ledger_user_id ON credits_ledger(user_id);
CREATE INDEX IF NOT EXISTS idx_credits_ledger_created_at ON credits_ledger(created_at);

CREATE INDEX IF NOT EXISTS idx_syllabus_chunks_doc_id ON syllabus_chunks(syllabus_doc_id);
CREATE INDEX IF NOT EXISTS idx_topics_category_id ON topics(category_id);
CREATE INDEX IF NOT EXISTS idx_topics_parent_topic_id ON topics(parent_topic_id);

-- Update triggers for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tickets_updated_at BEFORE UPDATE ON tickets 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert seed data for exam categories
INSERT INTO exam_categories (code, name, description) VALUES 
    ('CACS2', 'IBF CACS Level 2', 'Capital Markets and Financial Advisory Services Level 2')
ON CONFLICT (code) DO NOTHING;

INSERT INTO exam_categories (code, name, description) VALUES 
    ('CMSIP', 'CMFAS CM-SIP', 'Capital Markets and Financial Advisory Services - Securities Investment Products')
ON CONFLICT (code) DO NOTHING;

-- Seed topics for CACS2
INSERT INTO topics (category_id, code, name, description) 
SELECT c.id, 'RISK_MGMT', 'Risk Management', 'Portfolio risk assessment and management techniques'
FROM exam_categories c WHERE c.code = 'CACS2'
ON CONFLICT (category_id, code) DO NOTHING;

INSERT INTO topics (category_id, code, name, description) 
SELECT c.id, 'PORTFOLIO', 'Portfolio Management', 'Asset allocation and portfolio construction'
FROM exam_categories c WHERE c.code = 'CACS2'
ON CONFLICT (category_id, code) DO NOTHING;

INSERT INTO topics (category_id, code, name, description) 
SELECT c.id, 'DERIVATIVES', 'Derivatives', 'Options, futures, and structured products'
FROM exam_categories c WHERE c.code = 'CACS2'
ON CONFLICT (category_id, code) DO NOTHING;

INSERT INTO topics (category_id, code, name, description) 
SELECT c.id, 'ETHICS', 'Professional Ethics', 'Code of conduct and regulatory compliance'
FROM exam_categories c WHERE c.code = 'CACS2'
ON CONFLICT (category_id, code) DO NOTHING;

-- Seed topics for CMSIP
INSERT INTO topics (category_id, code, name, description) 
SELECT c.id, 'SECURITIES', 'Securities Markets', 'Equity and debt securities fundamentals'
FROM exam_categories c WHERE c.code = 'CMSIP'
ON CONFLICT (category_id, code) DO NOTHING;

INSERT INTO topics (category_id, code, name, description) 
SELECT c.id, 'ANALYSIS', 'Investment Analysis', 'Fundamental and technical analysis methods'
FROM exam_categories c WHERE c.code = 'CMSIP'
ON CONFLICT (category_id, code) DO NOTHING;

INSERT INTO topics (category_id, code, name, description) 
SELECT c.id, 'REGULATIONS', 'Market Regulations', 'SFA and regulatory framework'
FROM exam_categories c WHERE c.code = 'CMSIP'
ON CONFLICT (category_id, code) DO NOTHING;

INSERT INTO topics (category_id, code, name, description) 
SELECT c.id, 'PRODUCTS', 'Investment Products', 'REITs, ETFs, and structured products'
FROM exam_categories c WHERE c.code = 'CMSIP'
ON CONFLICT (category_id, code) DO NOTHING;