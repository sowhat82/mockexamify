"""
Privacy Policy Page for MockExamify
"""

from pathlib import Path

import streamlit as st


def show_privacy_page():
    """Display Privacy Policy page"""

    # Page config
    st.markdown('<h2 style="color: #000000;">🔒 Privacy Policy</h2>', unsafe_allow_html=True)

    # Back button at top
    if st.button("⬅️ Back to Login", use_container_width=True, type="secondary"):
        st.session_state.page = "login"
        st.rerun()

    st.markdown("---")

    # Read and display the Privacy Policy
    privacy_path = Path(__file__).parent.parent / "legal" / "privacy_policy.md"

    try:
        with open(privacy_path, "r", encoding="utf-8") as f:
            privacy_content = f.read()

        # Display in a container with styling
        st.markdown(
            """
            <style>
            /* Force all text to black with maximum specificity */
            .stMarkdown, .stMarkdown *,
            .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
            .stMarkdown p, .stMarkdown li, .stMarkdown span, .stMarkdown div,
            .stMarkdown a, .stMarkdown strong, .stMarkdown em, .stMarkdown code,
            div[data-testid="stMarkdownContainer"] *,
            [data-testid="stMarkdownContainer"] *,
            .element-container * {
                color: #000000 !important;
            }
            </style>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(privacy_content, unsafe_allow_html=True)

        # Back button at bottom
        st.markdown("---")
        if st.button(
            "⬅️ Back to Login", use_container_width=True, type="secondary", key="back_bottom"
        ):
            st.session_state.page = "login"
            st.rerun()

    except FileNotFoundError:
        st.error(
            "Privacy Policy document not found. Please contact support at support@mockexamify.com"
        )
        if st.button("⬅️ Back to Login"):
            st.session_state.page = "login"
            st.rerun()


if __name__ == "__main__":
    show_privacy_page()
