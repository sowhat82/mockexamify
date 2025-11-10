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

        # Add aggressive CSS to force black text
        st.markdown(
            """
        <style>
        /* Override Streamlit's theme colors */
        [data-testid="stMarkdownContainer"],
        [data-testid="stMarkdownContainer"] *,
        .stMarkdown,
        .stMarkdown *,
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
        .stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
        .stMarkdown p, .stMarkdown li, .stMarkdown ul, .stMarkdown ol,
        .stMarkdown span, .stMarkdown div, .stMarkdown a,
        .stMarkdown strong, .stMarkdown em, .stMarkdown code,
        .element-container p,
        .element-container h1, .element-container h2, .element-container h3,
        .element-container h4, .element-container h5, .element-container h6,
        .element-container li, .element-container span {
            color: #000000 !important;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        # Display markdown content directly
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

        # Add aggressive CSS to force black text
        st.markdown(
            """
        <style>
        /* Override Streamlit's theme colors */
        [data-testid="stMarkdownContainer"],
        [data-testid="stMarkdownContainer"] *,
        .stMarkdown,
        .stMarkdown *,
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
        .stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
        .stMarkdown p, .stMarkdown li, .stMarkdown ul, .stMarkdown ol,
        .stMarkdown span, .stMarkdown div, .stMarkdown a,
        .stMarkdown strong, .stMarkdown em, .stMarkdown code,
        .element-container p,
        .element-container h1, .element-container h2, .element-container h3,
        .element-container h4, .element-container h5, .element-container h6,
        .element-container li, .element-container span {
            color: #000000 !important;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        # Display markdown content directly
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
