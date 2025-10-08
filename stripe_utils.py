"""
Stripe payment integration for MockExamify
"""
import stripe
import logging
from typing import Optional, Dict, Any
from models import StripeCheckoutRequest, User
import config

# Configure Stripe
stripe.api_key = config.STRIPE_SECRET_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StripeManager:
    """Handles Stripe payment operations"""
    
    def __init__(self):
        self.webhook_secret = config.STRIPE_WEBHOOK_SECRET
    
    async def create_checkout_session(self, user: User, pack_id: str, success_url: str, cancel_url: str) -> Optional[str]:
        """Create a Stripe checkout session for credit purchase"""
        try:
            if pack_id not in config.CREDIT_PACKS:
                logger.error(f"Invalid pack_id: {pack_id}")
                return None
            
            pack_info = config.CREDIT_PACKS[pack_id]
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': pack_info['name'],
                            'description': f"{pack_info['credits']} exam credits"
                        },
                        'unit_amount': pack_info['price'],  # Amount in cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': user.id,
                    'pack_id': pack_id,
                    'credits': pack_info['credits'],
                    'action': 'buy_credits'
                },
                customer_email=user.email,
            )
            
            logger.info(f"Created checkout session {session.id} for user {user.id}")
            return session.url
            
        except Exception as e:
            logger.error(f"Error creating checkout session: {e}")
            return None
    
    async def create_explanation_unlock_session(self, user: User, attempt_id: str, success_url: str, cancel_url: str) -> Optional[str]:
        """Create a Stripe checkout session for unlocking explanations"""
        try:
            # Fixed price for explanation unlock (e.g., $2.99)
            explanation_price = 299  # $2.99 in cents
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Unlock Explanations',
                            'description': 'Detailed explanations for your exam attempt'
                        },
                        'unit_amount': explanation_price,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': user.id,
                    'attempt_id': attempt_id,
                    'action': 'unlock_explanations'
                },
                customer_email=user.email,
            )
            
            logger.info(f"Created explanation unlock session {session.id} for user {user.id}")
            return session.url
            
        except Exception as e:
            logger.error(f"Error creating explanation unlock session: {e}")
            return None
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Stripe webhook signature"""
        try:
            stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return True
        except ValueError:
            logger.error("Invalid payload")
            return False
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid signature")
            return False
    
    async def handle_checkout_completed(self, session: Dict[str, Any]) -> bool:
        """Handle successful checkout completion"""
        try:
            metadata = session.get('metadata', {})
            action = metadata.get('action')
            
            if action == 'buy_credits':
                return await self._handle_credit_purchase(metadata)
            elif action == 'unlock_explanations':
                return await self._handle_explanation_unlock(metadata)
            else:
                logger.error(f"Unknown action: {action}")
                return False
                
        except Exception as e:
            logger.error(f"Error handling checkout completion: {e}")
            return False
    
    async def _handle_credit_purchase(self, metadata: Dict[str, Any]) -> bool:
        """Handle credit purchase completion"""
        try:
            from db import db  # Import here to avoid circular imports
            
            user_id = metadata.get('user_id')
            credits = int(metadata.get('credits', 0))
            
            if not user_id or credits <= 0:
                logger.error("Invalid metadata for credit purchase")
                return False
            
            # Add credits to user account
            success = await db.update_user_credits(user_id, credits)
            
            if success:
                logger.info(f"Added {credits} credits to user {user_id}")
                return True
            else:
                logger.error(f"Failed to add credits to user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error handling credit purchase: {e}")
            return False
    
    async def _handle_explanation_unlock(self, metadata: Dict[str, Any]) -> bool:
        """Handle explanation unlock completion"""
        try:
            from db import db  # Import here to avoid circular imports
            
            user_id = metadata.get('user_id')
            attempt_id = metadata.get('attempt_id')
            
            if not user_id or not attempt_id:
                logger.error("Invalid metadata for explanation unlock")
                return False
            
            # Update attempt to mark explanations as unlocked
            result = db.client.table('attempts').update({
                'explanation_unlocked': True
            }).eq('id', attempt_id).eq('user_id', user_id).execute()
            
            if result.data:
                logger.info(f"Unlocked explanations for attempt {attempt_id}")
                return True
            else:
                logger.error(f"Failed to unlock explanations for attempt {attempt_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error handling explanation unlock: {e}")
            return False
    
    def get_pack_info(self, pack_id: str) -> Optional[Dict[str, Any]]:
        """Get credit pack information"""
        return config.CREDIT_PACKS.get(pack_id)
    
    def get_all_packs(self) -> Dict[str, Dict[str, Any]]:
        """Get all available credit packs"""
        return config.CREDIT_PACKS


# Global Stripe manager instance
stripe_manager = StripeManager()