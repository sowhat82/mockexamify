"""
MockExamify - SIMPLE Streamlit Application (NO COMPLEX CSS)
Interactive Mock Exam Platform with Credit System
"""
import streamlit as st
import config
from auth_utils import AuthUtils, validate_email, validate_password, run_async

# Import components (no auto-navigation)
try:
    from components.dashboard import show_dashboard, handle_dashboard_modals
except ImportError:
    def show_dashboard():
        st.error("Dashboard functionality temporarily unavailable")
    def handle_dashboard_modals():
        pass

try:
    from components.exam import show_exam
except ImportError:
    def show_exam():
        st.error("Exam functionality temporarily unavailable")

try:
    from components.purchase_credits import show_purchase_credits, handle_payment_callback
except ImportError:
    def show_purchase_credits():
        st.error("Purchase functionality temporarily unavailable")
    def handle_payment_callback():
        pass

try:
    from components.past_attempts import show_past_attempts, handle_modals
except ImportError:
    def show_past_attempts():
        st.error("Past attempts functionality temporarily unavailable")
    def handle_modals():
        pass

# Import admin components
try:
    from components.admin_manage import show_admin_manage
    from components.admin_dashboard import show_admin_dashboard
except ImportError:
    # Fallback if admin components aren't available yet
    def show_admin_manage():
        st.info("Admin management functionality coming soon!")
    def show_admin_dashboard():
        st.info("Admin dashboard functionality coming soon!")

