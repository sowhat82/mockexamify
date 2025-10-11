-- MockExamify Comprehensive Database Schema
-- Copy and paste this into Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    credits_balance INTEGER DEFAULT 0,
    role VARCHAR(50) DEFAULT 'user',
    subscription_status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Mocks table
CREATE TABLE IF NOT EXISTS mocks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    questions_json JSONB NOT NULL,
    price_credits INTEGER DEFAULT 1,
    explanation_enabled BOOLEAN DEFAULT TRUE,
    time_limit_minutes INTEGER DEFAULT 60,
    category VARCHAR(100) DEFAULT 'General',
    difficulty VARCHAR(20) DEFAULT 'medium',
    is_active BOOLEAN DEFAULT TRUE,
    creator_id UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Separate questions table for better normalization
CREATE TABLE IF NOT EXISTS questions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    mock_id UUID NOT NULL REFERENCES mocks(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    choices JSONB NOT NULL,
    correct_index INTEGER NOT NULL,
    explanation TEXT,
    explanation_seed TEXT,
    category VARCHAR(100),
    difficulty VARCHAR(20) DEFAULT 'medium',
    scenario TEXT,
    variant_of UUID REFERENCES questions(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Attempts table
CREATE TABLE IF NOT EXISTS attempts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    mock_id UUID NOT NULL REFERENCES mocks(id),
    user_answers JSONB NOT NULL,
    score DECIMAL(5,2) NOT NULL,
    correct_answers INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    explanations_unlocked BOOLEAN DEFAULT FALSE,
    time_taken INTEGER, -- in seconds
    status VARCHAR(20) DEFAULT 'completed', -- in_progress, completed, abandoned
    detailed_results JSONB,
    pdf_url TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Support tickets table
CREATE TABLE IF NOT EXISTS support_tickets (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    browser VARCHAR(100),
    device VARCHAR(100),
    error_message TEXT,
    affected_exam VARCHAR(255),
    status VARCHAR(50) DEFAULT 'open', -- open, resolved, closed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Payments table for Stripe integration
CREATE TABLE IF NOT EXISTS payments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    stripe_session_id VARCHAR(255) UNIQUE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    credits_purchased INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, completed, failed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Explanations table for AI-generated explanations
CREATE TABLE IF NOT EXISTS explanations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    explanation TEXT NOT NULL,
    confidence DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Keep legacy tickets table for backward compatibility
CREATE TABLE IF NOT EXISTS tickets (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL,
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'open',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

CREATE INDEX IF NOT EXISTS idx_mocks_category ON mocks(category);
CREATE INDEX IF NOT EXISTS idx_mocks_active ON mocks(is_active);
CREATE INDEX IF NOT EXISTS idx_mocks_difficulty ON mocks(difficulty);
CREATE INDEX IF NOT EXISTS idx_mocks_creator ON mocks(creator_id);

CREATE INDEX IF NOT EXISTS idx_questions_mock_id ON questions(mock_id);
CREATE INDEX IF NOT EXISTS idx_questions_category ON questions(category);
CREATE INDEX IF NOT EXISTS idx_questions_variant_of ON questions(variant_of);

CREATE INDEX IF NOT EXISTS idx_attempts_user_id ON attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_attempts_mock_id ON attempts(mock_id);
CREATE INDEX IF NOT EXISTS idx_attempts_status ON attempts(status);
CREATE INDEX IF NOT EXISTS idx_attempts_created_at ON attempts(created_at);

CREATE INDEX IF NOT EXISTS idx_support_tickets_user_id ON support_tickets(user_id);
CREATE INDEX IF NOT EXISTS idx_support_tickets_status ON support_tickets(status);
CREATE INDEX IF NOT EXISTS idx_support_tickets_created_at ON support_tickets(created_at);

CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_stripe_session ON payments(stripe_session_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);

CREATE INDEX IF NOT EXISTS idx_explanations_question_id ON explanations(question_id);

-- Legacy indexes
CREATE INDEX IF NOT EXISTS idx_tickets_user_id ON tickets(user_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);

-- Row Level Security (RLS) policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE mocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE support_tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE explanations ENABLE ROW LEVEL SECURITY;

-- Users can view and update their own data
CREATE POLICY "Users can view own data" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own data" ON users FOR UPDATE USING (auth.uid() = id);

-- Mocks are publicly viewable, but only admins can create/edit
CREATE POLICY "Mocks are viewable by everyone" ON mocks FOR SELECT USING (is_active = true);
CREATE POLICY "Only admins can create mocks" ON mocks FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
);
CREATE POLICY "Only admins can update mocks" ON mocks FOR UPDATE USING (
    EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
);

-- Questions follow mock permissions
CREATE POLICY "Questions are viewable with mocks" ON questions FOR SELECT USING (
    EXISTS (SELECT 1 FROM mocks WHERE id = mock_id AND is_active = true)
);
CREATE POLICY "Only admins can create questions" ON questions FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
);

-- Users can view their own attempts
CREATE POLICY "Users can view own attempts" ON attempts FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create attempts" ON attempts FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own attempts" ON attempts FOR UPDATE USING (auth.uid() = user_id);

-- Users can view their own tickets
CREATE POLICY "Users can view own tickets" ON support_tickets FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create tickets" ON support_tickets FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Admins can view all tickets" ON support_tickets FOR SELECT USING (
    EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
);
CREATE POLICY "Admins can update tickets" ON support_tickets FOR UPDATE USING (
    EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
);

-- Users can view their own payments
CREATE POLICY "Users can view own payments" ON payments FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "System can create payments" ON payments FOR INSERT WITH CHECK (true);
CREATE POLICY "System can update payments" ON payments FOR UPDATE USING (true);

-- Explanations are viewable by everyone
CREATE POLICY "Explanations are viewable by everyone" ON explanations FOR SELECT USING (true);
CREATE POLICY "Only system can create explanations" ON explanations FOR INSERT WITH CHECK (true);

-- Functions for automatic updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_mocks_updated_at BEFORE UPDATE ON mocks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_support_tickets_updated_at BEFORE UPDATE ON support_tickets 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tickets_updated_at BEFORE UPDATE ON tickets 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create default admin user (password: admin123)
-- Note: In production, change this password immediately
INSERT INTO users (id, email, password_hash, credits_balance, role) 
VALUES (
    gen_random_uuid(),
    'admin@mockexamify.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBCBdSLDqn0Xc2', -- admin123
    1000,
    'admin'
) ON CONFLICT (email) DO NOTHING;

-- Insert sample mock data
INSERT INTO mocks (title, description, questions_json, price_credits, category, difficulty) VALUES
(
    'Sample Programming Quiz',
    'A basic programming knowledge test covering fundamental concepts.',
    '[
        {
            "question": "What is the output of print(2 + 2)?",
            "choices": ["2", "4", "22", "Error"],
            "correct_index": 1,
            "explanation": "The + operator performs arithmetic addition on numbers."
        },
        {
            "question": "Which of the following is a valid Python variable name?",
            "choices": ["2var", "var-name", "var_name", "var name"],
            "correct_index": 2,
            "explanation": "Python variables can contain letters, numbers, and underscores, but cannot start with a number or contain spaces or hyphens."
        }
    ]',
    1,
    'Programming',
    'easy'
) ON CONFLICT DO NOTHING;