try:
    from app_pages.dashboard import handle_dashboard_modals, show_dashboard
except ImportError:

    def show_dashboard():
        st.error("Dashboard functionality temporarily unavailable")

    def handle_dashboard_modals():
        pass


import streamlit as st

# Aggressive sidebar hiding CSS injected before anything else
st.markdown(
    """
<style>
section[data-testid="stSidebar"] {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    min-width: 0 !important;
    max-width: 0 !important;
    overflow: hidden !important;
}
[data-testid="collapsedControl"] {
    display: none !important;
    visibility: hidden !important;
}
[data-testid="stSidebarNav"] {
    display: none !important;
    visibility: hidden !important;
}
</style>
""",
    unsafe_allow_html=True,
)

from datetime import datetime
from typing import Any, Dict, Optional

import config
from auth_utils import AuthUtils, run_async, validate_email, validate_password

# ...existing code...


try:
    from app_pages.past_attempts import handle_modals, show_past_attempts
except ImportError:

    def show_past_attempts():
        st.error("Past attempts functionality temporarily unavailable")

    def handle_modals():
        pass


# Import exam page
try:
    from app_pages.exam import show_exam
except ImportError:

    def show_exam():
        st.error("Exam functionality temporarily unavailable")


# Import supporting pages
try:
    from app_pages.contact_support import show_contact_support
except ImportError:

    def show_contact_support():
        st.error("Contact support functionality temporarily unavailable")


try:
    from app_pages.purchase_credits import (
        handle_payment_callback,
        show_purchase_credits,
    )
except ImportError:

    def show_purchase_credits():
        st.error("Purchase credits functionality temporarily unavailable")

    def handle_payment_callback():
        pass


# Import legal pages
try:
    from app_pages.privacy_policy import show_privacy_page
    from app_pages.terms_of_service import show_terms_page
except ImportError:

    def show_terms_page():
        st.error("Terms of Service page temporarily unavailable")

    def show_privacy_page():
        st.error("Privacy Policy page temporarily unavailable")


# Import admin pages
try:
    from app_pages.admin_dashboard import show_admin_dashboard
    from app_pages.admin_manage import show_admin_manage
    from app_pages.admin_question_pools import show_admin_question_pools
    from app_pages.admin_upload import show_admin_upload
except ImportError as e:
    # Fallback if admin pages aren't available yet
    st.error(f"Admin pages import error: {e}")

    def show_admin_upload():
        st.info("Admin upload functionality coming soon!")

    def show_admin_manage():
        st.info("Admin management functionality coming soon!")

    def show_admin_dashboard():
        st.info("Admin dashboard functionality coming soon!")

    def show_admin_question_pools():
        st.info("Question pools functionality coming soon!")


# Configure Streamlit page
st.set_page_config(
    page_title="WantAMock - AI-Powered Mock Exams",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",  # Sidebar hidden permanently
    menu_items={
        "Get Help": "mailto:support@wantamock.com",
        "Report a bug": "mailto:support@wantamock.com",
        "About": "WantAMock - Master your exams with AI-powered mock tests!",
    },
)

