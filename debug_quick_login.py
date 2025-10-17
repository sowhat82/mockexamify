"""
Debug script to check why quick login isn't showing
Run this to see the exact conditions being checked
"""
import config

print("=" * 60)
print("QUICK LOGIN DEBUG INFO")
print("=" * 60)

print("\nChecking the three required conditions:")
print(f"1. API_BASE_URL == 'http://localhost:8000'")
print(f"   Current value: '{config.API_BASE_URL}'")
print(f"   Match: {config.API_BASE_URL == 'http://localhost:8000'}")

print(f"\n2. ENVIRONMENT == 'development'")
print(f"   Current value: '{config.ENVIRONMENT}'")
print(f"   Match: {config.ENVIRONMENT == 'development'}")

print(f"\n3. DEMO_MODE == True")
print(f"   Current value: {config.DEMO_MODE}")
print(f"   Match: {config.DEMO_MODE == True}")

print("\n" + "=" * 60)
is_localhost = config.API_BASE_URL == "http://localhost:8000"
is_dev_env = config.ENVIRONMENT == "development"
is_demo = config.DEMO_MODE

all_conditions_met = is_localhost and is_dev_env and is_demo

print(f"ALL CONDITIONS MET: {all_conditions_met}")
print("=" * 60)

if all_conditions_met:
    print("\n✅ Quick login SHOULD be visible!")
    print("\nIf you don't see it:")
    print("1. Stop Streamlit (Ctrl+C)")
    print("2. Clear browser cache or hard refresh (Ctrl+Shift+R)")
    print("3. Restart: streamlit run streamlit_app.py")
    print("4. Check you're on the login page (not logged in)")
else:
    print("\n❌ Quick login will NOT show because one or more conditions failed")
    print("\nTo fix this, update your .env file:")
    if not is_localhost:
        print(f"   - Change API_BASE_URL to: http://localhost:8000")
    if not is_dev_env:
        print(f"   - Change ENVIRONMENT to: development")
    if not is_demo:
        print(f"   - Change DEMO_MODE to: true")
    print("\nAfter updating .env, restart the Streamlit app.")
