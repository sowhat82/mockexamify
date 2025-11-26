"""
Automatic Health Check for AI Explanation Generation
Scans pools for incomplete explanations and auto-restarts generation if needed
"""
import asyncio
import logging
import os
import subprocess
import sys
from typing import Dict, List

logger = logging.getLogger(__name__)


async def check_pool_explanation_status(pool_id: str, pool_name: str) -> Dict:
    """
    Check a single pool for incomplete explanations

    Returns:
        {
            'pool_id': str,
            'pool_name': str,
            'total': int,
            'incomplete': int,
            'needs_generation': bool
        }
    """
    from db import db

    try:
        # Get all questions from the pool
        questions = await db.get_pool_questions(pool_id)

        if not questions:
            return {
                'pool_id': pool_id,
                'pool_name': pool_name,
                'total': 0,
                'incomplete': 0,
                'needs_generation': False
            }

        # Count questions with placeholder explanations
        incomplete = sum(
            1 for q in questions
            if q.get('explanation', '').startswith('The correct answer is:')
        )

        total = len(questions)

        return {
            'pool_id': pool_id,
            'pool_name': pool_name,
            'total': total,
            'incomplete': incomplete,
            'needs_generation': incomplete > 0
        }

    except Exception as e:
        logger.error(f"Error checking pool {pool_name}: {e}")
        return {
            'pool_id': pool_id,
            'pool_name': pool_name,
            'total': 0,
            'incomplete': 0,
            'needs_generation': False
        }


async def auto_check_and_restart_incomplete_pools() -> List[Dict]:
    """
    Check all active pools and automatically restart generation for incomplete ones

    Returns:
        List of pools that had generation restarted
    """
    from db import db

    restarted_pools = []

    try:
        # Get all active pools
        pools_result = db.admin_client.table('question_pools').select('*').eq('is_active', True).execute()

        if not pools_result.data:
            logger.info("No active pools found")
            return restarted_pools

        logger.info(f"Checking {len(pools_result.data)} active pools for incomplete explanations...")

        # Check each pool
        for pool in pools_result.data:
            pool_id = pool['id']
            pool_name = pool.get('pool_name', 'Unknown')

            status = await check_pool_explanation_status(pool_id, pool_name)

            if status['needs_generation']:
                logger.info(
                    f"🔄 Pool '{pool_name}': {status['incomplete']}/{status['total']} "
                    f"questions need explanations - restarting background generator"
                )

                # Restart background generation
                restart_background_generator(pool_id)

                restarted_pools.append(status)
            else:
                logger.info(f"✅ Pool '{pool_name}': All {status['total']} explanations complete")

        if restarted_pools:
            logger.info(
                f"🔧 Auto-restarted generation for {len(restarted_pools)} pool(s): "
                f"{', '.join([p['pool_name'] for p in restarted_pools])}"
            )
        else:
            logger.info("✅ All pools have complete explanations - no action needed")

        return restarted_pools

    except Exception as e:
        logger.error(f"Error in auto-check: {e}", exc_info=True)
        return restarted_pools


def restart_background_generator(pool_id: str):
    """
    Restart the background explanation generator for a specific pool
    """
    try:
        # Use current Python interpreter
        python_path = sys.executable
        script_path = os.path.join(os.getcwd(), "background_explanation_generator.py")

        # Check if generator is already running for this pool
        # (simple check - don't start duplicate processes)
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and 'background_explanation_generator.py' in ' '.join(cmdline):
                    if pool_id in ' '.join(cmdline):
                        logger.info(f"Background generator already running for pool {pool_id} - skipping")
                        return
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Spawn detached background process
        subprocess.Popen(
            [python_path, script_path, pool_id],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,  # Detach from parent process
        )

        logger.info(f"✅ Restarted background generator for pool {pool_id}")

    except Exception as e:
        logger.error(f"Failed to restart background generator for pool {pool_id}: {e}")


async def get_all_pool_statuses() -> List[Dict]:
    """
    Get explanation status for all active pools (for dashboard display)

    Returns:
        List of pool statuses with completion percentages
    """
    from db import db

    try:
        pools_result = db.admin_client.table('question_pools').select('*').eq('is_active', True).execute()

        if not pools_result.data:
            return []

        statuses = []
        for pool in pools_result.data:
            pool_id = pool['id']
            pool_name = pool.get('pool_name', 'Unknown')

            status = await check_pool_explanation_status(pool_id, pool_name)

            # Add completion percentage
            if status['total'] > 0:
                status['completion_pct'] = round(
                    ((status['total'] - status['incomplete']) / status['total']) * 100, 1
                )
            else:
                status['completion_pct'] = 100.0

            statuses.append(status)

        return statuses

    except Exception as e:
        logger.error(f"Error getting pool statuses: {e}")
        return []


def run_health_check_sync():
    """
    Synchronous wrapper for health check (for use in Streamlit startup)
    """
    try:
        asyncio.run(auto_check_and_restart_incomplete_pools())
    except Exception as e:
        logger.error(f"Error running health check: {e}")
