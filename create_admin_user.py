"""
Script to create admin user in the database
Run this to set up the admin account for the first time
"""
import asyncio
import bcrypt
from supabase import create_client, Client
import config

async def create_admin_user():
    """Create the admin user in the database"""
    try:
        # Initialize Supabase client
        client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        
        # Check if admin user already exists
        result = client.table('users').select('*').eq('email', config.ADMIN_EMAIL).execute()
        
        if result.data:
            print(f"Admin user {config.ADMIN_EMAIL} already exists!")
            return
        
        # Hash the password
        hashed_password = bcrypt.hashpw(config.ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt())
        
        # Create admin user
        result = client.table('users').insert({
            'email': config.ADMIN_EMAIL,
            'password_hash': hashed_password.decode('utf-8'),
            'credits_balance': 1000,  # Give admin lots of credits
            'role': 'admin'
        }).execute()
        
        if result.data:
            print(f"✅ Admin user created successfully!")
            print(f"Email: {config.ADMIN_EMAIL}")
            print(f"Password: {config.ADMIN_PASSWORD}")
            print(f"Role: admin")
            print(f"Credits: 1000")
        else:
            print("❌ Failed to create admin user")
            
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")

if __name__ == "__main__":
    asyncio.run(create_admin_user())