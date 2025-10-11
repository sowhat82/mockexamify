"""
MockExamify - Enhanced Streamlit Application
Interactive Mock Exam Platform with Credit System
"""
import streamlit as st
import config
from auth_utils import AuthUtils, validate_email, validate_password, run_async

# Import enhanced pages
try:
    from pages.dashboard import show_dashboard, handle_dashboard_modals
except ImportError:
    def show_dashboard():
        st.error("Dashboard functionality temporarily unavailable")
    def handle_dashboard_modals():
        pass

try:
    from pages.exam import show_exam
except ImportError:
    def show_exam():
        st.error("Exam functionality temporarily unavailable")

try:
    from pages.purchase_credits import show_purchase_credits, handle_payment_callback
except ImportError:
    def show_purchase_credits():
        st.error("Purchase functionality temporarily unavailable")
    def handle_payment_callback():
        pass

try:
    from pages.past_attempts import show_past_attempts, handle_modals
except ImportError:
    def show_past_attempts():
        st.error("Past attempts functionality temporarily unavailable")
    def handle_modals():
        pass

try:
    from pages.contact_support import show_contact_support
except ImportError:
    def show_contact_support():
        st.error("Contact support functionality temporarily unavailable")

# Import admin pages
try:
    from pages.admin_upload import show_admin_upload
    from pages.admin_manage import show_admin_manage
    from pages.admin_dashboard import show_admin_dashboard
except ImportError:
    # Fallback if admin pages aren't available yet
    def show_admin_upload():
        st.info("Admin upload functionality coming soon!")
    def show_admin_manage():
        st.info("Admin management functionality coming soon!")
    def show_admin_dashboard():
        st.info("Admin dashboard functionality coming soon!")

# Configure Streamlit page
st.set_page_config(
    page_title="MockExamify - AI-Powered Mock Exams",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'mailto:support@mockexamify.com',
        'Report a bug': 'mailto:support@mockexamify.com',
        'About': "MockExamify - Master your exams with AI-powered mock tests!"
    }
)

