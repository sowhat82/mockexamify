#!/usr/bin/env python3
"""Check for active users before deploying to production"""

from datetime import datetime, timezone, timedelta
from db import DatabaseManager

def check_active_users(minutes_threshold: int = 30, max_exam_duration_hours: int = 2):
    """Check for users active within the last N minutes"""
    db = DatabaseManager()

    print("🔍 Checking for active users in production...\n")

    # Calculate threshold time
    threshold = datetime.now(timezone.utc) - timedelta(minutes=minutes_threshold)
    threshold_str = threshold.isoformat()

    # Calculate stale exam threshold (exams older than N hours are considered abandoned)
    stale_threshold = datetime.now(timezone.utc) - timedelta(hours=max_exam_duration_hours)
    stale_threshold_str = stale_threshold.isoformat()

    # Check for in-progress exams (only recent ones, not stale)
    print(f"📝 Checking for active in-progress exams (started within last {max_exam_duration_hours} hours)...")
    in_progress_attempts = db.admin_client.table("attempts")\
        .select("id, user_id, created_at, status")\
        .eq("status", "in_progress")\
        .gte("created_at", stale_threshold_str)\
        .execute()

    # Also check total stale attempts for informational purposes
    all_in_progress = db.admin_client.table("attempts")\
        .select("id", count="exact")\
        .eq("status", "in_progress")\
        .execute()

    stale_count = all_in_progress.count - len(in_progress_attempts.data) if all_in_progress.count else 0

    if in_progress_attempts.data:
        print(f"⚠️  WARNING: {len(in_progress_attempts.data)} active in-progress exam(s) found!")
        for attempt in in_progress_attempts.data[:5]:  # Show first 5
            created = attempt.get('created_at', 'unknown')
            print(f"   - User ID: {attempt['user_id']}, Started: {created}")
        if len(in_progress_attempts.data) > 5:
            print(f"   ... and {len(in_progress_attempts.data) - 5} more")
    else:
        print("✅ No active in-progress exams")

    if stale_count > 0:
        print(f"ℹ️  Note: {stale_count} stale in-progress attempt(s) found (older than {max_exam_duration_hours}h, likely abandoned)")

    # Check for recently active users (updated_at field)
    print(f"\n👥 Checking for users active in last {minutes_threshold} minutes...")
    recent_users = db.admin_client.table("users")\
        .select("id, email, updated_at")\
        .gte("updated_at", threshold_str)\
        .execute()

    if recent_users.data:
        print(f"⚠️  WARNING: {len(recent_users.data)} recently active user(s) found!")
        for user in recent_users.data[:5]:  # Show first 5
            print(f"   - {user['email']}, Last activity: {user['updated_at']}")
        if len(recent_users.data) > 5:
            print(f"   ... and {len(recent_users.data) - 5} more")
    else:
        print("✅ No recently active users")

    # Check for recent attempts (completed in last N minutes)
    print(f"\n📊 Checking for recently completed exams (last {minutes_threshold} min)...")
    recent_attempts = db.admin_client.table("attempts")\
        .select("id, user_id, created_at, status")\
        .eq("status", "completed")\
        .gte("created_at", threshold_str)\
        .execute()

    if recent_attempts.data:
        print(f"ℹ️  {len(recent_attempts.data)} exam(s) completed recently")
        for attempt in recent_attempts.data[:3]:  # Show first 3
            completed = attempt.get('created_at', 'unknown')
            print(f"   - User ID: {attempt['user_id']}, Completed: {completed}")
    else:
        print("✅ No recently completed exams")

    # Summary
    print("\n" + "="*60)
    total_activity = len(in_progress_attempts.data) + len(recent_users.data)

    if in_progress_attempts.data:
        print("❌ DEPLOYMENT NOT RECOMMENDED")
        print(f"   Reason: {len(in_progress_attempts.data)} user(s) currently taking exams")
        print("   Action: Wait for exams to complete or deploy during off-peak hours")
        return False
    elif total_activity > 0:
        print("⚠️  CAUTION ADVISED")
        print(f"   {total_activity} user(s) recently active")
        print("   Consider waiting a few minutes or proceed with caution")
        return None  # User decision
    else:
        print("✅ SAFE TO DEPLOY")
        print("   No active users detected in the last 30 minutes")
        return True

if __name__ == "__main__":
    import sys

    # Allow custom threshold via command line
    threshold = 30
    if len(sys.argv) > 1:
        try:
            threshold = int(sys.argv[1])
        except ValueError:
            print("Usage: python check_active_users.py [minutes_threshold]")
            sys.exit(1)

    result = check_active_users(threshold)

    # Exit with appropriate code for scripting
    if result is True:
        sys.exit(0)  # Safe to deploy
    elif result is False:
        sys.exit(1)  # Do not deploy
    else:
        sys.exit(2)  # Caution - user decision
