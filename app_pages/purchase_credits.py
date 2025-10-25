"""
Enhanced Purchase Credits page for MockExamify
Comprehensive Stripe integration for credit purchases
"""

from typing import Any, Dict, Optional

import streamlit as st

import config
from auth_utils import AuthUtils, run_async
from stripe_utils import create_payment_button, init_stripe_utils


def show_purchase_credits():
    """Display the enhanced credit purchase page"""
    auth = AuthUtils(config.API_BASE_URL)

    if not auth.is_authenticated():
        st.error("Please log in to purchase credits")
        st.stop()

    user = auth.get_current_user()
    if not user:
        st.error("User data not found")
        st.stop()

    # Initialize Stripe utils
    stripe_utils = init_stripe_utils()

    # Back to Dashboard button
    col_back, col_spacer = st.columns([1, 9])
    with col_back:
        if st.button("← Back to Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()

    # Header with enhanced styling
    st.markdown("# 💳 Purchase Credits")
    st.markdown("*Unlock your full exam potential with our credit packages*")

    # Current balance with enhanced display
    current_credits = user.get("credits_balance", 0)
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(
            f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 2rem; border-radius: 1rem; color: white; text-align: center;
                    margin-bottom: 2rem; box-shadow: 0 8px 32px rgba(0,0,0,0.1);">
            <h2 style="margin: 0; font-size: 1.2rem; opacity: 0.9;">Current Balance</h2>
            <h1 style="margin: 0.5rem 0; font-size: 3rem; font-weight: bold;">{current_credits}</h1>
            <h3 style="margin: 0; font-size: 1.1rem; opacity: 0.9;">Credits Available</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )

    if not stripe_utils:
        st.warning("Payment system temporarily unavailable. Please try again later.")
        return

    # Display credit packages
    st.markdown("## 📦 Choose Your Credit Package")
    st.markdown("*All packages include instant credit delivery and never expire*")

    packages = stripe_utils.get_credit_packages()

    # Display packages in a 2x2 grid
    col1, col2 = st.columns(2)
    package_keys = list(packages.keys())

    for i, package_key in enumerate(package_keys):
        package = packages[package_key]

        # Alternate between columns
        with col1 if i % 2 == 0 else col2:
            display_package_card(stripe_utils, package_key, package, user)

    # Value proposition section
    st.markdown("---")
    st.markdown("## 🌟 Why Choose Our Credits?")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
        ### 🔒 Secure Payment
        Protected by Stripe's enterprise-grade security
        """
        )

    with col2:
        st.markdown(
            """
        ### ⚡ Instant Delivery
        Credits added immediately after payment
        """
        )

    with col3:
        st.markdown(
            """
        ### ♾️ Never Expire
        Use your credits whenever you're ready
        """
        )

    # Payment info and security
    st.markdown("---")
    st.markdown("## 🔐 Payment Information")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
        **Accepted Payment Methods:**
        - 💳 All major credit cards (Visa, MasterCard, Amex)
        - 🏦 Bank transfers (ACH)
        - 📱 Digital wallets (Apple Pay, Google Pay)
        - 🌍 International cards welcome
        """
        )

    with col2:
        st.markdown(
            """
        **Security & Trust:**
        - 🔐 256-bit SSL encryption
        - 🛡️ PCI DSS Level 1 compliance
        - 🚫 We never store your card details
        - 💼 Backed by Stripe's fraud protection
        """
        )

    # FAQ Section
    st.markdown("---")
    st.markdown("## ❓ Frequently Asked Questions")

    with st.expander("How quickly will I receive my credits?"):
        st.markdown(
            "Credits are added to your account immediately after successful payment confirmation."
        )

    with st.expander("Do credits expire?"):
        st.markdown("No! Your credits never expire. Use them whenever you're ready to take exams.")

    with st.expander("Can I get a refund?"):
        st.markdown(
            "Unused credits can be refunded within 30 days of purchase. Contact support for assistance."
        )

    with st.expander("Is my payment information secure?"):
        st.markdown(
            "Yes! We use Stripe for payment processing, which uses bank-level security. We never store your payment details."
        )

    with st.expander("What happens if a payment fails?"):
        st.markdown(
            "If a payment fails, you'll be notified immediately and no credits will be deducted. You can try again with a different payment method."
        )


