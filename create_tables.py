"""
Create database tables in Supabase via SQL
Run this to set up the database schema
"""
import asyncio
from supabase import create_client
import config

async def create_tables():
    """Create all necessary tables in Supabase"""
    
    # Initialize Supabase client
    supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    
    print("🔧 Creating database tables in Supabase...")
    
    # SQL to create all tables
    create_tables_sql = """
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
        time_limit_minutes INTEGER DEFAULT 30,
        category VARCHAR(100) DEFAULT 'General',
        is_active BOOLEAN DEFAULT TRUE,
        creator_id UUID,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Attempts table
    CREATE TABLE IF NOT EXISTS attempts (
        id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
        user_id UUID NOT NULL,
        mock_id UUID NOT NULL,
        user_answers_json JSONB NOT NULL,
        score DECIMAL(5,2) NOT NULL,
        correct_answers INTEGER NOT NULL,
        total_questions INTEGER NOT NULL,
        explanation_unlocked BOOLEAN DEFAULT FALSE,
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Support tickets table
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
    CREATE INDEX IF NOT EXISTS idx_mocks_category ON mocks(category);
    CREATE INDEX IF NOT EXISTS idx_mocks_active ON mocks(is_active);
    CREATE INDEX IF NOT EXISTS idx_attempts_user_id ON attempts(user_id);
    CREATE INDEX IF NOT EXISTS idx_attempts_mock_id ON attempts(mock_id);
    CREATE INDEX IF NOT EXISTS idx_tickets_user_id ON tickets(user_id);
    CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
    """
    
    try:
        # Execute SQL to create tables
        result = supabase.rpc('exec_sql', {'sql': create_tables_sql}).execute()
        print("✅ Tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        print("\n📋 Please run this SQL manually in your Supabase SQL Editor:")
        print(create_tables_sql)
        return False

if __name__ == "__main__":
    asyncio.run(create_tables())