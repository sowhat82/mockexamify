"""
Terms of Service Page for MockExamify
"""

from pathlib import Path

import streamlit as st


def show_terms_page():
    """Display Terms of Service page"""

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

        # Display in a container with styling
        st.markdown(
            """
            <style>
            /* Force all text in stMarkdown to black */
            .stMarkdown, .stMarkdown * {
                color: #000000 !important;
            }
            .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
                color: #000000 !important;
            }
            .stMarkdown p, .stMarkdown li, .stMarkdown span, .stMarkdown div {
                color: #000000 !important;
            }
            </style>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(tos_content, unsafe_allow_html=True)

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