# Enhanced Custom CSS with modern design
st.markdown("""
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Global styles */
.stApp {
    font-family: 'Inter', sans-serif;
}

/* Main header styling */
.main-header {
    font-size: 3rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    margin-bottom: 2rem;
    font-weight: 700;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
}

.sub-header {
    font-size: 1.5rem;
    color: #4a5568;
    text-align: center;
    margin-bottom: 3rem;
    font-weight: 400;
}

/* Credit balance card */
.credit-balance {
    background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%);
    padding: 1.5rem;
    border-radius: 15px;
    color: white;
    text-align: center;
    margin-bottom: 1.5rem;
    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    border: 1px solid rgba(255,255,255,0.2);
}

.credit-balance h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.2rem;
    font-weight: 600;
}

.credit-balance .amount {
    font-size: 2rem;
    font-weight: 700;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
}

/* Sidebar styling */
.sidebar-info {
    background: linear-gradient(135deg, #f7f9fc 0%, #e9ecef 100%);
    padding: 1.5rem;
    border-radius: 15px;
    margin-bottom: 1.5rem;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.sidebar-info h3 {
    color: #2d3748;
    margin-bottom: 1rem;
    font-size: 1.3rem;
    font-weight: 600;
}

.sidebar-info p {
    color: #4a5568;
    margin: 0.5rem 0;
    font-size: 0.95rem;
}

/* Feature cards */
.feature-card {
    background: white;
    padding: 2rem;
    border-radius: 20px;
    margin-bottom: 2rem;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    border: 1px solid #e2e8f0;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.feature-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 40px rgba(0,0,0,0.15);
}

.feature-card h4 {
    color: #2d3748;
    font-size: 1.3rem;
    font-weight: 600;
    margin-bottom: 1rem;
}

.feature-card p {
    color: #4a5568;
    line-height: 1.6;
    margin: 0.5rem 0;
}

/* Navigation section headers */
.nav-section {
    color: #718096;
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 1.5rem 0 0.5rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #e2e8f0;
}

/* Welcome section */
.welcome-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 3rem 2rem;
    border-radius: 20px;
    margin-bottom: 3rem;
    text-align: center;
}

.welcome-section h2 {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 1rem;
}

.welcome-section p {
    font-size: 1.2rem;
    opacity: 0.9;
    margin-bottom: 0;
}

/* Login/Register tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 2rem;
    background: #f7fafc;
    padding: 0.5rem;
    border-radius: 15px;
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 10px;
    color: #4a5568;
    font-weight: 500;
    padding: 1rem 2rem;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: 600;
}

/* Form styling */
.stForm {
    background: white;
    padding: 2rem;
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    border: 1px solid #e2e8f0;
}

/* Input field styling */
.stTextInput > div > div > input {
    background-color: #f7fafc;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    color: #2d3748;
    font-size: 16px;
}

.stTextInput > div > div > input:focus {
    border-color: #667eea;
    box-shadow: 0 0 0 1px #667eea;
}

.stTextArea > div > div > textarea {
    background-color: #f7fafc;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    color: #2d3748;
    font-size: 16px;
}

.stTextArea > div > div > textarea:focus {
    border-color: #667eea;
    box-shadow: 0 0 0 1px #667eea;
}

/* Select box styling */
.stSelectbox > div > div > div {
    background-color: #f7fafc;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    color: #2d3748;
}

/* Label styling */
.stTextInput > label,
.stTextArea > label,
.stSelectbox > label,
.stFileUploader > label {
    color: #2d3748 !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    margin-bottom: 0.5rem !important;
}

/* Form labels */
.stForm label {
    color: #2d3748 !important;
    font-weight: 600 !important;
}

/* Tab content styling */
.stTabs > div > div > div > div {
    background: white;
    border-radius: 15px;
    padding: 2rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

/* File uploader styling */
.stFileUploader > div {
    background-color: #f7fafc;
    border: 2px dashed #cbd5e0;
    border-radius: 8px;
    color: #4a5568;
}

/* Checkbox styling improvements */
.stCheckbox > label {
    color: #2d3748 !important;
    font-weight: 500 !important;
}

/* Expander styling */
.streamlit-expanderHeader {
    background-color: #f7fafc;
    border-radius: 8px;
    color: #2d3748;
    font-weight: 600;
}

.streamlit-expanderContent {
    background-color: white;
    color: #4a5568;
    border: 1px solid #e2e8f0;
    border-radius: 0 0 8px 8px;
}

/* Button styling */
.stButton > button {
    border-radius: 12px;
    border: none;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: 600;
    padding: 0.8rem 2rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.stButton > button:hover {
    background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.stButton > button:active {
    transform: translateY(0);
}

/* Primary button variant */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
    box-shadow: 0 4px 12px rgba(72, 187, 120, 0.3);
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
    box-shadow: 0 8px 20px rgba(72, 187, 120, 0.4);
}

/* Secondary button variant */
.stButton > button[kind="secondary"] {
    background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
    box-shadow: 0 4px 12px rgba(237, 137, 54, 0.3);
}

.stButton > button[kind="secondary"]:hover {
    background: linear-gradient(135deg, #dd6b20 0%, #c05621 100%);
    box-shadow: 0 8px 20px rgba(237, 137, 54, 0.4);
}

/* Hide streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Alert styling */
.stAlert {
    border-radius: 12px;
    border: none;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

/* Checkbox styling */
.stCheckbox {
    margin: 1rem 0;
}

/* Loading spinner */
.stSpinner {
    text-align: center;
}

/* Responsive design */
@media (max-width: 768px) {
    .main-header {
        font-size: 2rem;
    }
    
    .welcome-section {
        padding: 2rem 1rem;
    }
    
    .welcome-section h2 {
        font-size: 2rem;
    }
    
    .feature-card {
        padding: 1.5rem;
    }
}
</style>
""", unsafe_allow_html=True)

