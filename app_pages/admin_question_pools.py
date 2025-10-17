"""
Admin Question Pool Management Page
View, edit, and manage question pools
"""
import streamlit as st
import json
from typing import List, Dict, Any
from auth_utils import AuthUtils, run_async
import config

def show_admin_question_pools():
    """Display question pool management page"""
    auth = AuthUtils(config.API_BASE_URL)
    
    if not auth.is_authenticated() or not auth.is_admin():
        st.error("Admin access required")
        st.stop()
    
    st.markdown("# 💼 Question Pool Management")
    st.markdown("View and manage your question pools")
    
    # Load question pools
    pools = run_async(load_question_pools())
    
    if not pools:
        st.info("📭 No question pools found. Upload some questions to get started!")
        if st.button("➕ Upload Questions", use_container_width=True):
            st.session_state.page = "admin_upload"
            st.rerun()
        return
    
    # Display pools overview
    st.markdown("### 📚 Your Question Pools")
    
    for pool in pools:
        with st.expander(f"**{pool['pool_name']}** - {pool['unique_questions']} unique questions", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"""
                **Category:** {pool.get('category', 'Uncategorized')}
                
                **Description:** {pool.get('description', 'No description')}
                
                **Statistics:**
                - Total questions uploaded: {pool.get('total_questions', 0)}
                - Unique questions (after deduplication): {pool.get('unique_questions', 0)}
                - Duplicates removed: {pool.get('total_questions', 0) - pool.get('unique_questions', 0)}
                
                **Last Updated:** {pool.get('last_updated', 'Unknown')}
                """)
            
            with col2:
                if st.button(f"👁️ View Questions", key=f"view_{pool['id']}"):
                    st.session_state.viewing_pool = pool['id']
                    st.rerun()
                
                if st.button(f"➕ Add More Questions", key=f"add_{pool['id']}"):
                    st.session_state.page = "admin_upload"
                    st.session_state.pool_name = pool['pool_name']
                    st.rerun()
                
                if st.button(f"🗑️ Delete Pool", key=f"delete_{pool['id']}", type="secondary"):
                    st.session_state.confirm_delete_pool = pool['id']
                    st.rerun()
    
    # Show questions if a pool is selected
    if hasattr(st.session_state, 'viewing_pool') and st.session_state.viewing_pool:
        show_pool_questions(st.session_state.viewing_pool)
    
    # Handle delete confirmation
    if hasattr(st.session_state, 'confirm_delete_pool') and st.session_state.confirm_delete_pool:
        show_delete_confirmation(st.session_state.confirm_delete_pool, pools)


def show_pool_questions(pool_id: str):
    """Display questions in a specific pool"""
    st.markdown("---")
    st.markdown("### 📝 Pool Questions")
    
    questions = run_async(load_pool_questions(pool_id))
    
    if not questions:
        st.info("No questions found in this pool")
        if st.button("⬅️ Back to Pools"):
            del st.session_state.viewing_pool
            st.rerun()
        return
    
    # Filter and search
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search questions", placeholder="Type to search...")
    
    with col2:
        sort_by = st.selectbox("Sort by", ["Recent", "Most Shown", "Most Correct", "Most Incorrect"])
    
    with col3:
        if st.button("⬅️ Back to Pools"):
            del st.session_state.viewing_pool
            st.rerun()
    
    # Filter questions based on search
    filtered_questions = questions
    if search_term:
        filtered_questions = [
            q for q in questions
            if search_term.lower() in q['question_text'].lower()
        ]
    
    # Sort questions
    if sort_by == "Most Shown":
        filtered_questions.sort(key=lambda x: x.get('times_shown', 0), reverse=True)
    elif sort_by == "Most Correct":
        filtered_questions.sort(key=lambda x: x.get('times_correct', 0), reverse=True)
    elif sort_by == "Most Incorrect":
        filtered_questions.sort(key=lambda x: x.get('times_incorrect', 0), reverse=True)
    
    st.markdown(f"**Showing {len(filtered_questions)} of {len(questions)} questions**")
    
    # Display questions
    for idx, question in enumerate(filtered_questions, 1):
        with st.expander(f"Q{idx}: {question['question_text'][:100]}..."):
            display_question_details(question)


