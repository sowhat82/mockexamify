"""
Script to create admin user in the database
Run this to set up the admin account for the first time
"""
import bcrypt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_admin_user():
    """Create the admin user in the database"""
    try:
        from supabase import create_client, Client
        
        # Get credentials from environment/secrets
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@mockexamify.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        
        if not supabase_url or not supabase_key:
            print("❌ Missing SUPABASE_URL or SUPABASE_KEY in environment variables")
            return
        
        print(f"Connecting to Supabase: {supabase_url}")
        
        # Initialize Supabase client
        client = create_client(supabase_url, supabase_key)
        
        # Check if admin user already exists
        result = client.table('users').select('*').eq('email', admin_email).execute()
        
        if result.data:
            print(f"✅ Admin user {admin_email} already exists!")
            user = result.data[0]
            print(f"   User ID: {user['id']}")
            print(f"   Role: {user.get('role', 'user')}")
            print(f"   Credits: {user.get('credits_balance', 0)}")
            return
        
        # Hash the password
        hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
        
        # Create admin user
        result = client.table('users').insert({
            'email': admin_email,
            'password_hash': hashed_password.decode('utf-8'),
            'credits_balance': 1000,  # Give admin lots of credits
            'role': 'admin'
        }).execute()
        
        if result.data:
            print(f"✅ Admin user created successfully!")
            print(f"   Email: {admin_email}")
            print(f"   Password: {admin_password}")
            print(f"   Role: admin")
            print(f"   Credits: 1000")
        else:
            print("❌ Failed to create admin user")
            print(f"   Response: {result}")
            
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_admin_user()