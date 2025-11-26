"""
One-time cleanup script to fix corrupted question text in existing database
"""
import asyncio
import logging
from question_text_validator import QuestionTextValidator
from db import db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def cleanup_all_pools():
    """Fix corrupted question text in all active pools"""

    print('=' * 80)
    print('🔧 ONE-TIME CLEANUP: Fixing Corrupted Question Text')
    print('=' * 80)
    print()

    validator = QuestionTextValidator()

    # Get all active pools
    pools_result = db.admin_client.table('question_pools').select('*').eq('is_active', True).execute()

    if not pools_result.data:
        print('No active pools found')
        return

    total_fixed = 0
    total_questions = 0
    fixes_by_pool = {}

    for pool in pools_result.data:
        pool_id = pool['id']
        pool_name = pool.get('pool_name', 'Unknown')

        print(f'\n📋 Processing pool: {pool_name}')
        print('-' * 80)

        # Get all questions
        questions_result = db.admin_client.table('pool_questions').select('*').eq('pool_id', pool_id).execute()

        pool_fixes = []
        questions_fixed = 0

        for q in questions_result.data:
            total_questions += 1
            question_id = q['id']
            original_text = q.get('question_text', '')

            if not original_text:
                continue

            # Validate and fix
            fixed_text, fixes_applied, warnings = validator.validate_and_fix_question(original_text)

            # Only update if text was actually changed
            if fixed_text != original_text:
                # Update in database
                update_result = db.admin_client.table('pool_questions').update({
                    'question_text': fixed_text
                }).eq('id', question_id).execute()

                if update_result.data:
                    questions_fixed += 1
                    total_fixed += 1

                    pool_fixes.append({
                        'id': question_id[:8],
                        'original': original_text[:80] + ('...' if len(original_text) > 80 else ''),
                        'fixed': fixed_text[:80] + ('...' if len(fixed_text) > 80 else ''),
                        'fixes': fixes_applied
                    })

        if questions_fixed > 0:
            fixes_by_pool[pool_name] = pool_fixes
            print(f'✅ Fixed {questions_fixed} questions in {pool_name}')

            # Show first 5 examples
            for i, fix in enumerate(pool_fixes[:5], 1):
                print(f'\n  {i}. ID: {fix["id"]}...')
                print(f'     Original: {fix["original"]}')
                print(f'     Fixed:    {fix["fixed"]}')
                print(f'     Changes:  {", ".join(fix["fixes"])}')

            if len(pool_fixes) > 5:
                print(f'\n  ... and {len(pool_fixes) - 5} more')
        else:
            print(f'✅ No corruption found in {pool_name}')

    print()
    print('=' * 80)
    print(f'🎉 CLEANUP COMPLETE')
    print('=' * 80)
    print(f'Total questions scanned: {total_questions}')
    print(f'Total questions fixed: {total_fixed}')
    print()

    if total_fixed > 0:
        print('✨ Summary of fixes by pool:')
        for pool_name, fixes in fixes_by_pool.items():
            print(f'  • {pool_name}: {len(fixes)} questions fixed')
    else:
        print('✅ No corrupted questions found - database is clean!')


if __name__ == '__main__':
    asyncio.run(cleanup_all_pools())