def main():
    """Main application logic with enhanced UI"""
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
    """Enhanced authentication page with better design"""
    # Hero section
    st.markdown("""
    <div class="welcome-section">
        <h2>🎯 MockExamify</h2>
        <p>Master Your Exams with AI-Powered Mock Tests</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Features showcase with enhanced cards
    st.markdown("## Why Choose MockExamify?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4>📚 Comprehensive Exams</h4>
            <p>• Industry-standard questions</p>
            <p>• Realistic exam scenarios</p>
            <p>• Detailed performance analysis</p>
            <p>• Multiple difficulty levels</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>🤖 AI-Powered Insights</h4>
            <p>• Personalized explanations</p>
            <p>• Smart performance analytics</p>
            <p>• Adaptive recommendations</p>
            <p>• Learning path optimization</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h4>💎 Flexible Pricing</h4>
            <p>• Pay-per-exam credit system</p>
            <p>• No monthly subscriptions</p>
            <p>• Credits never expire</p>
            <p>• Bulk purchase discounts</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Enhanced Login/Register tabs
    tab1, tab2 = st.tabs(["🔑 Sign In", "✨ Create Account"])
    
    with tab1:
        show_enhanced_login_form(auth)
    
    with tab2:
        show_enhanced_register_form(auth)

def show_enhanced_login_form(auth: AuthUtils):
    """Enhanced login form with better UX"""
    st.markdown("### Welcome Back!")
    st.markdown("Sign in to access your mock exams and track your progress.")
    
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input(
            "📧 Email Address",
            value=st.session_state.last_email,
            placeholder="your.email@example.com",
            help="Enter your registered email address"
        )
        
        password = st.text_input(
            "🔒 Password",
            type="password",
            placeholder="Enter your password",
            help="Enter your account password"
        )
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            login_submitted = st.form_submit_button(
                "🚀 Sign In", 
                use_container_width=True, 
                type="primary"
            )
        
        with col2:
            forgot_password = st.form_submit_button(
                "❓ Forgot Password?", 
                use_container_width=True
            )
        
        if login_submitted:
            if not email or not password:
                st.error("⚠️ Please fill in both email and password")
                return
            
            # Validate email format
            email_valid, email_error = validate_email(email)
            if not email_valid:
                st.error(f"⚠️ {email_error}")
                return
            
            # Attempt login with enhanced feedback
            with st.spinner("🔄 Signing you in..."):
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
                    
                    st.success("🎉 Welcome back! Redirecting to your dashboard...")
                    st.rerun()
                else:
                    st.error(f"❌ {error_msg or 'Login failed. Please check your credentials.'}")
        
        if forgot_password:
            st.info("🔄 Password reset feature coming soon! Contact support for assistance.")

def show_enhanced_register_form(auth: AuthUtils):
    """Enhanced registration form with better UX"""
    st.markdown("### Join MockExamify Today!")
    st.markdown("Create your account and get **5 free credits** to start practicing!")
    
    with st.form("register_form", clear_on_submit=False):
        email = st.text_input(
            "📧 Email Address",
            placeholder="your.email@example.com",
            help="This will be your login email"
        )
        
        password = st.text_input(
            "🔒 Password",
            type="password",
            placeholder="Choose a strong password",
            help="Minimum 6 characters with letters and numbers"
        )
        
        confirm_password = st.text_input(
            "🔒 Confirm Password",
            type="password",
            placeholder="Re-enter your password"
        )
        
        terms_agreed = st.checkbox(
            "✅ I agree to the Terms of Service and Privacy Policy",
            help="You must agree to continue"
        )
        
        register_submitted = st.form_submit_button(
            "🎯 Create My Account", 
            use_container_width=True, 
            type="primary"
        )
        
        if register_submitted:
            # Enhanced validation with better feedback
            if not email or not password or not confirm_password:
                st.error("⚠️ Please fill in all fields")
                return
            
            if not terms_agreed:
                st.error("⚠️ Please agree to the Terms of Service to continue")
                return
            
            # Validate email
            email_valid, email_error = validate_email(email)
            if not email_valid:
                st.error(f"⚠️ {email_error}")
                return
            
            # Validate password
            password_valid, password_error = validate_password(password, confirm_password)
            if not password_valid:
                st.error(f"⚠️ {password_error}")
                return
            
            # Attempt registration with enhanced feedback
            with st.spinner("🚀 Creating your account..."):
                success, user_data, error_msg = run_async(auth.sign_up(email, password))
                
                if success and user_data:
                    # Automatically log the user in after successful registration
                    st.session_state.authenticated = True
                    st.session_state.user_token = user_data.get("token")
                    st.session_state.current_user = {
                        "id": user_data.get("user_id"),
                        "email": email,
                        "role": user_data.get("role", "user"),
                        "credits_balance": user_data.get("credits_balance", 5)
                    }
                    st.session_state.last_email = email
                    st.session_state.page = "dashboard"
                    
                    st.success("🎉 Account created successfully! Welcome to MockExamify!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ {error_msg or 'Registration failed. Please try again.'}")

def show_authenticated_app(auth: AuthUtils):
    """Enhanced authenticated app with improved navigation"""
    # Enhanced sidebar navigation
    with st.sidebar:
        user = auth.get_current_user()
        
        # Enhanced user info card
        st.markdown(f"""
        <div class="sidebar-info">
            <h3>👋 Welcome Back!</h3>
            <p><strong>📧 {user.get('email', 'User')}</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced credit balance display
        credits = user.get('credits_balance', 0)
        st.markdown(f"""
        <div class="credit-balance">
            <h3>💰 Your Credits</h3>
            <div class="amount">{credits}</div>
            <p>{"Ready to explore!" if credits > 0 else "Purchase credits to start practicing"}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Main navigation
        st.markdown('<div class="nav-section">📱 Main Menu</div>', unsafe_allow_html=True)
        
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
            st.session_state.page = "contact_support"
            st.rerun()
        
        # Enhanced admin menu
        if auth.is_admin():
            st.markdown('<div class="nav-section">👨‍💼 Admin Panel</div>', unsafe_allow_html=True)
            
            if st.button("📊 Admin Dashboard", use_container_width=True):
                st.session_state.page = "admin_dashboard"
                st.rerun()
            
            if st.button("📤 Upload Mock", use_container_width=True):
                st.session_state.page = "admin_upload"
                st.rerun()
            
            if st.button("📝 Manage Mocks", use_container_width=True):
                st.session_state.page = "admin_manage"
                st.rerun()
            
            if st.button("🎫 Support Tickets", use_container_width=True):
                st.session_state.page = "admin_tickets"
                st.rerun()
        
        # Enhanced logout section
        st.markdown('<div class="nav-section">👤 Account</div>', unsafe_allow_html=True)
        if st.button("🚪 Sign Out", use_container_width=True):
            auth.logout()
            st.session_state.page = "login"
            st.rerun()
    
    # Enhanced main content area with better routing
    page = st.session_state.get("page", "dashboard")
    
    # Add page breadcrumb
    page_titles = {
        "dashboard": "🏠 Dashboard",
        "exam": "📝 Mock Exam",
        "purchase_credits": "💳 Purchase Credits",
        "past_attempts": "📈 Past Attempts",
        "contact_support": "💬 Contact Support",
        "admin_dashboard": "📊 Admin Dashboard",
        "admin_upload": "📤 Upload Mock",
        "admin_manage": "📝 Manage Mocks",
        "admin_tickets": "🎫 Support Tickets"
    }
    
    current_title = page_titles.get(page, "🏠 Dashboard")
    st.markdown(f"# {current_title}")
    
    # Route to appropriate page
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
    elif page == "contact_support":
        show_contact_support()
    elif page == "admin_dashboard":
        show_admin_dashboard()
    elif page == "admin_upload":
        show_admin_upload()
    elif page == "admin_manage":
        show_admin_manage()
    elif page == "admin_tickets":
        show_admin_tickets()
    else:
        show_dashboard()
        handle_dashboard_modals()

def show_admin_tickets():
    """Enhanced admin tickets management"""
    st.markdown("### 🎫 Support Tickets Management")
    st.info("📧 Support ticket management functionality coming soon!")
    
    # Placeholder for future ticket management features
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Open Tickets", "0", "0")
    
    with col2:
        st.metric("Resolved Today", "0", "0")
    
    with col3:
        st.metric("Avg Response Time", "< 24h", "0h")
    
    if st.button("🏠 Back to Dashboard", type="primary"):
        st.session_state.page = "dashboard"
        st.rerun()

if __name__ == "__main__":
    main()