# Enhanced Custom CSS with modern design
st.markdown(
    """
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* CRITICAL: Hide sidebar immediately on page load to prevent flashing */
section[data-testid="stSidebar"] {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    min-width: 0 !important;
    max-width: 0 !important;
    overflow: hidden !important;
}
[data-testid="collapsedControl"] {
    display: none !important;
    visibility: hidden !important;
}
[data-testid="stSidebarNav"] {
    display: none !important;
    visibility: hidden !important;
}

/* Global styles */
.stApp {
    font-family: 'Inter', sans-serif;
}

/* Main header styling */
.main-header {
    font-size: 4.5rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    margin-bottom: 2rem;
    font-weight: 700;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
}
/* Enlarge top-left app name/logo in header bar (robust selector) */
header .st-emotion-cache-1v0mbdj, header .st-emotion-cache-10trblm, header [data-testid="stHeader"] div, header [data-testid^="stApp"] div:first-child {
    font-size: 2.5rem !important;
    font-weight: 900 !important;
    color: #fff !important;
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

/* Label styling - removed hardcoded colors for theme compatibility */
.stTextInput > label,
.stTextArea > label,
.stSelectbox > label,
.stFileUploader > label {
    font-weight: 600 !important;
    font-size: 16px !important;
    margin-bottom: 0.5rem !important;
}

/* Form labels */
.stForm label {
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

/* Checkbox styling improvements - removed hardcoded colors for theme compatibility */
.stCheckbox > label {
    font-weight: 500 !important;
    color: #000000 !important;
}

.stCheckbox > label > div {
    color: #000000 !important;
}

.stCheckbox > label > div > p {
    color: #000000 !important;
}

/* Hide the emoji checkmark in checkbox label to avoid double checkmarks */
.stCheckbox > label > div > p::before {
    content: none !important;
}

/* Expander styling */
.streamlit-expanderHeader {
    background-color: #f7fafc;
    border-radius: 8px;
    color: #000000 !important;
    font-weight: 600;
}

.streamlit-expanderHeader p {
    color: #000000 !important;
}

.streamlit-expanderHeader svg {
    color: #000000 !important;
}

/* New expander styling for Streamlit updates */
.st-emotion-cache-p5msec {
    color: #000000 !important;
}

[data-testid="stExpander"] summary {
    color: #000000 !important;
}

[data-testid="stExpander"] summary p {
    color: #000000 !important;
}

.streamlit-expanderContent {
    background-color: white;
    color: #000000 !important;
    border: 1px solid #e2e8f0;
    border-radius: 0 0 8px 8px;
}

/* Expander content styling - allow custom colors */
/* Removed forced black color to allow pages to set their own text colors */

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

/* Error/Warning/Success message text color */
.stAlert p {
    color: #000000 !important;
}

.stAlert div {
    color: #000000 !important;
}

/* Error messages */
[data-testid="stNotificationContentError"] {
    color: #000000 !important;
}

/* Success messages */
[data-testid="stNotificationContentSuccess"] {
    color: #000000 !important;
}

/* Warning messages */
[data-testid="stNotificationContentWarning"] {
    color: #000000 !important;
}

/* Info messages */
[data-testid="stNotificationContentInfo"] {
    color: #000000 !important;
}

/* Checkbox styling */
.stCheckbox {
    margin: 1rem 0;
}

/* Loading spinner */
.stSpinner {
    text-align: center;
}

/* Fix dropdown arrows - make them visible and black */
/* Selectbox dropdown arrow */
.stSelectbox > div > div > div > div[data-baseweb="select"] > div {
    color: #000000 !important;
}

.stSelectbox [data-baseweb="select"] svg {
    fill: #000000 !important;
    color: #000000 !important;
}

/* Number input arrows/spinners */
.stNumberInput > div > div > input[type="number"] {
    color: #000000 !important;
}

.stNumberInput > div > div > div > button {
    color: #000000 !important;
}

.stNumberInput > div > div > div > button svg {
    fill: #000000 !important;
    color: #000000 !important;
}

/* All select dropdown indicators */
[data-baseweb="select"] svg {
    fill: #000000 !important;
}

/* Ensure dropdown arrow is visible */
select::-ms-expand {
    color: #000000 !important;
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
""",
    unsafe_allow_html=True,
)


