"""
Create test student account in live Supabase database
This script will create the test student account specified in streamlit-secrets.toml
"""
import asyncio
import bcrypt
from datetime import datetime
from supabase import create_client, Client

async def create_test_student():
    """Create test student account in the database"""
    try:
        # Supabase credentials from your secrets file
        SUPABASE_URL = "https://mgdgovkyomfkcljutcsj.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1nZGdvdmt5b21ma2NsanV0Y3NqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk5MzY2NzYsImV4cCI6MjA3NTUxMjY3Nn0.a1ZAzp1QKS_Rr0IJmdANbypzFBGOCOqcLl4-_Oi1LOc"
        
        # Initialize Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Test student credentials from secrets
        email = "student@test.com"
        password = "student123"
        
        print(f"Creating test student account: {email}")
        
        # Check if user already exists
        existing_user = supabase.table('users').select('*').eq('email', email).execute()
        
        if existing_user.data:
            print(f"❌ User {email} already exists in the database!")
            print("User details:", existing_user.data[0])
            return
        
        # Hash the password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create the user record (only using columns that exist)
        user_data = {
            'email': email,
            'password_hash': password_hash,
            'credits_balance': 25,  # Give them extra credits for testing
            'role': 'user',
            'created_at': datetime.now().isoformat()
        }
        
        # Insert into database
        result = supabase.table('users').insert(user_data).execute()
        
        if result.data:
            print("✅ Test student account created successfully!")
            print(f"📧 Email: {email}")
            print(f"🔒 Password: {password}")
            print(f"💰 Credits: {user_data['credits_balance']}")
            print(f"🆔 User ID: {result.data[0]['id']}")
            print("\nYou can now log in with these credentials on your live app!")
        else:
            print("❌ Failed to create user account")
            print("Error:", result)
            
    except Exception as e:
        print(f"❌ Error creating test student: {e}")
        print("Make sure your Supabase credentials are correct and the users table exists.")

if __name__ == "__main__":
    print("🚀 Creating test student account in live database...")
    print("=" * 50)
    asyncio.run(create_test_student())