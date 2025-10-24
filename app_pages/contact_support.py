"""
Contact Support page for MockExamify
Comprehensive support ticket system and help resources
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

import config
from auth_utils import AuthUtils, run_async


def show_contact_support():
    """Display the comprehensive support page"""
    auth = AuthUtils(config.API_BASE_URL)

    if not auth.is_authenticated():
        st.error("Please log in to access support")
        st.stop()

    user = auth.get_current_user()

    # Header
    st.markdown("# 💬 Contact Support")
    st.markdown("*We're here to help! Get answers to your questions and resolve any issues.*")

    # Add CSS to hide empty containers
    st.markdown(
        """
        <style>
        /* Hide empty containers/divs */
        div:empty {
            display: none !important;
        }
        /* Hide containers with only whitespace */
        .stTabs [data-baseweb="tab-panel"] > div:not(:has(*:not(:empty))) {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Tab layout for different support options - hide FAQ and Help Center for students
    is_admin = user.get("role") == "admin"

    if is_admin:
        # Admin sees all tabs
        tab1, tab2, tab3, tab4 = st.tabs(
            ["🎫 Submit Ticket", "❓ FAQ", "📚 Help Center", "🎤 My Tickets"]
        )

        with tab1:
            show_submit_ticket_form(user)

        with tab2:
            show_faq_section()

        with tab3:
            show_help_center()

        with tab4:
            show_user_tickets(user)
    else:
        # Students only see Submit Ticket and My Tickets
        tab1, tab2 = st.tabs(["🎫 Submit Ticket", "🎤 My Tickets"])

        with tab1:
            show_submit_ticket_form(user)

        with tab2:
            show_user_tickets(user)


def show_submit_ticket_form(user: Dict[str, Any]):
    """Display ticket submission form"""

    # Add CSS to ensure all text is black except buttons
    st.markdown(
        """
        <style>
        /* Force all form text to black */
        .stMarkdown h3, .stMarkdown p, .stMarkdown em {
            color: #000000 !important;
        }
        .stTextInput label, .stTextArea label, .stSelectbox label, .stFileUploader label {
            color: #000000 !important;
        }
        .stTextInput input, .stTextArea textarea {
            color: #000000 !important;
        }
        .stTextInput input::placeholder, .stTextArea textarea::placeholder {
            color: #666666 !important;
        }
        .stCheckbox label {
            color: #000000 !important;
        }
        .stCheckbox label p {
            color: #000000 !important;
        }
        .stForm {
            color: #000000 !important;
        }
        .stForm label {
            color: #000000 !important;
        }
        /* Keep file upload button text white */
        .stFileUploader button {
            color: #ffffff !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🎫 Submit a Support Ticket")
    st.markdown("*Fill out the form below and we'll get back to you within 24 hours.*")

    with st.form("support_ticket_form"):
        # Ticket category
        category = st.selectbox(
            "📋 Issue Category",
            [
                "Technical Issue",
                "Payment & Billing",
                "Account & Login",
                "Exam Content",
                "Feature Request",
                "Bug Report",
                "Other",
            ],
            help="Select the category that best describes your issue",
        )

        # Priority level
        priority = st.selectbox(
            "🚨 Priority Level",
            ["Low", "Medium", "High", "Urgent"],
            index=1,
            help="How urgent is your issue?",
        )

        # Subject
        subject = st.text_input(
            "📝 Subject",
            placeholder="Brief description of your issue",
            help="Provide a clear, concise subject line",
        )

        # Description
        description = st.text_area(
            "📄 Detailed Description",
            placeholder="Please provide detailed information about your issue, including steps to reproduce if applicable...",
            height=150,
            help="The more details you provide, the faster we can help you",
        )

        # Additional information
        st.markdown("**📎 Additional Information (Optional)**")

        col1, col2 = st.columns(2)

        with col1:
            browser = st.text_input("🌐 Browser", placeholder="e.g., Chrome 96.0")
            device = st.text_input("📱 Device", placeholder="e.g., Windows 10, iPhone 13")

        with col2:
            error_message = st.text_input(
                "⚠️ Error Message", placeholder="Any error messages you received"
            )
            affected_exam = st.text_input(
                "📝 Affected Exam", placeholder="Name of exam if issue is exam-specific"
            )

        # File upload
        uploaded_file = st.file_uploader(
            "📎 Attach File (Optional)",
            type=["png", "jpg", "jpeg", "gif", "pdf", "txt"],
            help="Upload screenshots or relevant files (max 10MB)",
        )

        # Contact preferences
        st.markdown("**📞 Contact Preferences**")
        email_updates = st.checkbox("📧 Email me updates on this ticket", value=True)

        # Submit button
        submitted = st.form_submit_button(
            "🚀 Submit Ticket", type="primary", use_container_width=True
        )

        if submitted:
            if not subject or not description:
                st.error("Please fill in both subject and description fields.")
            else:
                # Create ticket
                ticket_data = {
                    "user_id": user["id"],
                    "user_email": user["email"],
                    "category": category,
                    "priority": priority,
                    "subject": subject,
                    "description": description,
                    "browser": browser,
                    "device": device,
                    "error_message": error_message,
                    "affected_exam": affected_exam,
                    "email_updates": email_updates,
                    "status": "Open",
                    "created_at": datetime.now().isoformat(),
                }

                ticket_id = run_async(create_support_ticket(ticket_data, uploaded_file))

                if ticket_id:
                    st.success(
                        f"✅ Ticket submitted successfully! Your ticket ID is: **{ticket_id}**"
                    )
                    st.info(
                        "We'll review your ticket and respond within 24 hours. You can track its status in the 'My Tickets' tab."
                    )
                    st.balloons()
                else:
                    st.error("❌ Failed to submit ticket. Please try again.")


def show_faq_section():
    """Display FAQ section"""
    st.markdown("### ❓ Frequently Asked Questions")
    st.markdown("*Quick answers to common questions*")

    # Search FAQ
    search_query = st.text_input("🔍 Search FAQ", placeholder="Type keywords to search...")

    faqs = [
        {
            "category": "Getting Started",
            "icon": "🚀",
            "questions": [
                {
                    "q": "How do I take my first exam?",
                    "a": "After logging in, go to your dashboard and browse available mock exams. Purchase credits if needed, then click 'Take Exam' to start. Make sure you have a stable internet connection.",
                },
                {
                    "q": "How many credits do I need per exam?",
                    "a": "Most exams cost 1-3 credits depending on length and complexity. The exact cost is shown on each exam card before you start.",
                },
                {
                    "q": "Can I pause an exam once started?",
                    "a": "Yes! You can close your browser and return later. Your progress is automatically saved. However, the timer continues running, so complete exams promptly.",
                },
            ],
        },
        {
            "category": "Credits & Payments",
            "icon": "💳",
            "questions": [
                {
                    "q": "How do I purchase credits?",
                    "a": "Click 'Purchase Credits' in the top menu or dashboard. Choose a package and complete payment through our secure Stripe checkout. Credits are added instantly.",
                },
                {
                    "q": "Do credits expire?",
                    "a": "No! Your credits never expire. Use them whenever you're ready to take exams.",
                },
                {
                    "q": "Can I get a refund?",
                    "a": "We offer full refunds within 30 days of purchase if you haven't used any credits. Contact support with your purchase details.",
                },
                {
                    "q": "What payment methods do you accept?",
                    "a": "We accept all major credit cards (Visa, MasterCard, American Express), debit cards, and digital wallets (Apple Pay, Google Pay) through Stripe.",
                },
            ],
        },
        {
            "category": "Exams & Scoring",
            "icon": "📝",
            "questions": [
                {
                    "q": "How is my score calculated?",
                    "a": "Your score is the percentage of correct answers. For example, if you get 18 out of 20 questions correct, your score is 90%.",
                },
                {
                    "q": "Can I review my answers after submitting?",
                    "a": "Yes! After submitting, you'll see detailed results showing correct answers, your responses, and explanations (if unlocked).",
                },
                {
                    "q": "How do I unlock explanations?",
                    "a": "After completing an exam, you can unlock AI-powered explanations for 2 credits. These provide detailed reasoning for each question.",
                },
                {
                    "q": "Can I retake the same exam?",
                    "a": "Yes! You can retake any exam multiple times. Each attempt costs the same number of credits and helps you track improvement.",
                },
            ],
        },
        {
            "category": "Technical Issues",
            "icon": "🔧",
            "questions": [
                {
                    "q": "The exam page won't load. What should I do?",
                    "a": "Try refreshing the page, clearing your browser cache, or using a different browser. Ensure you have a stable internet connection. If issues persist, contact support.",
                },
                {
                    "q": "I lost connection during an exam. Is my progress saved?",
                    "a": "Yes! Your answers are automatically saved. Return to the exam page and continue where you left off. The timer continues running during disconnection.",
                },
                {
                    "q": "The timer seems incorrect. What's happening?",
                    "a": "The timer is based on your device's clock. Ensure your system time is correct. If you experience timer issues, contact support immediately.",
                },
                {
                    "q": "I can't download my PDF report. Help!",
                    "a": "Ensure your browser allows downloads and you have sufficient storage space. Try using a different browser or device. Contact support if the issue persists.",
                },
            ],
        },
        {
            "category": "Account & Profile",
            "icon": "👤",
            "questions": [
                {
                    "q": "How do I reset my password?",
                    "a": "Click 'Forgot Password' on the login page and enter your email. You'll receive a password reset link within a few minutes.",
                },
                {
                    "q": "Can I change my email address?",
                    "a": "Currently, email changes require manual assistance. Contact support with your current and new email addresses for help.",
                },
                {
                    "q": "How do I delete my account?",
                    "a": "Contact support to request account deletion. We'll permanently remove your data within 30 days as per our privacy policy.",
                },
                {
                    "q": "Can I share my account with others?",
                    "a": "No, accounts are for individual use only. Credits and exam history cannot be shared or transferred between users.",
                },
            ],
        },
    ]

    # Filter FAQs by search query
    if search_query:
        filtered_faqs = []
        for category in faqs:
            filtered_questions = [
                q
                for q in category["questions"]
                if search_query.lower() in q["q"].lower() or search_query.lower() in q["a"].lower()
            ]
            if filtered_questions:
                filtered_category = category.copy()
                filtered_category["questions"] = filtered_questions
                filtered_faqs.append(filtered_category)
        faqs = filtered_faqs

    # Display FAQs
    for category in faqs:
        st.markdown(f"#### {category['icon']} {category['category']}")

        for faq in category["questions"]:
            with st.expander(f"**{faq['q']}**"):
                st.markdown(faq["a"])

        st.markdown("---")

    # Still need help?
    st.markdown("### 🤔 Still Need Help?")
    st.info(
        "Can't find what you're looking for? Submit a support ticket and we'll help you personally!"
    )

    if st.button("🎫 Submit Support Ticket", use_container_width=True):
        st.session_state.support_tab = 0  # Switch to submit ticket tab
        st.rerun()


def show_help_center():
    """Display help center with guides and tutorials"""
    st.markdown("### 📚 Help Center")
    st.markdown("*Comprehensive guides and tutorials*")

    # Guide categories
    guides = {
        "Getting Started": {
            "icon": "🚀",
            "items": [
                "Creating Your Account",
                "Taking Your First Exam",
                "Understanding the Dashboard",
                "Purchasing Credits",
                "Navigating the Interface",
            ],
        },
        "Exam Taking": {
            "icon": "📝",
            "items": [
                "Exam Interface Guide",
                "Time Management Tips",
                "Using Review Mode",
                "Understanding Scoring",
                "Retaking Exams",
            ],
        },
        "Features": {
            "icon": "⚡",
            "items": [
                "AI-Powered Explanations",
                "Progress Tracking",
                "PDF Reports",
                "Performance Analytics",
                "Mobile Usage",
            ],
        },
        "Account Management": {
            "icon": "👤",
            "items": [
                "Profile Settings",
                "Password Management",
                "Email Preferences",
                "Data Export",
                "Account Security",
            ],
        },
    }

    # Display guides in tabs
    guide_tabs = st.tabs([f"{info['icon']} {name}" for name, info in guides.items()])

    for tab, (category_name, category_info) in zip(guide_tabs, guides.items()):
        with tab:
            st.markdown(f"#### {category_info['icon']} {category_name} Guides")

            for item in category_info["items"]:
                with st.expander(f"📖 {item}"):
                    st.markdown(get_guide_content(item))

    # Video tutorials section
    st.markdown("---")
    st.markdown("### 🎥 Video Tutorials")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
        **📹 Quick Start Guide (3 min)**
        Learn the basics in under 3 minutes

        **📹 Advanced Features (8 min)**
        Unlock the full potential of MockExamify
        """
        )

    with col2:
        st.markdown(
            """
        **📹 Exam Strategies (5 min)**
        Tips for maximizing your exam performance

        **📹 Progress Tracking (4 min)**
        Monitor and improve your performance
        """
        )

    st.info("📺 Video tutorials are coming soon! For now, use our written guides above.")


def show_user_tickets(user: Dict[str, Any]):
    """Display user's support tickets"""
    st.markdown("### 🎤 My Support Tickets")

    # Load user tickets
    tickets = run_async(load_user_tickets(user["id"]))

    if not tickets:
        st.markdown(
            """
        <div style="text-align: center; padding: 2rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🎫</div>
            <h4>No Support Tickets</h4>
            <p style="color: #666;">You haven't submitted any support tickets yet.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        if st.button("🎫 Submit Your First Ticket", use_container_width=True, type="primary"):
            st.session_state.support_tab = 0
            st.rerun()
        return

    # Display tickets
    for ticket in tickets:
        show_ticket_card(ticket)


def show_ticket_card(ticket: Dict[str, Any]):
    """Display individual ticket card"""
    status = ticket.get("status", "Open")
    priority = ticket.get("priority", "Medium")
    created_at = ticket.get("created_at", "")
    subject = ticket.get("subject", "No subject")
    category = ticket.get("category", "General")
    ticket_id = ticket.get("id", "Unknown")

    # Status colors
    status_colors = {
        "Open": "#e74c3c",
        "In Progress": "#f39c12",
        "Pending": "#3498db",
        "Resolved": "#27ae60",
        "Closed": "#95a5a6",
    }

    # Priority emojis
    priority_emojis = {"Low": "🟢", "Medium": "🟡", "High": "🟠", "Urgent": "🔴"}

    status_color = status_colors.get(status, "#95a5a6")
    priority_emoji = priority_emojis.get(priority, "🟡")

    # Format date
    try:
        date_obj = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        formatted_date = date_obj.strftime("%B %d, %Y")
    except:
        formatted_date = "Unknown date"

    with st.container():
        st.markdown(
            f"""
        <div style="
            border: 1px solid #e1e5e9;
            border-left: 4px solid {status_color};
            border-radius: 0.5rem;
            padding: 1.5rem;
            margin-bottom: 1rem;
            background: white;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <div>
                    <h4 style="margin: 0; color: #2c3e50;">#{ticket_id} - {subject}</h4>
                    <p style="margin: 0.5rem 0 0 0; color: #7f8c8d;">📂 {category}</p>
                </div>
                <div style="text-align: right;">
                    <div style="background: {status_color}; color: white; padding: 0.3rem 0.8rem; border-radius: 1rem; font-size: 0.8rem; font-weight: bold;">
                        {status}
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.9rem;">
                        {priority_emoji} {priority} Priority
                    </div>
                </div>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #7f8c8d;">📅 Created: {formatted_date}</span>
                <span style="color: #7f8c8d;">💬 Last updated: {formatted_date}</span>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Action buttons
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button(
                "👁️ View Details", key=f"view_ticket_{ticket_id}", use_container_width=True
            ):
                show_ticket_details(ticket)

        with col2:
            if status not in ["Resolved", "Closed"]:
                if st.button(
                    "💬 Add Reply", key=f"reply_ticket_{ticket_id}", use_container_width=True
                ):
                    show_ticket_reply_form(ticket)

        with col3:
            if status not in ["Closed"]:
                if st.button(
                    "❌ Close Ticket", key=f"close_ticket_{ticket_id}", use_container_width=True
                ):
                    close_ticket(ticket_id)


def show_ticket_details(ticket: Dict[str, Any]):
    """Show detailed ticket view"""
    st.session_state.view_ticket = ticket


def show_ticket_reply_form(ticket: Dict[str, Any]):
    """Show reply form for ticket"""
    st.session_state.reply_ticket = ticket


def close_ticket(ticket_id: str):
    """Close a support ticket"""
    success = run_async(update_ticket_status(ticket_id, "Closed"))
    if success:
        st.success("✅ Ticket closed successfully")
        st.rerun()
    else:
        st.error("❌ Failed to close ticket")


def get_guide_content(guide_title: str) -> str:
    """Get content for help guides"""
    guides_content = {
        "Creating Your Account": """
        **Step 1:** Go to the MockExamify homepage
        **Step 2:** Click "Sign Up" in the top right corner
        **Step 3:** Enter your email and create a strong password
        **Step 4:** Verify your email address
        **Step 5:** Complete your profile setup

        🎉 **You're ready to start taking exams!**
        """,
        "Taking Your First Exam": """
        **Before You Start:**
        - Ensure you have sufficient credits
        - Find a quiet environment
        - Check your internet connection

        **During the Exam:**
        1. Read each question carefully
        2. Use the review function to check answers
        3. Watch the timer in the top right
        4. Submit when ready or when time expires

        **After Submission:**
        - Review your results immediately
        - Consider unlocking explanations
        - Download your PDF report
        """,
        "Understanding the Dashboard": """
        **Dashboard Overview:**
        - **Available Exams:** Browse and filter mock exams
        - **Credit Balance:** Your current available credits
        - **Recent Attempts:** Quick access to recent exam results
        - **Progress Stats:** Your overall performance metrics

        **Quick Actions:**
        - Purchase credits
        - View exam history
        - Access support
        - Update profile settings
        """,
        # Add more guide content as needed
    }

    return guides_content.get(guide_title, "Guide content coming soon!")


async def create_support_ticket(ticket_data: Dict[str, Any], uploaded_file=None) -> Optional[str]:
    """Create a new support ticket"""
    try:
        from db import db

        # Handle file upload if present
        file_url = None
        if uploaded_file:
            file_url = await upload_support_file(uploaded_file)

        ticket_data["attachment_url"] = file_url

        # Create ticket in database
        ticket_id = await db.create_support_ticket(ticket_data)

        # Send notification email (implement as needed)
        # await send_ticket_notification(ticket_data)

        return ticket_id

    except Exception as e:
        st.error(f"Error creating ticket: {str(e)}")
        return None


async def upload_support_file(uploaded_file) -> Optional[str]:
    """Upload support attachment file"""
    try:
        # Implementation would depend on your file storage solution
        # For now, return None to indicate no file upload
        return None
    except Exception as e:
        return None


async def load_user_tickets(user_id: str) -> List[Dict[str, Any]]:
    """Load user's support tickets"""
    try:
        from db import db

        return await db.get_user_support_tickets(user_id)
    except Exception as e:
        return []


async def update_ticket_status(ticket_id: str, status: str) -> bool:
    """Update ticket status"""
    try:
        from db import db

        return await db.update_support_ticket_status(ticket_id, status)
    except Exception as e:
        return False
