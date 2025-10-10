"""
MockExamify - Main Streamlit Application
Interactive Mock Exam Platform with Credit System
"""
import streamlit as st
import config
from auth_utils import AuthUtils, validate_email, validate_password, run_async

# Import pages
from pages.dashboard import show_dashboard, show_past_attempts
from pages.exam import show_exam
from pages.purchase_credits import show_purchase_credits, handle_payment_callback

# Configure Streamlit page
st.set_page_config(
    page_title="MockExamify",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
    font-weight: bold;
}

.credit-balance {
    background: linear-gradient(90deg, #ff7b7b, #ffb347);
    padding: 1rem;
    border-radius: 0.5rem;
    color: white;
    text-align: center;
    margin-bottom: 1rem;
}

.sidebar-info {
    background: #f0f8ff;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
}

/* Hide streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Custom button styles */
.stButton > button {
    border-radius: 0.5rem;
    border: none;
    background: linear-gradient(45deg, #1f77b4, #ff7f0e);
    color: white;
    font-weight: bold;
}

.stButton > button:hover {
    background: linear-gradient(45deg, #1a6ba3, #e6720d);
    transform: translateY(-1px);
}
</style>
""", unsafe_allow_html=True)

def main():
    """Main application logic"""
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
    """Show login/register page"""
    st.markdown('<h1 class="main-header">Welcome to MockExamify</h1>', unsafe_allow_html=True)
    st.markdown("### 🎯 Master Your Exams with AI-Powered Mock Tests")
    
    # Features showcase
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 📚 Comprehensive Exams
        - Industry-standard questions
        - Realistic exam scenarios
        - Detailed explanations
        """)
    
    with col2:
        st.markdown("""
        #### 🤖 AI-Powered Insights
        - Personalized explanations
        - Performance analytics
        - Smart recommendations
        """)
    
    with col3:
        st.markdown("""
        #### 💎 Credit System
        - Pay only for what you use
        - No monthly subscriptions
        - Credits never expire
        """)
    
    st.markdown("---")
    
    # Login/Register tabs
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Create Account"])
    
    with tab1:
        show_login_form(auth)
    
    with tab2:
        show_register_form(auth)

def show_login_form(auth: AuthUtils):
    """Display login form with validation"""
    st.markdown("### Login to Your Account")
    
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input(
            "Email Address",
            value=st.session_state.last_email,
            placeholder="your.email@example.com",
            help="Enter your registered email address"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            help="Enter your account password"
        )
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            login_submitted = st.form_submit_button("🔑 Login", use_container_width=True, type="primary")
        
        with col2:
            forgot_password = st.form_submit_button("🔄 Forgot Password?", use_container_width=True)
        
        if login_submitted:
            if not email or not password:
                st.error("Please fill in both email and password")
                return
            
            # Validate email format
            email_valid, email_error = validate_email(email)
            if not email_valid:
                st.error(email_error)
                return
            
            # Attempt login
            with st.spinner("Logging in..."):
                success, user_data, error_msg = run_async(auth.sign_in(email, password))
                
                if success and user_data:
                    # Store user session data
                    st.session_state.authenticated = True
                    st.session_state.user_token = user_data.get("token")
                    st.session_state.current_user = {
                        "id": user_data.get("user_id"),
                        "email": email,
                        "role": user_data.get("role", "user"),
                        "credits_balance": user_data.get("credits_balance", 0)
                    }
                    st.session_state.last_email = email
                    st.session_state.page = "dashboard"
                    
                    st.success("Login successful! Redirecting...")
                    st.rerun()
                else:
                    st.error(error_msg or "Login failed. Please check your credentials.")
        
        if forgot_password:
            st.info("Password reset feature coming soon! Contact support for assistance.")

def show_register_form(auth: AuthUtils):
    """Display registration form with validation"""
    st.markdown("### Create Your Account")
    
    with st.form("register_form", clear_on_submit=False):
        email = st.text_input(
            "Email Address",
            placeholder="your.email@example.com",
            help="This will be your login email"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Choose a strong password",
            help="Minimum 6 characters with letters and numbers"
        )
        
        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Re-enter your password"
        )
        
        terms_agreed = st.checkbox(
            "I agree to the Terms of Service and Privacy Policy",
            help="You must agree to continue"
        )
        
        register_submitted = st.form_submit_button("📝 Create Account", use_container_width=True, type="primary")
        
        if register_submitted:
            # Validation
            if not email or not password or not confirm_password:
                st.error("Please fill in all fields")
                return
            
            if not terms_agreed:
                st.error("Please agree to the Terms of Service to continue")
                return
            
            # Validate email
            email_valid, email_error = validate_email(email)
            if not email_valid:
                st.error(email_error)
                return
            
            # Validate password
            password_valid, password_error = validate_password(password, confirm_password)
            if not password_valid:
                st.error(password_error)
                return
            
            # Attempt registration
            with st.spinner("Creating your account..."):
                success, user_data, error_msg = run_async(auth.sign_up(email, password))
                
                if success:
                    st.success("Account created successfully! You can now log in.")
                    st.session_state.last_email = email
                    st.balloons()
                    # Switch to login tab would be ideal here
                else:
                    st.error(error_msg or "Registration failed. Please try again.")

def show_authenticated_app(auth: AuthUtils):
    """Show the main application for authenticated users"""
    # Sidebar navigation
    with st.sidebar:
        user = auth.get_current_user()
        
        # User info
        st.markdown(f"""
        <div class="sidebar-info">
            <h3>👋 Welcome!</h3>
            <p><strong>{user.get('email', 'User')}</strong></p>
            <p>💰 Credits: <strong>{user.get('credits_balance', 0)}</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation menu
        st.markdown("### 📱 Navigation")
        
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
        
        if st.button("💳 Purchase Credits", use_container_width=True):
            st.session_state.page = "purchase_credits"
            st.rerun()
        
        if st.button("📈 Past Attempts", use_container_width=True):
            st.session_state.page = "past_attempts"
            st.rerun()
        
        if st.button("💬 Contact Support", use_container_width=True):
            st.session_state.page = "contact"
            st.rerun()
        
        # Admin menu
        if auth.is_admin():
            st.markdown("---")
            st.markdown("### 👨‍💼 Admin Panel")
            
            if st.button("📤 Upload Mock", use_container_width=True):
                st.session_state.page = "admin_upload"
                st.rerun()
            
            if st.button("📝 Manage Mocks", use_container_width=True):
                st.session_state.page = "admin_manage"
                st.rerun()
            
            if st.button("🎫 Support Tickets", use_container_width=True):
                st.session_state.page = "admin_tickets"
                st.rerun()
        
        # Logout
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            auth.logout()
            st.session_state.page = "login"
            st.rerun()
    
    # Main content area
    page = st.session_state.get("page", "dashboard")
    
    if page == "dashboard":
        show_dashboard()
    elif page == "exam":
        show_exam()
    elif page == "purchase_credits":
        show_purchase_credits()
    elif page == "past_attempts":
        show_past_attempts()
    elif page == "contact":
        show_contact_page()
    elif page == "admin_upload":
        show_admin_upload()
    elif page == "admin_manage":
        show_admin_manage()
    elif page == "admin_tickets":
        show_admin_tickets()
    else:
        show_dashboard()

def show_contact_page():
    """Show contact/support form"""
    st.markdown("# 💬 Contact Support")
    
    with st.form("contact_form"):
        subject = st.selectbox(
            "Subject",
            ["General Question", "Technical Issue", "Billing Question", "Feature Request", "Other"]
        )
        
        message = st.text_area(
            "Message",
            placeholder="Please describe your question or issue in detail...",
            height=150
        )
        
        submitted = st.form_submit_button("📤 Send Message", type="primary")
        
        if submitted:
            if not message.strip():
                st.error("Please enter a message")
            else:
                # Here you would send the message to your support system
                st.success("Message sent successfully! We'll get back to you within 24 hours.")
                st.balloons()
    
    if st.button("🏠 Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()

def show_admin_upload():
    """Placeholder for admin upload page"""
    st.markdown("# 📤 Upload Mock Exam")
    st.info("Admin upload functionality coming soon!")
    
    if st.button("🏠 Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()

def show_admin_manage():
    """Placeholder for admin manage page"""
    st.markdown("# 📝 Manage Mock Exams")
    st.info("Admin management functionality coming soon!")
    
    if st.button("🏠 Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()

def show_admin_tickets():
    """Placeholder for admin tickets page"""
    st.markdown("# 🎫 Support Tickets")
    st.info("Support ticket management coming soon!")
    
    if st.button("🏠 Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()

if __name__ == "__main__":
    main()