"""
HitPay Payment Integration for MockExamify
Handles PayNow payments with secure payment processing
"""
import hashlib
import hmac
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import requests
import streamlit as st

logger = logging.getLogger(__name__)


class HitPayUtils:
    """HitPay payment processing utility for PayNow"""

    def __init__(self, api_key: str, salt: str = None):
        """Initialize HitPay with API key and salt"""
        self.api_key = api_key
        self.salt = salt
        self.base_url = "https://api.hit-pay.com/v1"

        # Credit packages matching Stripe packages
        self.credit_packages = {
            "starter": {
                "credits": 10,
                "price": 999,  # $9.99 (in cents)
                "name": "Starter Pack",
                "description": "10 credits - Perfect for trying out our platform",
            },
            "popular": {
                "credits": 25,
                "price": 1999,  # $19.99
                "name": "Popular Pack",
                "description": "25 credits - Great value for regular users",
            },
            "premium": {
                "credits": 50,
                "price": 3499,  # $34.99
                "name": "Premium Pack",
                "description": "50 credits - Best value for power users",
            },
            "unlimited": {
                "credits": 100,
                "price": 5999,  # $59.99
                "name": "Unlimited Pack",
                "description": "100 credits - Maximum value for exam prep",
            },
        }

    def get_credit_packages(self) -> Dict[str, Any]:
        """Get available credit packages"""
        return self.credit_packages

    def create_payment_request(
        self,
        package_key: str,
        user_id: str,
        user_email: str,
        redirect_url: str,
        webhook_url: str = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Create HitPay payment request for PayNow
        Returns: (success, payment_url, error_message)
        """
        try:
            if package_key not in self.credit_packages:
                return False, None, "Invalid credit package selected"

            package = self.credit_packages[package_key]

            # Convert cents to dollars for HitPay
            amount = package["price"] / 100

            # Generate unique reference ID
            reference_id = f"MOCK_{user_id[:8]}_{int(datetime.now().timestamp())}"

            # Prepare request payload
            payload = {
                "amount": f"{amount:.2f}",
                "currency": "SGD",
                "email": user_email,
                "name": f"WantAMock - {package['name']}",
                "purpose": package["description"],
                "reference_number": reference_id,
                "redirect_url": redirect_url,
                "payment_methods": ["paynow_online"],  # PayNow only
            }

            # Add webhook URL if provided
            if webhook_url:
                payload["webhook"] = webhook_url

            # Add metadata for tracking
            payload["metadata"] = {
                "user_id": user_id,
                "package_key": package_key,
                "credits": str(package["credits"]),
                "app_name": "WantAMock",
            }

            # Make API request
            headers = {
                "X-BUSINESS-API-KEY": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }

            logger.info(f"[HITPAY] Creating payment request for {package_key}")
            response = requests.post(
                f"{self.base_url}/payment-requests",
                data=payload,
                headers=headers,
                timeout=10,
            )

            if response.status_code == 201:
                data = response.json()
                payment_url = data.get("url")
                logger.info(f"[HITPAY] Payment request created successfully")
                return True, payment_url, None
            else:
                error_msg = f"HitPay API error: {response.status_code}"
                logger.error(f"[HITPAY] {error_msg} - {response.text}")
                return False, None, error_msg

        except requests.RequestException as e:
            logger.error(f"[HITPAY] Network error: {e}")
            return False, None, f"Payment service unavailable: {str(e)}"
        except Exception as e:
            logger.error(f"[HITPAY] Unexpected error creating payment: {e}")
            return False, None, "Payment system temporarily unavailable"

    def verify_webhook_signature(
        self, payload: Dict[str, Any], signature: str
    ) -> bool:
        """
        Verify HitPay webhook signature
        Returns: True if signature is valid, False otherwise
        """
        if not self.salt:
            logger.error("[HITPAY] Salt not configured - cannot verify webhook")
            return False

        try:
            # HitPay signature verification
            # Concatenate payload values in alphabetical order by key
            sorted_keys = sorted(payload.keys())
            data_string = ""

            for key in sorted_keys:
                if key != "hmac":  # Exclude the signature itself
                    value = payload.get(key, "")
                    data_string += str(value)

            # Add salt
            data_string += self.salt

            # Calculate HMAC-SHA256
            calculated_signature = hmac.new(
                self.salt.encode("utf-8"),
                data_string.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            is_valid = hmac.compare_digest(calculated_signature, signature)

            if not is_valid:
                logger.warning(
                    f"[HITPAY] Invalid webhook signature. Expected: {calculated_signature}, Got: {signature}"
                )

            return is_valid

        except Exception as e:
            logger.error(f"[HITPAY] Error verifying webhook signature: {e}")
            return False

    def handle_webhook(
        self, payload: Dict[str, Any]
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Handle HitPay webhook events
        Returns: (success, event_data, error_message)
        """
        try:
            # Extract signature from payload
            signature = payload.get("hmac")
            if not signature:
                return False, None, "Missing webhook signature"

            # Verify signature
            if not self.verify_webhook_signature(payload, signature):
                return False, None, "Invalid webhook signature"

            # Check payment status
            payment_status = payload.get("status")

            if payment_status == "completed":
                # Extract metadata
                reference_number = payload.get("reference_number", "")
                user_id = payload.get("metadata", {}).get("user_id")
                package_key = payload.get("metadata", {}).get("package_key")
                credits = payload.get("metadata", {}).get("credits")

                # Parse from reference if metadata not available
                if not user_id and reference_number.startswith("MOCK_"):
                    parts = reference_number.split("_")
                    if len(parts) >= 2:
                        user_id = parts[1]

                return True, {
                    "type": "payment_completed",
                    "payment_id": payload.get("payment_id"),
                    "payment_request_id": payload.get("payment_request_id"),
                    "reference_number": reference_number,
                    "user_id": user_id,
                    "package_key": package_key,
                    "credits": int(credits) if credits else 0,
                    "amount_paid": float(payload.get("amount", 0)),
                    "currency": payload.get("currency", "SGD"),
                    "customer_email": payload.get("email"),
                    "payment_type": payload.get("payment_type", "paynow"),
                }, None

            elif payment_status in ["failed", "canceled"]:
                return True, {
                    "type": "payment_failed",
                    "payment_request_id": payload.get("payment_request_id"),
                    "status": payment_status,
                }, None

            else:
                # Pending or other status
                return True, {
                    "type": "unhandled",
                    "status": payment_status,
                }, None

        except Exception as e:
            logger.error(f"[HITPAY] Webhook handling error: {e}")
            return False, None, f"Webhook processing failed: {str(e)}"

    async def process_successful_payment(
        self, payment_data: Dict
    ) -> Tuple[bool, Optional[str]]:
        """
        Process successful HitPay payment and award credits
        Returns: (success, error_message)
        """
        try:
            from db import db

            user_id = payment_data.get("user_id")
            credits_to_add = payment_data.get("credits", 0)
            payment_request_id = payment_data.get("payment_request_id")
            amount_paid = payment_data.get("amount_paid", 0)

            if not user_id or not credits_to_add:
                return False, "Invalid payment data"

            # Check if payment already processed
            existing_payment = await db.get_payment_by_hitpay_id(payment_request_id)
            if existing_payment and existing_payment.status == "completed":
                return True, None  # Already processed

            # Record payment in database as completed
            payment_record = await db.create_hitpay_payment(
                user_id=user_id,
                hitpay_payment_id=payment_request_id,
                amount=amount_paid,
                credits_purchased=credits_to_add,
                status="completed",
            )

            if not payment_record:
                logger.error(
                    f"Failed to record HitPay payment for user {user_id}, payment {payment_request_id}"
                )
                return True, None  # Payment succeeded, manual credit needed

            # Add credits to user account
            success = await db.add_credits_to_user(user_id, credits_to_add)

            if success:
                logger.info(
                    f"✅ HitPay payment successful: Added {credits_to_add} credits to user {user_id}"
                )
                return True, None
            else:
                # Credits failed to add but payment is recorded
                logger.error(
                    f"🚨 URGENT: HitPay payment completed but credits NOT added!\n"
                    f"   User ID: {user_id}\n"
                    f"   Payment ID: {payment_request_id}\n"
                    f"   Credits owed: {credits_to_add}\n"
                    f"   Amount paid: ${amount_paid}\n"
                    f"   ACTION REQUIRED: Manually credit user's account"
                )
                return True, None

        except Exception as e:
            logger.error(
                f"🚨 URGENT: Exception during HitPay payment processing!\n"
                f"   User ID: {payment_data.get('user_id')}\n"
                f"   Payment ID: {payment_data.get('payment_request_id')}\n"
                f"   Credits owed: {payment_data.get('credits', 0)}\n"
                f"   Error: {str(e)}\n"
                f"   ACTION REQUIRED: Check if payment was recorded and manually credit user"
            )
            return True, None  # Payment succeeded, manual credit needed

    def get_package_by_key(self, package_key: str) -> Optional[Dict]:
        """Get package details by key"""
        return self.credit_packages.get(package_key)

    def format_price(self, price_cents: int) -> str:
        """Format price in cents to SGD string"""
        return f"S${price_cents / 100:.2f}"


# Utility functions for Streamlit integration
def init_hitpay_utils() -> Optional[HitPayUtils]:
    """Initialize HitPay utils with config"""
    try:
        import config

        # Check if HitPay is enabled
        hitpay_enabled = getattr(config, "ENABLE_HITPAY", False)
        if not hitpay_enabled:
            logger.info("[HITPAY] HitPay disabled in config")
            return None

        hitpay_key = getattr(config, "HITPAY_API_KEY", None)
        hitpay_salt = getattr(config, "HITPAY_SALT", None)

        if not hitpay_key:
            logger.warning(
                "[HITPAY] HitPay enabled but API key not configured. PayNow unavailable."
            )
            return None

        if not hitpay_salt:
            logger.warning(
                "[HITPAY] HitPay salt not configured. Webhook verification will fail."
            )

        logger.info("[HITPAY] HitPay initialized successfully")
        return HitPayUtils(hitpay_key, hitpay_salt)

    except Exception as e:
        logger.error(f"[HITPAY] Failed to initialize HitPay: {e}")
        return None


def create_hitpay_payment_button(
    hitpay_utils: HitPayUtils,
    package_key: str,
    user_id: str,
    user_email: str,
    base_url: str = "https://mockexamify.streamlit.app",
) -> bool:
    """
    Create HitPay payment button for a credit package
    Returns True if payment request was created successfully
    """
    if not hitpay_utils:
        st.error("PayNow payment system not available")
        return False

    package = hitpay_utils.get_package_by_key(package_key)
    if not package:
        st.error("Invalid package selected")
        return False

    # Create redirect URL
    redirect_url = f"{base_url}/?payment=success&source=hitpay"
    webhook_url = f"{base_url}/api/payments/hitpay-webhook"

    logger.info(f"[HITPAY] Creating payment request for {package_key}")

    success, payment_url, error = hitpay_utils.create_payment_request(
        package_key=package_key,
        user_id=user_id,
        user_email=user_email,
        redirect_url=redirect_url,
        webhook_url=webhook_url,
    )

    if success and payment_url:
        # Store URL in session state
        logger.info(f"[HITPAY] Storing payment URL in session state: hitpay_url_{package_key}")
        st.session_state[f"hitpay_url_{package_key}"] = payment_url
        return True
    else:
        logger.error(f"[HITPAY] Failed to create payment request: {error}")
        st.error(f"PayNow payment error: {error}")
        return False