# Configure Streamlit page
st.set_page_config(
    page_title="MockExamify",
    page_icon="🎯", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

def main():
    """Main application logic with simple UI"""
    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "login"
    if "last_email" not in st.session_state:
        st.session_state.last_email = ""
    
    # Initialize auth utility
    auth = AuthUtils(config.API_BASE_URL)
    
    # Handle payment callbacks
    query_params = st.query_params
    if "payment" in query_params:
        handle_payment_callback()
        return
    
    # Check authentication status
    if auth.is_authenticated():
        show_authenticated_app(auth)
    else:
        show_authentication_page(auth)

def show_authentication_page(auth: AuthUtils):
    """Simple authentication page"""
    
    # Hide sidebar on login page
    st.markdown("""
    <style>
    .css-1d391kg {display: none}
    .css-1rs6os {display: none}
    .css-17eq0hr {display: none}
    section[data-testid="stSidebar"] {display: none}
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🎯 MockExamify")
    st.subheader("Master Your Exams with AI-Powered Mock Tests")
    
    st.markdown("---")
    
    # Simple feature showcase
    st.subheader("Why Choose MockExamify?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📚 Comprehensive Exams**")
        st.write("• Industry-standard questions")
        st.write("• Realistic exam scenarios")
        st.write("• Detailed performance analysis")
    
    with col2:
        st.markdown("**🤖 AI-Powered Insights**")
        st.write("• Personalized explanations")
        st.write("• Smart performance analytics")
        st.write("• Adaptive recommendations")
    
    with col3:
        st.markdown("**💎 Flexible Pricing**")
        st.write("• Pay-per-exam credit system")
        st.write("• No monthly subscriptions")
        st.write("• Credits never expire")
    
    st.markdown("---")
    
    # Simple Login/Register tabs
    tab1, tab2 = st.tabs(["🔑 Sign In", "✨ Create Account"])
    
    with tab1:
        show_simple_login_form(auth)
    
    with tab2:
        show_simple_register_form(auth)

def show_simple_login_form(auth: AuthUtils):
    """Simple login form"""
    st.markdown("### Welcome Back!")
    
    with st.form("login_form"):
        email = st.text_input("📧 Email Address", value=st.session_state.last_email)
        password = st.text_input("🔒 Password", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            login_submitted = st.form_submit_button("🔑 Sign In", type="primary")
        with col2:
            forgot_password = st.form_submit_button("❓ Forgot Password?")
        
        if login_submitted:
            if not email or not password:
                st.error("⚠️ Please fill in both fields")
                return
            
            # Attempt login
            success, user_data, error_msg = run_async(auth.sign_in(email, password))
            
            if success and user_data:
                # Set the correct session state variables that AuthUtils expects
                st.session_state.authenticated = True
                st.session_state.current_user = {
                    "id": user_data.get("user_id"),
                    "email": user_data.get("email"),
                    "role": user_data.get("role"),
                    "credits_balance": user_data.get("credits_balance", 0)
                }
                st.session_state.token = user_data.get("token")
                st.session_state.last_email = email
                st.session_state.page = "dashboard"
                
                st.success("🎉 Welcome back! Redirecting to your dashboard...")
                st.rerun()
            else:
                st.error(f"❌ {error_msg or 'Login failed. Please check your credentials.'}")
        
        if forgot_password:
            st.info("🔄 Password reset feature coming soon! Contact support for assistance.")

def show_simple_register_form(auth: AuthUtils):
    """Simple registration form"""
    st.markdown("### Join MockExamify Today!")
    
    with st.form("register_form"):
        email = st.text_input("📧 Email Address")
        password = st.text_input("🔒 Password", type="password")
        confirm_password = st.text_input("🔒 Confirm Password", type="password")
        terms_agreed = st.checkbox("✅ I agree to the Terms of Service")
        
        register_submitted = st.form_submit_button("🎯 Create My Account", type="primary")
        
        if register_submitted:
            if not email or not password or not confirm_password:
                st.error("⚠️ Please fill in all fields")
                return
            
            if not terms_agreed:
                st.error("⚠️ Please agree to the Terms of Service")
                return
            
            if password != confirm_password:
                st.error("⚠️ Passwords don't match")
                return
            
            # Attempt registration
            success, user_data, error_msg = run_async(auth.sign_up(email, password))
            
            if success and user_data:
                st.success("🎉 Account created successfully! Please sign in.")
                st.session_state.last_email = email
                st.rerun()
            else:
                st.error(f"❌ {error_msg or 'Registration failed. Please try again.'}")

def show_authenticated_app(auth: AuthUtils):
    """Simple authenticated app"""
    
    # Simple sidebar navigation
    with st.sidebar:
        user = auth.get_current_user()
        st.markdown(f"### 👋 Welcome!")
        st.markdown(f"**📧 {user.get('email', 'User')}**")
        
        # Credit balance
        credits = user.get('credits_balance', 0)
        st.markdown(f"### 💰 Credits: {credits}")
        
        st.markdown("---")
        
        # Main Navigation - MVP essentials only
        if st.button("🏠 Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        
        if st.button("💳 Buy Credits"):
            st.session_state.page = "purchase_credits"
            st.rerun()
        
        if st.button("📈 My Results"):
            st.session_state.page = "past_attempts"
            st.rerun()
        
        # Simple Admin menu - MVP only
        if auth.is_admin():
            st.markdown("---")
            st.markdown("### 👨‍💼 Admin")
            
            if st.button("📊 Admin Dashboard"):
                st.session_state.page = "admin_dashboard"
                st.rerun()
            
            if st.button("🎯 Manage Exams"):
                st.session_state.page = "admin_manage"
                st.rerun()
        
        st.markdown("---")
        if st.button("🚪 Logout"):
            auth.logout()
            st.rerun()
    
    # Main content area - MVP pages only
    page = st.session_state.get("page", "dashboard")
    
    if page == "dashboard":
        show_dashboard()
        handle_dashboard_modals()
    elif page == "exam":
        show_exam()
    elif page == "purchase_credits":
        show_purchase_credits()
    elif page == "past_attempts":
        show_past_attempts()
        handle_modals()
    elif page == "admin_dashboard":
        show_admin_dashboard()
    elif page == "admin_manage":
        show_admin_manage()
    else:
        show_dashboard()
        handle_dashboard_modals()

if __name__ == "__main__":
    main()