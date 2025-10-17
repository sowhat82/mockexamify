"""
Privacy Policy Page for MockExamify
"""
import streamlit as st
from pathlib import Path

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
        with open(privacy_path, 'r', encoding='utf-8') as f:
            privacy_content = f.read()
        
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
            st.markdown(privacy_content, unsafe_allow_html=True)
        
        # Back button at bottom
        st.markdown("---")
        if st.button("⬅️ Back to Login", use_container_width=True, type="secondary", key="back_bottom"):
            st.session_state.page = "login"
            st.rerun()
            
    except FileNotFoundError:
        st.error("Privacy Policy document not found. Please contact support at support@mockexamify.com")
        if st.button("⬅️ Back to Login"):
            st.session_state.page = "login"
            st.rerun()

if __name__ == "__main__":
    show_privacy_page()
