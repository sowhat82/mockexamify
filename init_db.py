"""
Database initialization and seed data for MockExamify
Run this script to set up the database tables and insert sample data
"""
import asyncio
import json
from datetime import datetime, timezone
from supabase import create_client
import config

# Sample data
SAMPLE_QUESTIONS = [
    {
        "question": "What is the output of the following Python code?\n```python\nprint(2 ** 3 ** 2)\n```",
        "choices": ["64", "512", "256", "128"],
        "correct_index": 1,
        "explanation_template": "The expression 2 ** 3 ** 2 is evaluated as 2 ** (3 ** 2) = 2 ** 9 = 512, due to right-to-left associativity of the exponentiation operator.",
        "category": "Python",
        "difficulty": "medium"
    },
    {
        "question": "Which of the following is NOT a valid Python data type?",
        "choices": ["list", "tuple", "array", "dictionary"],
        "correct_index": 2,
        "explanation_template": "While list, tuple, and dictionary are built-in Python data types, 'array' is not a built-in type. You need to import the array module or use lists instead.",
        "category": "Python",
        "difficulty": "easy"
    },
    {
        "question": "What is the time complexity of accessing an element in a Python dictionary?",
        "choices": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
        "correct_index": 0,
        "explanation_template": "Python dictionaries are implemented as hash tables, which provide O(1) average-case time complexity for access, insertion, and deletion operations.",
        "category": "Python",
        "difficulty": "medium"
    },
    {
        "question": "Which keyword is used to create a function in Python?",
        "choices": ["function", "def", "create", "func"],
        "correct_index": 1,
        "explanation_template": "The 'def' keyword is used to define functions in Python. The syntax is: def function_name(parameters):",
        "category": "Python",
        "difficulty": "easy"
    },
    {
        "question": "What will be the output of: bool([False])?",
        "choices": ["True", "False", "Error", "None"],
        "correct_index": 0,
        "explanation_template": "bool([False]) returns True because the list [False] is not empty. An empty list would return False, but a list containing any element (even False) is considered True.",
        "category": "Python",
        "difficulty": "medium"
    }
]

SAMPLE_MOCK = {
    "title": "Python Fundamentals Quiz",
    "description": "Test your knowledge of Python programming basics including syntax, data types, and basic operations.",
    "questions": SAMPLE_QUESTIONS,
    "price_credits": 1,
    "explanation_enabled": True,
    "time_limit_minutes": 30,
    "category": "Python Programming",
    "is_active": True
}

ADMIN_USER = {
    "email": "admin@mockexamify.com",
    "password": "admin123",  # Change this in production!
    "role": "admin"
}

SAMPLE_USER = {
    "email": "student@example.com", 
    "password": "password123",
    "role": "user"
}

# SQL statements for table creation
CREATE_TABLES_SQL = """
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
    time_limit_minutes INTEGER,
    category VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    creator_id UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Attempts table
CREATE TABLE IF NOT EXISTS attempts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES users(id) NOT NULL,
    mock_id UUID REFERENCES mocks(id) NOT NULL,
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
    user_id UUID REFERENCES users(id) NOT NULL,
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

-- Row Level Security (RLS) policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE mocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY users_own_data ON users FOR ALL USING (auth.uid() = id);

-- Mocks are publicly readable, but only admins can modify
CREATE POLICY mocks_public_read ON mocks FOR SELECT USING (true);
CREATE POLICY mocks_admin_write ON mocks FOR ALL USING (
    EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
);

-- Users can only see their own attempts
CREATE POLICY attempts_own_data ON attempts FOR ALL USING (auth.uid() = user_id);

-- Users can only see their own tickets
CREATE POLICY tickets_own_data ON tickets FOR ALL USING (auth.uid() = user_id);
"""

