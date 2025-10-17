"""
Terms of Service Page for MockExamify
"""
import streamlit as st
from pathlib import Path

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
        with open(tos_path, 'r', encoding='utf-8') as f:
            tos_content = f.read()
        
        # Display in a container with styling
        st.markdown("""
            <style>
            .legal-content {
                background: white;
                padding: 2rem;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                color: #000000;
            }
            .legal-content h1, .legal-content h2, .legal-content h3 {
                color: #000000;
            }
            .legal-content p, .legal-content li {
                color: #333333;
            }
            </style>
        """, unsafe_allow_html=True)
        
        with st.container():
            st.markdown(tos_content, unsafe_allow_html=True)
        
        # Back button at bottom
        st.markdown("---")
        if st.button("⬅️ Back to Login", use_container_width=True, type="secondary", key="back_bottom"):
            st.session_state.page = "login"
            st.rerun()
            
    except FileNotFoundError:
        st.error("Terms of Service document not found. Please contact support at support@mockexamify.com")
        if st.button("⬅️ Back to Login"):
            st.session_state.page = "login"
            st.rerun()

if __name__ == "__main__":
    show_terms_page()