def main():
    """Main application logic with enhanced UI"""
    import logging

    logger = logging.getLogger(__name__)

    # EMERGENCY DEBUG - Log at entry point
    logger.info("\n" + "=" * 80)
    logger.info("[MAIN] Application starting")
    logger.info(f"[MAIN] Query params: {dict(st.query_params)}")
    logger.info(f"[MAIN] Session state: {dict(st.session_state)}")
    logger.info("=" * 80 + "\n")

    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "login"
    if "last_email" not in st.session_state:
        st.session_state.last_email = ""

    # Initialize auth utility
    auth = AuthUtils(config.API_BASE_URL)

    # Handle payment callbacks
    query_params = st.query_params
    logger.info(
        f"[MAIN] Checking for payment callback. Has 'payment' key: {'payment' in query_params}"
    )

    if "payment" in query_params:
        logger.info("[MAIN] Payment callback detected - calling handle_payment_callback()")
        handle_payment_callback()
        logger.info("[MAIN] Payment callback done - returning early")
        return

    # Check if viewing legal pages (accessible without authentication)
    current_page = st.session_state.get("page", "login")
    if current_page == "terms_of_service":
        show_terms_page()
        return
    elif current_page == "privacy_policy":
        show_privacy_page()
        return

    # Check authentication status
    if auth.is_authenticated():
        show_authenticated_app(auth)
    else:
        show_authentication_page(auth)


def show_authentication_page(auth: AuthUtils):
    """Enhanced authentication page with better design"""

    # Hide sidebar permanently with aggressive CSS to prevent flashing
    st.markdown(
        """
    <style>
    /* Aggressive sidebar hiding - prevents flash on load */
    section[data-testid="stSidebar"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
    }
    [data-testid="collapsedControl"] {
        display: none !important;
        visibility: hidden !important;
    }
    [data-testid="stSidebarNav"] {
        display: none !important;
        visibility: hidden !important;
    }
    /* Hide the sidebar toggle button */
    button[kind="header"] {
        display: none !important;
    }

    /* Fix form label and placeholder text colors */
    .stTextInput label {
        color: #000000 !important;
    }
    .stTextInput input::placeholder {
        color: #666666 !important;
        opacity: 1 !important;
    }
    .stTextInput input {
        color: #000000 !important;
    }

    /* Remove top whitespace on landing page */
    .block-container {
        padding-top: 1rem !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Hero section
    st.markdown(
        """
    <div class="welcome-section">
            <!-- Removed large header -->
        <p>Master Your Exams with AI-Powered Mock Tests</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Features showcase with enhanced cards
    st.markdown("## Why Choose WantAMock?")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
        <div class="feature-card">
            <h4>📚 Comprehensive Exams</h4>
            <p>• Industry-standard questions</p>
            <p>• Realistic exam scenarios</p>
            <p>• Detailed performance analysis</p>
            <p>• Multiple difficulty levels</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div class="feature-card">
            <h4>🤖 AI-Powered Insights</h4>
            <p>• Personalized explanations</p>
            <p>• Smart performance analytics</p>
            <p>• Adaptive recommendations</p>
            <p>• Learning path optimization</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
        <div class="feature-card">
            <h4>💎 Flexible Pricing</h4>
            <p>• Pay-per-exam credit system</p>
            <p>• No monthly subscriptions</p>
            <p>• Credits never expire</p>
            <p>• Bulk purchase discounts</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<p style='text-align: center; color: #666; font-size: 0.95rem; margin-top: 1.5rem;'>Trusted by finance professionals preparing for CACS & CMFAS exams.</p>", unsafe_allow_html=True)

    st.markdown("---")

    # Free trial announcement with custom styling for visibility in both light and dark modes
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 0.75rem;
            margin: 1rem 0 2rem 0;
            box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
            border-left: 5px solid #ffd700;
        ">
            <p style="color: white; margin: 0; font-size: 1.1rem; line-height: 1.6;">
                🎁 <strong>New users receive 1 FREE trial credit!</strong> Sign up now to test our platform and experience AI-powered mock exams.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Enhanced Login/Register tabs
    st.markdown("<p style='text-align: center; color: #666; font-size: 0.9rem; margin-bottom: 0.5rem;'>No credit card needed to start.</p>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔑 Sign In", "✨ Start Free Trial"])

    with tab1:
        show_enhanced_login_form(auth)

    with tab2:
        show_enhanced_register_form(auth)

    # FAQ Section (collapsible)
    st.markdown("---")
    with st.expander("❓ FAQ"):
        st.markdown("""
**Are these real exam questions?**
No — they are AI-generated questions designed to mirror the style and difficulty of CACS/CMFAS papers.

**How accurate are the explanations?**
Every explanation is generated by AI based on regulatory concepts and best practices.

**Will more exams be added?**
Yes. You can request new exams directly from the dashboard.

**How does the free trial work?**
New users receive 1 free credit to try a full mock paper.
""")

    # Help & Support footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; padding: 1rem; background-color: #f8f9fa; border-radius: 0.5rem; margin-top: 2rem;">
            <p style="color: #666666; margin: 0;">
                <strong>Need help?</strong> Use the "🔑 Forgot Password?" button on the Sign In tab to reset your password,
                or access <strong>Contact Support</strong> after logging in for other assistance.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Footer with last updated timestamp and recent updates
    st.markdown("---")
    from datetime import datetime
    import json
    from pathlib import Path

    current_month_year = datetime.now().strftime("%B %Y")
    st.markdown(f"<p style='text-align: center; color: #888; font-size: 0.8rem;'>Last updated: {current_month_year}</p>", unsafe_allow_html=True)

    # Load and display recent updates
    try:
        updates_file = Path(__file__).parent / "updates.json"
        with open(updates_file, "r") as f:
            updates = json.load(f)[:3]  # Get last 3 updates

        with st.expander("📢 Recent Updates"):
            for update in updates:
                st.markdown(f"**{update['date']}** — {update['text']}")
    except Exception:
        pass  # Silently fail if updates file doesn't exist