def display_package_card(
    stripe_utils, package_key: str, package: Dict[str, Any], user: Dict[str, Any]
):
    """Display a credit package card with purchase button integrated inside"""

    # Determine card style based on package
    if package_key == "popular":
        border_color = "#ff7f0e"
        badge = "🔥 MOST POPULAR"
        badge_color = "#ff7f0e"
        button_type = "primary"
    elif package_key == "premium":
        border_color = "#d62728"
        badge = ""
        badge_color = "#d62728"
        button_type = "secondary"
    else:
        border_color = "#1f77b4"
        badge = ""
        badge_color = "#1f77b4"
        button_type = "secondary"

    # Calculate value savings
    savings = stripe_utils.calculate_value_savings(package_key)

    # Create the card with button outside
    with st.container():
        # Add top badge if applicable
        if badge:
            st.markdown(
                f"""
            <div style="text-align: center; margin-bottom: -10px;">
                <span style="background: {badge_color}; color: white; padding: 0.3rem 1rem;
                           border-radius: 1rem; font-size: 0.8rem; font-weight: bold;">
                    {badge}
                </span>
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Main card content
        st.markdown(
            f"""
        <div style="border: 3px solid {border_color}; border-radius: 1rem; padding: 1.5rem;
                    margin-bottom: 0.5rem; background: white; text-align: center;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
            <h3 style="color: {border_color}; margin-top: 0;">{package['name']}</h3>
            <div style="font-size: 2.5rem; font-weight: bold; color: #333; margin: 1rem 0;">
                {package['credits']} Credits
            </div>
            <div style="font-size: 2rem; color: {border_color}; font-weight: bold; margin-bottom: 0.5rem;">
                {stripe_utils.format_price(package['price'])}
            </div>
            <div style="color: #666; margin-bottom: 1rem;">
                {stripe_utils.format_price(package['price'] // package['credits'])} per credit
            </div>
            <div style="color: #666; font-size: 0.9rem; margin-bottom: 1rem;">
                {package['description']}
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Add savings badge if applicable (separate from card, above button)
        if savings:
            st.markdown(
                f"""
            <div style="background: #28a745; color: white; padding: 0.5rem; border-radius: 0.5rem;
                       margin-bottom: 0.75rem; font-weight: bold; text-align: center;">
                {savings}
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Custom styled button to match card border color
        st.markdown(
            f"""
        <style>
        button[kind="secondary"][data-testid*="baseButton-secondary"] p {{
            color: white !important;
        }}
        div[data-testid="column"]:has(button[key="purchase_{package_key}"]) button {{
            background-color: {border_color} !important;
            color: white !important;
            border: 2px solid {border_color} !important;
        }}
        div[data-testid="column"]:has(button[key="purchase_{package_key}"]) button:hover {{
            background-color: {border_color}dd !important;
            border-color: {border_color}dd !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
        }}
        div[data-testid="column"]:has(button[key="purchase_{package_key}"]) button p {{
            color: white !important;
        }}
        </style>
        """,
            unsafe_allow_html=True,
        )

        # Purchase button
        button_key = f"purchase_{package_key}"
        if st.button(
            f"🛒 Purchase {package['name']}",
            key=button_key,
            use_container_width=True,
        ):
            # Create checkout session
            base_url = "https://mockexamify.streamlit.app"  # Update with your actual URL

            success = create_payment_button(
                stripe_utils=stripe_utils,
                package_key=package_key,
                user_id=user["id"],
                user_email=user["email"],
                base_url=base_url,
            )

            if success:
                st.success("Redirecting to secure payment...")
            else:
                st.error("Failed to initiate payment. Please try again.")

        # Add large spacing after button to clearly separate from next card
        st.markdown('<div style="height: 2.5rem;"></div>', unsafe_allow_html=True)


def handle_payment_callback():
    """Handle payment success/failure callbacks"""
    query_params = st.query_params

    if "payment" in query_params:
        payment_status = query_params["payment"]

        if payment_status == "success":
            # Handle successful payment
            session_id = query_params.get("session_id")

            if session_id:
                stripe_utils = init_stripe_utils()
                if stripe_utils:
                    # Verify the session and process payment
                    success, session_data, error = stripe_utils.verify_session(session_id)

                    if success and session_data:
                        # Process the payment (add credits to user)
                        payment_success, payment_error = run_async(
                            stripe_utils.process_successful_payment(session_data)
                        )

                        if payment_success:
                            st.success(
                                "🎉 Payment successful! Your credits have been added to your account."
                            )
                            st.balloons()

                            # Show payment details
                            with st.expander("Payment Details", expanded=True):
                                st.write(f"**Credits Purchased:** {session_data['credits']}")
                                st.write(
                                    f"**Amount Paid:** ${session_data['amount_paid'] / 100:.2f}"
                                )
                                st.write(f"**Transaction ID:** {session_id[:20]}...")

                            if st.button("Continue to Dashboard"):
                                st.session_state.page = "dashboard"
                                st.rerun()
                        else:
                            st.error(f"Payment verification failed: {payment_error}")
                    else:
                        st.error(f"Payment verification failed: {error}")
                else:
                    st.error("Payment system unavailable")
            else:
                st.error("Invalid payment session")

        elif payment_status == "cancelled":
            st.warning("Payment was cancelled. You can try again anytime.")

            if st.button("Try Again"):
                # Clear query params and reload
                st.query_params.clear()
                st.rerun()

        else:
            st.error("Unknown payment status")


# Additional utility functions
def get_recommended_package(current_credits: int) -> str:
    """Get recommended package based on current credits"""
    if current_credits < 5:
        return "popular"  # Need more credits
    elif current_credits < 15:
        return "starter"  # Just need a top-up
    else:
        return "premium"  # Go big for value


def calculate_credit_value(credits: int) -> str:
    """Calculate approximate exam value of credits"""
    return f"~{credits} exam attempts"
