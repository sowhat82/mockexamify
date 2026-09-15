"""
Investigate general knowledge questions in CM-SIP pool
"""

import asyncio

from db import db


async def main():
    # Get CM-SIP pool
    pools = await db.get_all_question_pools()
    cm_sip_pool = next((p for p in pools if "CM-SIP" in p["pool_name"]), None)

    if not cm_sip_pool:
        print("CM-SIP pool not found")
        return

    pool_id = cm_sip_pool["id"]
    print(f"Checking pool: {cm_sip_pool['pool_name']} (ID: {pool_id})")
    print(f"Total questions: {cm_sip_pool.get('unique_questions', 0)}\n")

    # Search for general knowledge questions
    search_terms = [
        "france",
        "capital",
        "paris",
        "london",
        "programming",
        "javascript",
        "python",
        "what is 2+2",
        "what is the output",
    ]

    found_any = False
    for term in search_terms:
        response = (
            db.client.table("pool_questions")
            .select("*")
            .eq("pool_id", pool_id)
            .ilike("question_text", f"%{term}%")
            .execute()
        )

        if response.data:
            found_any = True
            print(f"\n{'='*80}")
            print(f"Found {len(response.data)} question(s) containing '{term}':")
            print("=" * 80)

            for i, q in enumerate(response.data[:3], 1):
                print(f"\nQuestion {i}:")
                print(f"Text: {q['question_text']}")
                print(f"Source: {q.get('source_file', 'Unknown')}")
                print(f"Uploaded: {q.get('uploaded_at', 'Unknown')}")

                # Parse choices
                import json

                choices = (
                    json.loads(q["choices"]) if isinstance(q["choices"], str) else q["choices"]
                )
                print(f"Choices: {choices}")
                print(f"Correct answer: {q['correct_answer']}")

    if not found_any:
        print("No general knowledge questions found!")
        print("\nSearching for recent uploads...")

        # Get most recent questions
        response = (
            db.client.table("pool_questions")
            .select("*")
            .eq("pool_id", pool_id)
            .order("uploaded_at", desc=True)
            .limit(10)
            .execute()
        )

        print(f"\nMost recent {len(response.data)} questions:")
        for i, q in enumerate(response.data, 1):
            print(f"\n{i}. {q['question_text'][:100]}...")
            print(f"   Source: {q.get('source_file', 'Unknown')}")
            print(f"   Uploaded: {q.get('uploaded_at', 'Unknown')}")


if __name__ == "__main__":
    asyncio.run(main())
