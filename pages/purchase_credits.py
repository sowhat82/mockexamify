"""
Enhanced Purchase Credits page for MockExamify
Comprehensive Stripe integration for credit purchases
"""
import streamlit as st
from typing import Dict, Any
from auth_utils import AuthUtils, run_async
from stripe_utils import stripe_manager
import config

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
    
    # Handle payment callbacks first
    handle_payment_callback()
    
    # Header with enhanced styling
    st.markdown("# 💳 Purchase Credits")
    st.markdown("*Unlock your full exam potential with our credit packages*")
    
    # Current balance with enhanced display
    current_credits = user.get('credits_balance', 0)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 1rem; color: white; text-align: center; 
                    margin-bottom: 2rem; box-shadow: 0 8px 32px rgba(0,0,0,0.1);">
            <h2 style="margin: 0; font-size: 1.2rem; opacity: 0.9;">Current Balance</h2>
            <h1 style="margin: 0.5rem 0; font-size: 3rem; font-weight: bold;">{current_credits}</h1>
            <h3 style="margin: 0; font-size: 1.1rem; opacity: 0.9;">Credits Available</h3>
        </div>
        """, unsafe_allow_html=True)
    
    # Credit packages from config
    st.markdown("## 📦 Choose Your Credit Package")
    st.markdown("*All packages include instant credit delivery and never expire*")
    
    # Get packages from Stripe manager/config
    packages = stripe_manager.get_all_packs()
    
    if not packages:
        st.error("No credit packages available")
        return
    
    # Display packages in columns
    cols = st.columns(len(packages))
    
    for i, (pack_id, pack_info) in enumerate(packages.items()):
        with cols[i % len(cols)]:
            display_package_card(pack_id, pack_info, user)
    
    # Value proposition section
    st.markdown("---")
    st.markdown("## 🌟 Why Choose Our Credits?")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        ### 🔒 Secure Payment
        Protected by Stripe's enterprise-grade security
        """)
    
    with col2:
        st.markdown("""
        ### ⚡ Instant Delivery
        Credits added immediately after payment
        """)
    
    with col3:
        st.markdown("""
        ### ♾️ Never Expire
        Use your credits whenever you're ready
        """)
    
    with col4:
        st.markdown("""
        ### 🎯 Best Value
        More credits = better price per exam
        """)
    
    # Payment info and security
    st.markdown("---")
    st.markdown("## 🔐 Payment Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **💳 Accepted Payment Methods:**
        - All major credit cards (Visa, MasterCard, American Express)
        - Debit cards
        - Digital wallets (Apple Pay, Google Pay)
        """)
    
    with col2:
        st.success("""
        **🛡️ Security Features:**
        - 256-bit SSL encryption
        - PCI DSS compliant
        - Fraud protection included
        - No card details stored
        """)
    
    # FAQ section
    with st.expander("❓ Frequently Asked Questions"):
        st.markdown("""
        **Q: How long do credits last?**
        A: Credits never expire! Use them whenever you're ready to take exams.
        
        **Q: Can I get a refund?**
        A: We offer full refunds within 30 days of purchase if you haven't used any credits.
        
        **Q: Are there any hidden fees?**
        A: No hidden fees! The price you see is exactly what you pay.
        
        **Q: Can I share credits with others?**
        A: Credits are tied to your account and cannot be transferred to other users.
        
        **Q: What happens if I have technical issues?**
        A: Contact our support team and we'll resolve any issues promptly.
        
        **Q: Do you offer bulk discounts?**
        A: Yes! Larger credit packages offer better value per credit.
        """)
    
    # Contact support
    st.markdown("---")
    st.markdown("### 📞 Need Help?")
    if st.button("💬 Contact Support", use_container_width=True):
        st.session_state.page = "contact_support"
        st.rerun()
    
    # Back button
    if st.button("🏠 Back to Dashboard", type="secondary"):
        st.session_state.page = "dashboard"
        st.rerun()

def display_package_card(pack_id: str, pack_info: Dict[str, Any], user: Dict[str, Any]):
    """Display an enhanced package card"""
    credits = pack_info['credits']
    price_cents = pack_info['price']
    price_dollars = price_cents / 100
    name = pack_info['name']
    
    # Determine if this is the popular package
    is_popular = pack_info.get('popular', False)
    
    # Calculate value metrics
    price_per_credit = price_dollars / credits
    
    # Enhanced card styling
    card_style = f"""
    <div style="
        border: {'3px solid #ff6b6b' if is_popular else '2px solid #e1e5e9'};
        border-radius: 1rem; 
        padding: 1.5rem; 
        margin-bottom: 1rem;
        background: {'linear-gradient(135deg, #fff5f5 0%, #fff 100%)' if is_popular else 'white'};
        box-shadow: 0 8px 25px rgba(0,0,0,{'0.15' if is_popular else '0.1'});
        transform: {'scale(1.02)' if is_popular else 'scale(1)'};
        transition: all 0.3s ease;
        position: relative;
    ">
    """
    
    if is_popular:
        card_style += """
        <div style="
            position: absolute;
            top: -10px;
            left: 50%;
            transform: translateX(-50%);
            background: #ff6b6b;
            color: white;
            padding: 0.3rem 1rem;
            border-radius: 1rem;
            font-size: 0.8rem;
            font-weight: bold;
        ">
            🌟 MOST POPULAR
        </div>
        """
    
    card_style += f"""
        <div style="text-align: center;">
            <h3 style="margin-top: {'1rem' if is_popular else '0'}; color: #2c3e50; font-size: 1.3rem;">
                {name}
            </h3>
            <div style="font-size: 3rem; font-weight: bold; color: #3498db; margin: 1rem 0;">
                {credits}
            </div>
            <div style="font-size: 0.9rem; color: #7f8c8d; margin-bottom: 0.5rem;">
                Credits
            </div>
            <div style="font-size: 2rem; font-weight: bold; color: #27ae60; margin: 1rem 0;">
                ${price_dollars:.2f}
            </div>
            <div style="font-size: 0.9rem; color: #95a5a6; margin-bottom: 1.5rem;">
                ${price_per_credit:.2f} per credit
            </div>
        </div>
    </div>
    """
    
    st.markdown(card_style, unsafe_allow_html=True)
    
    # Purchase button
    button_type = "primary" if is_popular else "secondary"
    if st.button(
        f"💳 Purchase {name}", 
        key=f"purchase_{pack_id}",
        use_container_width=True,
        type=button_type
    ):
        initiate_stripe_checkout(pack_id, pack_info, user)

def initiate_stripe_checkout(pack_id: str, pack_info: Dict[str, Any], user: Dict[str, Any]):
    """Initiate Stripe checkout process"""
    try:
        with st.spinner("Creating secure checkout session..."):
            # Create success and cancel URLs
            base_url = st.session_state.get('base_url', 'http://localhost:8501')
            success_url = f"{base_url}?payment=success&pack_id={pack_id}"
            cancel_url = f"{base_url}?payment=cancel"
            
            # Create checkout session using Stripe manager
            checkout_url = run_async(stripe_manager.create_checkout_session(
                user=user,
                pack_id=pack_id,
                success_url=success_url,
                cancel_url=cancel_url
            ))
            
            if checkout_url:
                st.success("✅ Checkout session created!")
                st.info("🔄 Redirecting to secure payment page...")
                
                # Create redirect button
                st.markdown(f"""
                <div style="text-align: center; margin: 2rem 0;">
                    <a href="{checkout_url}" target="_blank" style="
                        background: linear-gradient(45deg, #667eea, #764ba2);
                        color: white;
                        padding: 1rem 2rem;
                        border-radius: 0.5rem;
                        text-decoration: none;
                        font-weight: bold;
                        display: inline-block;
                        transition: all 0.3s ease;
                    ">
                        🚀 Complete Payment Securely
                    </a>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("*A new tab will open with Stripe's secure checkout*")
            else:
                st.error("❌ Failed to create checkout session. Please try again.")
    
    except Exception as e:
        st.error(f"❌ Error initiating payment: {str(e)}")

def handle_payment_callback():
    """Handle payment success/failure callbacks"""
    # Get URL parameters
    query_params = st.query_params
    
    if "payment" in query_params:
        status = query_params["payment"]
        
        if status == "success":
            pack_id = query_params.get("pack_id", "")
            
            st.success("🎉 Payment Successful!")
            st.balloons()
            
            # Show success details
            if pack_id:
                pack_info = stripe_manager.get_pack_info(pack_id)
                if pack_info:
                    st.markdown(f"""
                    ### ✅ Credits Added Successfully!
                    
                    **Package:** {pack_info['name']}  
                    **Credits Added:** {pack_info['credits']}  
                    **Amount Paid:** ${pack_info['price']/100:.2f}
                    
                    Your credits have been added to your account and are ready to use!
                    """)
            
            # Refresh user data
            try:
                auth = AuthUtils(config.API_BASE_URL)
                refreshed_user = auth.get_current_user()
                if refreshed_user:
                    st.session_state.current_user = refreshed_user
                    st.success(f"✅ Updated balance: {refreshed_user.get('credits_balance', 0)} credits")
            except:
                st.info("Please refresh the page to see your updated balance.")
            
            # Clear query params and provide navigation
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🏠 Go to Dashboard", use_container_width=True, type="primary"):
                    st.query_params.clear()
                    st.session_state.page = "dashboard"
                    st.rerun()
            
            with col2:
                if st.button("📝 Take an Exam", use_container_width=True):
                    st.query_params.clear()
                    st.session_state.page = "dashboard"
                    st.rerun()
        
        elif status == "cancel":
            st.warning("⚠️ Payment Cancelled")
            st.info("Your payment was cancelled. No charges were made to your account.")
            
            if st.button("🔄 Try Again", use_container_width=True):
                st.query_params.clear()
                st.rerun()