def display_question_details(question: Dict[str, Any]):
    """Display detailed question information"""
    st.markdown(f"**Question:** {question['question_text']}")
    
    # Display choices
    st.markdown("**Choices:**")
    choices = json.loads(question['choices']) if isinstance(question['choices'], str) else question['choices']
    
    for i, choice in enumerate(choices):
        if i == question['correct_answer']:
            st.success(f"✅ {i}: {choice} (Correct Answer)")
        else:
            st.markdown(f"◯ {i}: {choice}")
    
    # Display metadata
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **Source:** {question.get('source_file', 'Unknown')}
        
        **Uploaded:** {question.get('uploaded_at', 'Unknown')}
        
        **Difficulty:** {question.get('difficulty', 'Medium')}
        """)
    
    with col2:
        st.markdown(f"""
        **Statistics:**
        - Times shown: {question.get('times_shown', 0)}
        - Times correct: {question.get('times_correct', 0)}
        - Times incorrect: {question.get('times_incorrect', 0)}
        """)
    
    if question.get('explanation'):
        st.markdown(f"**Explanation:** {question['explanation']}")
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(f"✏️ Edit", key=f"edit_{question['id']}"):
            st.session_state.editing_question = question['id']
            st.rerun()
    
    with col2:
        if st.button(f"🗑️ Delete", key=f"delete_q_{question['id']}", type="secondary"):
            success = run_async(delete_question(question['id']))
            if success:
                st.success("Question deleted!")
                st.rerun()
            else:
                st.error("Failed to delete question")


def show_delete_confirmation(pool_id: str, pools: List[Dict[str, Any]]):
    """Show delete confirmation dialog"""
    pool = next((p for p in pools if p['id'] == pool_id), None)
    
    if not pool:
        return
    
    st.markdown("---")
    st.warning(f"⚠️ Are you sure you want to delete the pool **{pool['pool_name']}**?")
    st.markdown(f"This will delete {pool['unique_questions']} questions permanently.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("❌ Yes, Delete Pool", type="primary", use_container_width=True):
            success = run_async(delete_pool(pool_id))
            if success:
                st.success("Pool deleted successfully!")
                del st.session_state.confirm_delete_pool
                st.rerun()
            else:
                st.error("Failed to delete pool")
    
    with col2:
        if st.button("⬅️ Cancel", use_container_width=True):
            del st.session_state.confirm_delete_pool
            st.rerun()


async def load_question_pools() -> List[Dict[str, Any]]:
    """Load all question pools"""
    try:
        from db import db
        return await db.get_all_question_pools()
    except Exception as e:
        st.error(f"Error loading question pools: {str(e)}")
        return []


async def load_pool_questions(pool_id: str) -> List[Dict[str, Any]]:
    """Load questions from a specific pool"""
    try:
        from db import db
        return await db.get_pool_questions(pool_id)
    except Exception as e:
        st.error(f"Error loading pool questions: {str(e)}")
        return []


async def delete_pool(pool_id: str) -> bool:
    """Delete a question pool"""
    try:
        from db import db
        
        if db.demo_mode:
            return True
        
        # In production, set is_active to False instead of hard delete
        response = (
            db.client.table("question_pools")
            .update({"is_active": False})
            .eq("id", pool_id)
            .execute()
        )
        
        return bool(response.data)
    except Exception as e:
        st.error(f"Error deleting pool: {str(e)}")
        return False


async def delete_question(question_id: str) -> bool:
    """Delete a specific question"""
    try:
        from db import db
        
        if db.demo_mode:
            return True
        
        response = (
            db.client.table("pool_questions")
            .delete()
            .eq("id", question_id)
            .execute()
        )
        
        return bool(response.data)
    except Exception as e:
        st.error(f"Error deleting question: {str(e)}")
        return False


# Main entry point
if __name__ == "__main__":
    show_admin_question_pools()