def show_enhanced_login_form(auth: AuthUtils):
    """Enhanced login form with better UX"""

    # Check if showing password reset form
    if st.session_state.get("show_password_reset_form", False):
        show_password_reset_ticket_form()
        return

    st.markdown('<h3 style="color: #000000;">Welcome Back!</h3>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color: #333333;">Sign in to access your mock exams and track your progress.</p>',
        unsafe_allow_html=True,
    )

    # Quick login buttons for development
    try:
        import logging

        logger = logging.getLogger(__name__)
        is_dev = config.ENVIRONMENT == "development"
        logger.info(f"Quick login check: ENVIRONMENT={config.ENVIRONMENT}, is_dev={is_dev}")

        # Show quick login if development mode (works with both demo and production database)
        if is_dev:
            st.markdown(
                """
            <div style="background-color: #e8f4f8; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #0066cc; margin-bottom: 1rem;">
                <p style="color: #000000; margin: 0; font-weight: 500;">🚀 <strong>Quick Login</strong> (Development Mode)</p>
            </div>
            """,
                unsafe_allow_html=True,
            )
            col1, col2 = st.columns(2)

            with col1:
                if st.button("👨‍💼 Login as Admin", use_container_width=True, type="secondary"):
                    # Auto-login as admin
                    st.session_state.authenticated = True
                    st.session_state.current_user = {
                        "id": "admin-demo-id",
                        "email": "admin@mockexamify.com",
                        "role": "admin",
                        "credits_balance": 100,
                    }
                    st.session_state.page = "dashboard"
                    st.rerun()

            with col2:
                if st.button("👨‍🎓 Login as Student", use_container_width=True, type="secondary"):
                    # Auto-login as student
                    st.session_state.authenticated = True
                    st.session_state.current_user = {
                        "id": "student-demo-id",
                        "email": "student@test.com",
                        "role": "user",
                        "credits_balance": 3,
                    }
                    st.session_state.page = "dashboard"
                    st.rerun()
    except Exception as e:
        # Log error but don't show to user
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Quick login setup failed: {e}")

    # Login form
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input(
            "📧 Email Address",
            value=st.session_state.last_email,
            placeholder="your.email@example.com",
            help="Enter your registered email address",
        )

        password = st.text_input(
            "🔒 Password",
            type="password",
            placeholder="Enter your password",
            help="Enter your password",
        )

        col1, col2 = st.columns(2)
        with col1:
            login_submitted = st.form_submit_button("Sign In", use_container_width=True)
        with col2:
            forgot_password = st.form_submit_button("🔑 Forgot Password?", use_container_width=True)

        if forgot_password:
            st.session_state.show_password_reset_form = True
            st.rerun()

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
                    "credits_balance": user_data.get("credits_balance", 0),
                }
                st.session_state.last_email = email
                st.session_state.page = "dashboard"

                st.success("🎉 Welcome back! Redirecting to your dashboard...")
                st.rerun()
            else:
                st.markdown(
                    f'<p style="color: black;">❌ {error_msg or "Login failed. Please check your credentials."}</p>',
                    unsafe_allow_html=True,
                )


