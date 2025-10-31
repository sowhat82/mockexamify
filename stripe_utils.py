"""
Stripe Payment Integration for MockExamify
Handles credit purchasing with secure payment processing
"""
import stripe
import streamlit as st
import logging
from typing import Optional, Dict, Any, Tuple
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class StripeUtils:
    """Stripe payment processing utility"""
    
    def __init__(self, api_key: str, webhook_secret: str = None):
        """Initialize Stripe with API key"""
        stripe.api_key = api_key
        self.webhook_secret = webhook_secret
        
        # Credit packages with prices in cents
        self.credit_packages = {
            "starter": {
                "credits": 10,
                "price": 999,  # $9.99
                "price_id": "price_starter_10_credits",
                "name": "Starter Pack",
                "description": "10 credits - Perfect for trying out our platform"
            },
            "popular": {
                "credits": 25,
                "price": 1999,  # $19.99
                "price_id": "price_popular_25_credits", 
                "name": "Popular Pack",
                "description": "25 credits - Great value for regular users"
            },
            "premium": {
                "credits": 50,
                "price": 3499,  # $34.99
                "price_id": "price_premium_50_credits",
                "name": "Premium Pack",
                "description": "50 credits - Best value for power users"
            },
            "unlimited": {
                "credits": 100,
                "price": 5999,  # $59.99
                "price_id": "price_unlimited_100_credits",
                "name": "Unlimited Pack",
                "description": "100 credits - Maximum value for exam prep"
            }
        }
    
    def get_credit_packages(self) -> Dict[str, Any]:
        """Get available credit packages"""
        return self.credit_packages
    
    def create_checkout_session(
        self, 
        package_key: str, 
        user_id: str, 
        user_email: str,
        success_url: str,
        cancel_url: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Create Stripe checkout session
        Returns: (success, session_url, error_message)
        """
        try:
            if package_key not in self.credit_packages:
                return False, None, "Invalid credit package selected"
            
            package = self.credit_packages[package_key]
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'sgd',
                            'product_data': {
                                'name': package['name'],
                                'description': package['description'],
                                'images': ['https://wantamock.streamlit.app/logo.png'],  # Add your logo URL
                            },
                            'unit_amount': package['price'],
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=success_url + '&session_id={CHECKOUT_SESSION_ID}',
                cancel_url=cancel_url,
                customer_email=user_email,
                metadata={
                    'user_id': user_id,
                    'package_key': package_key,
                    'credits': str(package['credits']),
                    'app_name': 'MockExamify'
                },
                expires_at=int((datetime.now().timestamp() + 30 * 60))  # 30 minutes expiry
            )
            
            return True, session.url, None
            
        except stripe.StripeError as e:
            logger.error(f"Stripe error creating session: {e}")
            return False, None, f"Payment error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error creating checkout session: {e}")
            return False, None, "Payment system temporarily unavailable"
    
    def verify_session(self, session_id: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Verify completed checkout session
        Returns: (success, session_data, error_message)
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status == 'paid':
                return True, {
                    'session_id': session.id,
                    'user_id': session.metadata.get('user_id'),
                    'package_key': session.metadata.get('package_key'),
                    'credits': int(session.metadata.get('credits', 0)),
                    'amount_paid': session.amount_total,
                    'customer_email': session.customer_details.email if session.customer_details else None
                }, None
            else:
                return False, None, f"Payment not completed. Status: {session.payment_status}"
                
        except stripe.StripeError as e:
            logger.error(f"Stripe error verifying session: {e}")
            return False, None, f"Payment verification error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error verifying session: {e}")
            return False, None, "Payment verification failed"
    
    def handle_webhook(self, payload: str, sig_header: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Handle Stripe webhook events
        Returns: (success, event_data, error_message)
        """
        if not self.webhook_secret:
            return False, None, "Webhook secret not configured"
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            
            # Handle the event
            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                
                if session.payment_status == 'paid':
                    return True, {
                        'type': 'payment_completed',
                        'session_id': session.id,
                        'user_id': session.metadata.get('user_id'),
                        'package_key': session.metadata.get('package_key'),
                        'credits': int(session.metadata.get('credits', 0)),
                        'amount_paid': session.amount_total,
                        'customer_email': session.customer_details.email if session.customer_details else None
                    }, None
            
            elif event['type'] == 'payment_intent.payment_failed':
                payment_intent = event['data']['object']
                return True, {
                    'type': 'payment_failed',
                    'payment_intent_id': payment_intent.id,
                    'error': payment_intent.last_payment_error.message if payment_intent.last_payment_error else 'Payment failed'
                }, None
            
            else:
                # Unhandled event type
                return True, {'type': 'unhandled', 'event_type': event['type']}, None
                
        except stripe.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return False, None, "Invalid webhook signature"
        except Exception as e:
            logger.error(f"Webhook handling error: {e}")
            return False, None, f"Webhook processing failed: {str(e)}"
    
    async def process_successful_payment(self, session_data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Process successful payment and award credits
        Returns: (success, error_message)
        """
        try:
            from db import db
            
            user_id = session_data.get('user_id')
            credits_to_add = session_data.get('credits', 0)
            session_id = session_data.get('session_id')
            amount_paid = session_data.get('amount_paid', 0)
            
            if not user_id or not credits_to_add:
                return False, "Invalid payment data"
            
            # Check if payment already processed
            existing_payment = await db.get_payment_by_session_id(session_id)
            if existing_payment and existing_payment.status == 'completed':
                return True, None  # Already processed
            
            # Record payment in database
            payment_record = await db.create_payment(
                user_id=user_id,
                stripe_session_id=session_id,
                amount=amount_paid / 100,  # Convert cents to dollars
                credits_purchased=credits_to_add,
                status='completed'
            )
            
            if not payment_record:
                return False, "Failed to record payment"
            
            # Add credits to user account
            success = await db.add_credits_to_user(user_id, credits_to_add)
            
            if success:
                logger.info(f"Successfully added {credits_to_add} credits to user {user_id}")
                return True, None
            else:
                return False, "Failed to add credits to user account"
                
        except Exception as e:
            logger.error(f"Error processing successful payment: {e}")
            return False, f"Payment processing error: {str(e)}"
    
    def get_package_by_key(self, package_key: str) -> Optional[Dict]:
        """Get package details by key"""
        return self.credit_packages.get(package_key)
    
    def format_price(self, price_cents: int) -> str:
        """Format price in cents to SGD string"""
        return f"S${price_cents / 100:.2f}"
    
    def calculate_value_savings(self, package_key: str) -> Optional[str]:
        """Calculate savings compared to base price"""
        if package_key not in self.credit_packages:
            return None
        
        package = self.credit_packages[package_key]
        base_price_per_credit = self.credit_packages['starter']['price'] / self.credit_packages['starter']['credits']
        actual_price_per_credit = package['price'] / package['credits']
        
        if actual_price_per_credit < base_price_per_credit:
            savings_percent = ((base_price_per_credit - actual_price_per_credit) / base_price_per_credit) * 100
            return f"Save {savings_percent:.0f}%"
        
        return None

# Utility functions for Streamlit integration
def init_stripe_utils() -> Optional[StripeUtils]:
    """Initialize Stripe utils with config"""
    try:
        import config
        
        stripe_key = getattr(config, 'STRIPE_SECRET_KEY', None)
        webhook_secret = getattr(config, 'STRIPE_WEBHOOK_SECRET', None)
        
        if not stripe_key:
            st.warning("Stripe not configured. Payment functionality unavailable.")
            return None
        
        return StripeUtils(stripe_key, webhook_secret)
        
    except Exception as e:
        st.error(f"Failed to initialize payments: {e}")
        return None

def create_payment_button(
    stripe_utils: StripeUtils, 
    package_key: str, 
    user_id: str, 
    user_email: str,
    base_url: str = "https://mockexamify.streamlit.app"
) -> bool:
    """
    Create payment button for a credit package
    Returns True if checkout session was created successfully
    """
    if not stripe_utils:
        st.error("Payment system not available")
        return False
    
    package = stripe_utils.get_package_by_key(package_key)
    if not package:
        st.error("Invalid package selected")
        return False
    
    # Create checkout session
    success_url = f"{base_url}/?payment=success"
    cancel_url = f"{base_url}/?payment=cancelled"
    
    success, session_url, error = stripe_utils.create_checkout_session(
        package_key=package_key,
        user_id=user_id,
        user_email=user_email,
        success_url=success_url,
        cancel_url=cancel_url
    )
    
    if success and session_url:
        # Store the checkout URL and redirect using Streamlit's method
        st.markdown(f'<meta http-equiv="refresh" content="0; url={session_url}">', unsafe_allow_html=True)
        return True
    else:
        st.error(f"Payment error: {error}")
        return False