async def init_database():
    """Initialize database tables and insert seed data"""
    try:
        # Initialize Supabase client
        supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        
        print("🚀 Initializing MockExamify database...")
        
        # Note: Table creation should be done via Supabase dashboard or SQL editor
        # This is just for reference - the actual SQL should be run in Supabase
        print("📋 SQL for table creation:")
        print(CREATE_TABLES_SQL)
        print("\n⚠️  Please run the above SQL in your Supabase SQL editor to create tables.\n")
        
        # Check if we can connect to database
        try:
            result = supabase.table('users').select('id').limit(1).execute()
            print("✅ Database connection successful!")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("Please ensure tables are created in Supabase first.")
            return False
        
        # Create admin user
        print("👤 Creating admin user...")
        try:
            import bcrypt
            hashed_password = bcrypt.hashpw(ADMIN_USER['password'].encode('utf-8'), bcrypt.gensalt())
            
            admin_result = supabase.table('users').insert({
                'email': ADMIN_USER['email'],
                'password_hash': hashed_password.decode('utf-8'),
                'credits_balance': 100,  # Give admin some credits
                'role': ADMIN_USER['role'],
                'created_at': datetime.now(timezone.utc).isoformat()
            }).execute()
            
            if admin_result.data:
                admin_id = admin_result.data[0]['id']
                print(f"✅ Admin user created: {ADMIN_USER['email']}")
            else:
                print("⚠️  Admin user may already exist")
                # Try to get existing admin
                existing_admin = supabase.table('users').select('*').eq('email', ADMIN_USER['email']).execute()
                if existing_admin.data:
                    admin_id = existing_admin.data[0]['id']
                    print(f"✅ Using existing admin: {ADMIN_USER['email']}")
                else:
                    print("❌ Could not create or find admin user")
                    return False
                    
        except Exception as e:
            print(f"⚠️  Admin user creation error: {e}")
            # Try to get existing admin
            try:
                existing_admin = supabase.table('users').select('*').eq('email', ADMIN_USER['email']).execute()
                if existing_admin.data:
                    admin_id = existing_admin.data[0]['id']
                    print(f"✅ Using existing admin: {ADMIN_USER['email']}")
                else:
                    print("❌ Could not find admin user")
                    return False
            except:
                print("❌ Could not access admin user")
                return False
        
        # Create sample user
        print("👤 Creating sample user...")
        try:
            import bcrypt
            hashed_password = bcrypt.hashpw(SAMPLE_USER['password'].encode('utf-8'), bcrypt.gensalt())
            
            user_result = supabase.table('users').insert({
                'email': SAMPLE_USER['email'],
                'password_hash': hashed_password.decode('utf-8'),
                'credits_balance': 5,  # Give sample user some credits
                'role': SAMPLE_USER['role'],
                'created_at': datetime.now(timezone.utc).isoformat()
            }).execute()
            
            if user_result.data:
                print(f"✅ Sample user created: {SAMPLE_USER['email']}")
            else:
                print("⚠️  Sample user may already exist")
                
        except Exception as e:
            print(f"⚠️  Sample user creation error: {e}")
        
        # Create sample mock
        print("📝 Creating sample mock exam...")
        try:
            mock_result = supabase.table('mocks').insert({
                'title': SAMPLE_MOCK['title'],
                'description': SAMPLE_MOCK['description'],
                'questions_json': json.dumps(SAMPLE_MOCK['questions']),
                'price_credits': SAMPLE_MOCK['price_credits'],
                'explanation_enabled': SAMPLE_MOCK['explanation_enabled'],
                'time_limit_minutes': SAMPLE_MOCK['time_limit_minutes'],
                'category': SAMPLE_MOCK['category'],
                'is_active': SAMPLE_MOCK['is_active'],
                'creator_id': admin_id,
                'created_at': datetime.now(timezone.utc).isoformat()
            }).execute()
            
            if mock_result.data:
                print(f"✅ Sample mock created: {SAMPLE_MOCK['title']}")
            else:
                print("⚠️  Sample mock may already exist")
                
        except Exception as e:
            print(f"⚠️  Sample mock creation error: {e}")
        
        print("\n🎉 Database initialization completed!")
        print("\n📋 Summary:")
        print(f"   - Admin user: {ADMIN_USER['email']} / {ADMIN_USER['password']}")
        print(f"   - Sample user: {SAMPLE_USER['email']} / {SAMPLE_USER['password']}")
        print(f"   - Sample mock: {SAMPLE_MOCK['title']} ({len(SAMPLE_MOCK['questions'])} questions)")
        print("\n🚀 You can now start the application!")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(init_database())