def show_password_reset_ticket_form():
    """Show password reset request form (pre-login)"""
    st.markdown(
        '<h3 style="color: #000000;">🔑 Request Password Reset</h3>', unsafe_allow_html=True
    )
    st.markdown(
        '<p style="color: #333333;">Submit a password reset request. An administrator will reset your password and contact you.</p>',
        unsafe_allow_html=True,
    )

    # Add CSS to make form labels black
    st.markdown(
        """
        <style>
        .stTextInput label, .stTextArea label {
            color: #000000 !important;
        }
        .stTextInput label span, .stTextArea label span {
            color: #000000 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Back to login button
    if st.button("⬅️ Back to Login"):
        st.session_state.show_password_reset_form = False
        st.rerun()

    st.markdown("---")

    with st.form("password_reset_ticket_form"):
        email = st.text_input(
            "📧 Your Email Address",
            placeholder="email@example.com",
            help="Enter the email address associated with your account",
        )

        description = st.text_area(
            "📄 Additional Information (Optional)",
            placeholder="Provide any additional details that might help us verify your identity...",
            height=100,
            help="You can include information like when you created the account, last login, etc.",
        )

        submitted = st.form_submit_button(
            "🚀 Submit Password Reset Request", type="primary", use_container_width=True
        )

        if submitted:
            if not email:
                st.error("⚠️ Please enter your email address")
            else:
                # Validate email
                email_valid, email_error = validate_email(email)
                if not email_valid:
                    st.error(f"⚠️ {email_error}")
                else:
                    # Create support ticket
                    # Use a special UUID for anonymous/pre-login tickets
                    import uuid

                    anonymous_uuid = "00000000-0000-0000-0000-000000000000"

                    ticket_data = {
                        "user_id": anonymous_uuid,  # Special UUID for pre-login tickets
                        "user_email": email,
                        "subject": "Password Reset Request",
                        "description": f"User requested password reset for account: {email}\n\nAdditional information:\n{description or 'None provided'}",
                        "category": "Account & Login",
                        "priority": "High",
                        "browser": "",
                        "device": "",
                        "error_message": "",
                        "affected_exam": "",
                        "email_updates": True,
                        "status": "Open",
                        "created_at": datetime.now().isoformat(),
                    }

                    ticket_id = run_async(create_password_reset_ticket(ticket_data))

                    if ticket_id:
                        st.success(
                            f"✅ Password reset request submitted successfully! Ticket ID: **{ticket_id}**"
                        )
                        st.info(
                            "📬 An administrator will review your request and reset your password. "
                            "You will be contacted at the email address you provided."
                        )
                        st.balloons()

                        # Auto-redirect to login after successful submission
                        st.session_state.show_password_reset_form = False
                    else:
                        st.error(
                            "❌ Failed to submit request. Please try again or contact support directly."
                        )


def show_enhanced_register_form(auth: AuthUtils):
    """Enhanced registration form with better UX"""
    st.markdown('<h3 style="color: #000000;">Join WantAMock Today!</h3>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color: #333333;">Create your account and get <strong>1 free trial credit</strong> to start practicing!</p>',
        unsafe_allow_html=True,
    )

    with st.form("register_form", clear_on_submit=False):
        email = st.text_input(
            "📧 Email Address",
            placeholder="your.email@example.com",
            help="This will be your login email",
        )

        password = st.text_input(
            "🔒 Password",
            type="password",
            placeholder="Choose a strong password",
            help="Minimum 6 characters with letters and numbers",
        )

        confirm_password = st.text_input(
            "🔒 Confirm Password", type="password", placeholder="Re-enter your password"
        )

        terms_agreed = st.checkbox(
            "I agree to the Terms of Service and Privacy Policy", help="You must agree to continue"
        )

        register_submitted = st.form_submit_button(
            "🎯 Create My Account", use_container_width=True, type="primary"
        )

        if register_submitted:
            # Enhanced validation with better feedback
            if not email or not password or not confirm_password:
                st.error("⚠️ Please fill in all fields")
                return

            if not terms_agreed:
                st.markdown(
                    '<p style="color: black;">⚠️ Please agree to the Terms of Service to continue</p>',
                    unsafe_allow_html=True,
                )
                return

            # Validate email
            email_valid, email_error = validate_email(email)
            if not email_valid:
                st.error(f"⚠️ {email_error}")
                return

            # Validate password
            password_valid, password_error = validate_password(password, confirm_password)
            if not password_valid:
                st.markdown(
                    f'<p style="color: black;">⚠️ {password_error}</p>', unsafe_allow_html=True
                )
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
                        "credits_balance": user_data.get("credits_balance", 5),
                    }
                    st.session_state.last_email = email
                    st.session_state.page = "dashboard"

                    st.success("🎉 Account created successfully! Welcome to WantAMock!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ {error_msg or 'Registration failed. Please try again.'}")

    # Links to legal documents (outside form) - using expanders to show inline
    st.markdown(
        '<p style="color: #666666; text-align: center; font-size: 0.9rem; margin: 1rem 0 0.5rem 0;">By creating an account, you agree to our legal terms. Click to read:</p>',
        unsafe_allow_html=True,
    )

    from pathlib import Path

    col1, col2 = st.columns(2)
    with col1:
        with st.expander("📜 Terms of Service", expanded=False):
            try:
                # Add CSS to force black text
                st.markdown(
                    """
                    <style>
                    /* Force black text in Terms of Service */
                    div[data-testid="stExpander"] p,
                    div[data-testid="stExpander"] h1,
                    div[data-testid="stExpander"] h2,
                    div[data-testid="stExpander"] h3,
                    div[data-testid="stExpander"] h4,
                    div[data-testid="stExpander"] h5,
                    div[data-testid="stExpander"] h6,
                    div[data-testid="stExpander"] li,
                    div[data-testid="stExpander"] span,
                    div[data-testid="stExpander"] div,
                    div[data-testid="stExpander"] strong,
                    div[data-testid="stExpander"] em {
                        color: #000000 !important;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                tos_path = Path(__file__).parent / "legal" / "terms_of_service.md"
                with open(tos_path, "r", encoding="utf-8") as f:
                    tos_content = f.read()
                st.markdown(tos_content, unsafe_allow_html=True)
            except FileNotFoundError:
                st.error("Terms of Service document not found.")

    with col2:
        with st.expander("🔒 Privacy Policy", expanded=False):
            try:
                # Add CSS to force black text
                st.markdown(
                    """
                    <style>
                    /* Force black text in Privacy Policy */
                    div[data-testid="stExpander"] p,
                    div[data-testid="stExpander"] h1,
                    div[data-testid="stExpander"] h2,
                    div[data-testid="stExpander"] h3,
                    div[data-testid="stExpander"] h4,
                    div[data-testid="stExpander"] h5,
                    div[data-testid="stExpander"] h6,
                    div[data-testid="stExpander"] li,
                    div[data-testid="stExpander"] span,
                    div[data-testid="stExpander"] div,
                    div[data-testid="stExpander"] strong,
                    div[data-testid="stExpander"] em {
                        color: #000000 !important;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                privacy_path = Path(__file__).parent / "legal" / "privacy_policy.md"
                with open(privacy_path, "r", encoding="utf-8") as f:
                    privacy_content = f.read()
                st.markdown(privacy_content, unsafe_allow_html=True)
            except FileNotFoundError:
                st.error("Privacy Policy document not found.")


def show_authenticated_app(auth: AuthUtils):
    """Enhanced authenticated app with improved navigation"""

    # Hide sidebar permanently
    st.markdown(
        """
    <style>
    section[data-testid="stSidebar"] {display: none !important;}
    [data-testid="collapsedControl"] {display: none !important;}
    </style>
    """,
        unsafe_allow_html=True,
    )

    user = auth.get_current_user()
    credits = user.get("credits_balance", 0)

    # Top navigation bar with user info - with gradient background for visibility
    st.markdown(
        """
        <style>
        .nav-bar-container {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .nav-bar-container h3,
        .nav-bar-container p,
        .nav-bar-container strong {
            color: white !important;
            margin: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Navigation bar with gradient background
    nav_html = f"""
    <div class="nav-bar-container">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="flex: 2;">
                <h3 style="margin: 0; color: white;">🎯 WantAMock</h3>
            </div>
            <div style="flex: 1; text-align: right;">
                <p style="margin: 0; color: white;"><strong>💰 Credits:</strong> {credits}</p>
            </div>
            <div style="flex: 1; text-align: right;">
                <p style="margin: 0; color: white;"><strong>👤</strong> {user.get("email", "User")}</p>
            </div>
        </div>
    </div>
    """
    st.html(nav_html)

    st.markdown("---")

    # Navigation: Only logout button
    col_spacer, col_logout = st.columns([9, 1])

    with col_logout:
        if st.button("🚪 Logout", use_container_width=True):
            auth.logout()
            st.session_state.page = "login"
            st.rerun()

    st.markdown("---")

    # Enhanced main content area with better routing
    page = st.session_state.get("page", "dashboard")
    print(f"DEBUG: Routing to page: {page}")

    # EMERGENCY DEBUG - Log routing
    import logging

    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info(f"[ROUTING] About to route to page: {page}")
    logger.info(f"[ROUTING] Query params: {dict(st.query_params)}")
    logger.info(f"[ROUTING] User: {user.get('email', 'unknown')}")
    logger.info("=" * 80)

    # Route to appropriate page (each page handles its own header)
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
    elif page == "admin_question_pools":
        show_admin_question_pools()
    elif page == "admin_tickets":
        show_admin_tickets()
    elif page == "terms_of_service":
        show_terms_page()
    elif page == "privacy_policy":
        show_privacy_page()
    else:
        show_dashboard()
        handle_dashboard_modals()

    # Footer with last updated timestamp
    st.markdown("---")
    from datetime import datetime
    current_month_year = datetime.now().strftime("%B %Y")
    st.markdown(f"<p style='text-align: center; color: #888; font-size: 0.8rem;'>Last updated: {current_month_year}</p>", unsafe_allow_html=True)


async def create_password_reset_ticket(ticket_data: Dict[str, Any]) -> Optional[str]:
    """Create a password reset support ticket (pre-login)"""
    try:
        from db import db

        # Create ticket in database
        ticket_id = await db.create_support_ticket(ticket_data)
        return ticket_id
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error creating password reset ticket: {e}")
        return None


def show_admin_tickets():
    """Enhanced admin tickets management"""
    from app_pages.admin_tickets import show_admin_tickets as show_tickets_page

    show_tickets_page()


if __name__ == "__main__":
    main()
