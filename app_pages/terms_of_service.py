"""
Terms of Service Page for MockExamify
"""

import re
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

        # Add inline black color styles to all HTML elements
        def add_black_color_styles(html_content):
            """Add inline black color to all HTML tags"""
            # Add style to opening tags
            html_content = re.sub(
                r'<(h[1-6]|p|li|ul|ol|div|span|strong|em|a)([^>]*)>',
                r'<\1\2 style="color: #000000 !important;">',
                html_content
            )
            return html_content

        # Apply black color styling
        styled_content = add_black_color_styles(tos_content)

        # Display with comprehensive CSS and wrapped content
        st.markdown(
            """
            <style>
            /* Force all text to black with maximum specificity */
            .tos-container,
            .tos-container *,
            .tos-container h1, .tos-container h2, .tos-container h3,
            .tos-container h4, .tos-container h5, .tos-container h6,
            .tos-container p, .tos-container li, .tos-container ul, .tos-container ol,
            .tos-container span, .tos-container div, .tos-container a,
            .tos-container strong, .tos-container em, .tos-container code {
                color: #000000 !important;
            }
            </style>
        """,
            unsafe_allow_html=True,
        )

        # Wrap in container with inline style
        final_content = f'<div class="tos-container" style="color: #000000 !important;">{styled_content}</div>'
        st.markdown(final_content, unsafe_allow_html=True)

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
