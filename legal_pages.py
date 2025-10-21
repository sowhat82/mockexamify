"""
Legal pages for MockExamify - Terms of Service and Privacy Policy
"""

from pathlib import Path

import streamlit as st


def show_terms_of_service():
    """Display Terms of Service"""
    st.markdown("### 📜 Terms of Service")

    # Read and display the Terms of Service
    tos_path = Path(__file__).parent / "legal" / "terms_of_service.md"
    try:
        with open(tos_path, "r", encoding="utf-8") as f:
            tos_content = f.read()

        # Create a scrollable container for the terms
        st.markdown(
            """
        <style>
        .legal-document {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            max-height: 600px;
            overflow-y: auto;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        with st.container():
            st.markdown(tos_content)

        if st.button("⬅️ Back", key="back_from_tos"):
            st.session_state.page = "login"
            st.rerun()

    except FileNotFoundError:
        st.error("Terms of Service document not found. Please contact support.")


def show_privacy_policy():
    """Display Privacy Policy"""
    st.markdown("### 🔒 Privacy Policy")

    # Read and display the Privacy Policy
    privacy_path = Path(__file__).parent / "legal" / "privacy_policy.md"
    try:
        with open(privacy_path, "r", encoding="utf-8") as f:
            privacy_content = f.read()

        # Create a scrollable container for the policy
        st.markdown(
            """
        <style>
        .legal-document {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            max-height: 600px;
            overflow-y: auto;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        with st.container():
            st.markdown(privacy_content)

        if st.button("⬅️ Back", key="back_from_privacy"):
            st.session_state.page = "login"
            st.rerun()

    except FileNotFoundError:
        st.error("Privacy Policy document not found. Please contact support.")


def show_legal_modal(document_type="tos"):
    """Show legal document in a modal-style dialog"""
    if document_type == "tos":
        show_terms_of_service()
    elif document_type == "privacy":
        show_privacy_policy()
