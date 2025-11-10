"""
Terms of Service Page for MockExamify
"""

import re
from pathlib import Path

import streamlit as st


def show_terms_page():
    """Display Terms of Service page"""

    # DEBUG MESSAGE
    st.warning("🔧 DEBUG: This is app_pages/terms_of_service.py - version 2024-01-10")

    # Page config
    st.markdown('<h2 style="color: #000000;">📜 Terms of Service</h2>', unsafe_allow_html=True)

    # Back button at top
    if st.button("⬅️ Back to Login", use_container_width=True, type="secondary"):
        st.session_state.page = "login"
        st.rerun()

    st.markdown("---")

    # Read and display the Terms of Service
    tos_path = Path(__file__).parent.parent / "legal" / "terms_of_service.md"

    try:
        with open(tos_path, "r", encoding="utf-8") as f:
            tos_content = f.read()

        # Add aggressive CSS to force black text on white background
        st.markdown(
            """
            <style>
            /* Override Streamlit's theme colors for this page */
            [data-testid="stAppViewContainer"] {
                background-color: #FFFFFF !important;
            }
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
                background-color: transparent !important;
            }
            </style>
        """,
            unsafe_allow_html=True,
        )

        # Display markdown content directly (Streamlit will render it)
        st.markdown(tos_content)

        # Back button at bottom
        st.markdown("---")
        if st.button(
            "⬅️ Back to Login", use_container_width=True, type="secondary", key="back_bottom"
        ):
            st.session_state.page = "login"
            st.rerun()

    except FileNotFoundError:
        st.error(
            "Terms of Service document not found. Please contact support at support@mockexamify.com"
        )
        if st.button("⬅️ Back to Login"):
            st.session_state.page = "login"
            st.rerun()


if __name__ == "__main__":
    show_terms_page()
