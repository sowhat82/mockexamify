"""
Purchase Credits page for MockExamify
Handles Stripe integration for credit purchases
"""
import streamlit as st
import httpx
import asyncio
from typing import Dict, Any
import config
from auth_utils import AuthUtils, run_async

def show_purchase_credits():
    """Display the credit purchase page"""
    auth = AuthUtils(config.API_BASE_URL)
    
    if not auth.is_authenticated():
        st.error("Please log in to purchase credits")
        st.stop()
    
    user = auth.get_current_user()
    if not user:
        st.error("User data not found")
        st.stop()
    
    # Header
    st.markdown("# 💳 Purchase Credits")
    
    # Current balance
    current_credits = user.get('credits_balance', 0)
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #4CAF50, #45a049); 
                padding: 1rem; border-radius: 0.5rem; color: white; margin-bottom: 2rem;">
        <h3 style="margin: 0;">Current Balance: {current_credits} credits</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Credit packages
    st.markdown("## 📦 Credit Packages")
    
    packages = [
        {
            "name": "Starter Pack",
            "credits": 5,
            "price": 9.99,
            "description": "Perfect for trying out a few exams",
            "popular": False
        },
        {
            "name": "Standard Pack",
            "credits": 15,
            "price": 24.99,
            "description": "Great value for regular practice",
            "popular": True
        },
        {
            "name": "Premium Pack",
            "credits": 30,
            "price": 44.99,
            "description": "Best value for serious exam preparation",
            "popular": False
        }
    ]
    
    col1, col2, col3 = st.columns(3)
    columns = [col1, col2, col3]
    
    for i, package in enumerate(packages):
        with columns[i]:
            # Popular badge
            if package["popular"]:
                st.markdown("🌟 **MOST POPULAR**")
            
            # Package card
            st.markdown(f"""
            <div style="border: {'2px solid #ff6b6b' if package['popular'] else '1px solid #ddd'}; 
                        border-radius: 0.5rem; padding: 1.5rem; margin-bottom: 1rem;
                        {'background: #fff5f5;' if package['popular'] else ''}">
                <h3 style="margin-top: 0;">{package['name']}</h3>
                <div style="font-size: 2rem; font-weight: bold; color: #1f77b4;">
                    {package['credits']} credits
                </div>
                <div style="font-size: 1.5rem; margin: 0.5rem 0;">
                    ${package['price']:.2f}
                </div>
                <p style="margin-bottom: 1rem;">{package['description']}</p>
                <div style="font-size: 0.9rem; color: #666;">
                    ${package['price']/package['credits']:.2f} per credit
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Purchase button
            if st.button(
                f"💳 Purchase {package['name']}", 
                key=f"purchase_{i}",
                use_container_width=True,
                type="primary" if package["popular"] else "secondary"
            ):
                initiate_stripe_checkout(package)
    
    # Payment info
    st.markdown("---")
    st.markdown("## 🔒 Secure Payment")
    st.info("💳 All payments are securely processed by Stripe. We accept all major credit cards.")
    
    # FAQ
    with st.expander("❓ Frequently Asked Questions"):
        st.markdown("""
        **Q: How long do credits last?**
        A: Credits never expire! Use them whenever you're ready.
        
        **Q: Can I get a refund?**
        A: We offer refunds within 30 days of purchase if you haven't used the credits.
        
        **Q: Are there any hidden fees?**
        A: No hidden fees! The price you see is exactly what you pay.
        
        **Q: Can I purchase credits for someone else?**
        A: Currently, credits can only be used by the account holder who purchased them.
        """)
    
    # Back button
    if st.button("🏠 Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()

def initiate_stripe_checkout(package: Dict[str, Any]):
    """Initiate Stripe checkout process"""
    try:
        # Create checkout session
        checkout_url = run_async(create_checkout_session(package))
        
        if checkout_url:
            st.success("Redirecting to secure payment...")
            st.markdown(f"""
            <script>
                window.open('{checkout_url}', '_blank');
            </script>
            """, unsafe_allow_html=True)
            
            # Show link as fallback
            st.markdown(f"[Click here if you're not automatically redirected]({checkout_url})")
        else:
            st.error("Failed to create checkout session. Please try again.")
    
    except Exception as e:
        st.error(f"Error initiating payment: {str(e)}")

async def create_checkout_session(package: Dict[str, Any]) -> str:
    """Create Stripe checkout session"""
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            headers = {}
            if "user_token" in st.session_state:
                headers["Authorization"] = f"Bearer {st.session_state.user_token}"
            
            checkout_data = {
                "package_name": package["name"],
                "credits": package["credits"],
                "price": package["price"],
                "success_url": f"{config.API_BASE_URL.replace('localhost:8000', 'mockexamify.streamlit.app')}?payment=success",
                "cancel_url": f"{config.API_BASE_URL.replace('localhost:8000', 'mockexamify.streamlit.app')}?payment=cancel"
            }
            
            response = await client.post(
                f"{config.API_BASE_URL}/api/stripe/create_checkout",
                json=checkout_data,
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("checkout_url", "")
            else:
                return ""
                
    except Exception as e:
        return ""

def handle_payment_callback():
    """Handle payment success/failure callbacks"""
    # Get URL parameters
    query_params = st.experimental_get_query_params()
    
    if "payment" in query_params:
        status = query_params["payment"][0]
        
        if status == "success":
            st.success("🎉 Payment successful! Your credits have been added to your account.")
            
            # Refresh user data
            try:
                user_data = run_async(refresh_user_data())
                if user_data:
                    st.session_state.current_user = user_data
                    st.balloons()
            except:
                pass
            
            # Clear query params and redirect
            if st.button("Go to Dashboard"):
                st.experimental_set_query_params()
                st.session_state.page = "dashboard"
                st.rerun()
        
        elif status == "cancel":
            st.warning("Payment was cancelled. You can try again anytime.")
            
            if st.button("Back to Credit Packages"):
                st.experimental_set_query_params()
                st.rerun()

async def refresh_user_data():
    """Refresh user data after payment"""
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            headers = {}
            if "user_token" in st.session_state:
                headers["Authorization"] = f"Bearer {st.session_state.user_token}"
            
            response = await client.get(
                f"{config.API_BASE_URL}/api/user/profile",
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
    except Exception as e:
        return None