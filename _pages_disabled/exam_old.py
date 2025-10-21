import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta

import streamlit as st

import config
from auth_utils import AuthUtils, run_async
from db import db


def show_exam():
    """Show the exam page - called by streamlit_app.py"""
    auth = AuthUtils(config.API_BASE_URL)

    if not auth.is_authenticated():
        st.error("Please log in to access the exam page")
        st.stop()

    user = auth.get_current_user()

    st.title(" Take Mock Exam")

    # Initialize session state
    if "exam_state" not in st.session_state:
        st.session_state.exam_state = "not_started"
    if "current_mock" not in st.session_state:
        st.session_state.current_mock = None
    if "answers" not in st.session_state:
        st.session_state.answers = {}
    if "current_question" not in st.session_state:
        st.session_state.current_question = 0
    if "start_time" not in st.session_state:
        st.session_state.start_time = None
    if "exam_id" not in st.session_state:
        st.session_state.exam_id = None

    # Simple exam interface for now
    if st.session_state.exam_state == "not_started":
        st.markdown("###  Available Mock Exams")

        # Load available mocks
        try:
            mocks = asyncio.run(db.get_all_mocks())

            if not mocks:
                st.warning("⚠️ No mock exams available. Please contact admin.")
                return

            # Display user credits
            user_data = asyncio.run(db.get_user_by_id(user["id"]))
            credits = user_data.credits_balance if user_data else 0

            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f" Available Credits: {credits}")
            with col2:
                if st.button(" Buy Credits"):
                    st.switch_page("pages/purchase_credits.py")

            # Mock selection
            for mock in mocks:
                with st.container():
                    st.markdown(f"####  {mock.get('title', 'Untitled Mock')}")

                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                    with col1:
                        st.write(f"**Description:** {mock.get('description', 'No description')}")

                    with col2:
                        questions_count = len(json.loads(mock.get("questions", "[]")))
                        st.metric("Questions", questions_count)

                    with col3:
                        st.metric("Duration", f"{mock.get('duration', 60)} min")

                    with col4:
                        if st.button(f" Start Exam", key=f"start_{mock['id']}"):
                            if credits >= 1:
                                # Start exam logic would go here
                                st.success("Starting exam... (Feature in development)")
                            else:
                                st.error(" Insufficient credits!")

                    st.divider()

        except Exception as e:
            st.error(f"Error loading exams: {e}")

    else:
        st.info("Exam in progress... (Feature in development)")

        # Reset button
        if st.button(" Reset to Start"):
            st.session_state.exam_state = "not_started"
            st.rerun()


def main():
    """Main function for standalone execution"""
    show_exam()


if __name__ == "__main__":
    main()
