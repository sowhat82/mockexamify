"""
Security and Compliance Module for MockExamify
Enhanced security features including input validation, SQL injection prevention,
XSS protection, rate limiting, and audit logging
"""
import re
import html
import hashlib
import hmac
import secrets
import time
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps
import streamlit as st
import bleach
from urllib.parse import quote, unquote
import json

# Configure security logger
security_logger = logging.getLogger('security')

class SecurityManager:
    """Comprehensive security management"""
    
    def __init__(self):
        self.failed_attempts = {}  # Track failed login attempts
        self.rate_limits = {}      # Track rate limiting
        self.session_tokens = {}   # Active session tokens
        self.audit_log = []        # Security audit log
        
        # Security configuration
        self.max_login_attempts = 5
        self.lockout_duration = 300  # 5 minutes
        self.session_timeout = 3600  # 1 hour
        self.rate_limit_window = 60  # 1 minute
        self.rate_limit_max_requests = 100
        
    def validate_input(self, input_data: Any, input_type: str = "text", 
                      max_length: int = 1000, allow_html: bool = False) -> tuple[bool, str, Any]:
        """
        Comprehensive input validation
        Returns: (is_valid, error_message, sanitized_data)
        """
        try:
            if input_data is None:
                return True, "", None
            
            # Convert to string for validation
            if not isinstance(input_data, str):
                input_data = str(input_data)
            
            # Length validation
            if len(input_data) > max_length:
                return False, f"Input exceeds maximum length of {max_length} characters", None
            
            # Type-specific validation
            if input_type == "email":
                if not self._validate_email(input_data):
                    return False, "Invalid email format", None
                    
            elif input_type == "password":
                if not self._validate_password(input_data):
                    return False, "Password must be at least 8 characters with letters and numbers", None
                    
            elif input_type == "sql_safe":
                if self._contains_sql_injection(input_data):
                    return False, "Input contains potentially dangerous content", None
                    
            elif input_type == "filename":
                if not self._validate_filename(input_data):
                    return False, "Invalid filename format", None
            
            # HTML/XSS sanitization
            if allow_html:
                sanitized = self._sanitize_html(input_data)
            else:
                sanitized = html.escape(input_data)
            
            return True, "", sanitized
            
        except Exception as e:
            security_logger.error(f"Input validation error: {e}")
            return False, "Input validation failed", None
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_password(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < 8:
            return False
        if not re.search(r'[A-Za-z]', password):
            return False
        if not re.search(r'[0-9]', password):
            return False
        return True
    
    def _contains_sql_injection(self, input_str: str) -> bool:
        """Check for potential SQL injection patterns"""
        dangerous_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"('|(\\');|--;|/\\*|\\*/)",
            r"(\\bOR\\b.*=.*=)",
            r"(\\bAND\\b.*=.*=)",
            r"(script:|javascript:|vbscript:)",
            r"(<script|</script>)",
            r"(onload|onerror|onclick|onmouseover)"
        ]
        
        input_lower = input_str.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, input_lower, re.IGNORECASE):
                return True
        return False
    
    def _validate_filename(self, filename: str) -> bool:
        """Validate filename for security"""
        # Check for directory traversal
        if '..' in filename or '/' in filename or '\\\\' in filename:
            return False
        
        # Check for dangerous extensions
        dangerous_exts = ['.exe', '.bat', '.cmd', '.sh', '.php', '.jsp', '.asp']
        for ext in dangerous_exts:
            if filename.lower().endswith(ext):
                return False
        
        # Valid filename pattern
        pattern = r'^[a-zA-Z0-9._-]+$'
        return re.match(pattern, filename) is not None
    
    def _sanitize_html(self, html_content: str) -> str:
        """Sanitize HTML content to prevent XSS"""
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        allowed_attributes = {'a': ['href'], 'img': ['src', 'alt']}
        
        return bleach.clean(html_content, tags=allowed_tags, attributes=allowed_attributes)
    
    def check_rate_limit(self, identifier: str, max_requests: int = None, 
                        window_seconds: int = None) -> tuple[bool, int]:
        """
        Check if identifier exceeds rate limit
        Returns: (is_allowed, remaining_requests)
        """
        if max_requests is None:
            max_requests = self.rate_limit_max_requests
        if window_seconds is None:
            window_seconds = self.rate_limit_window
        
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # Clean old entries
        if identifier in self.rate_limits:
            self.rate_limits[identifier] = [
                timestamp for timestamp in self.rate_limits[identifier]
                if timestamp > window_start
            ]
        else:
            self.rate_limits[identifier] = []
        
        # Check current count
        current_count = len(self.rate_limits[identifier])
        
        if current_count >= max_requests:
            security_logger.warning(f"Rate limit exceeded for {identifier}")
            return False, 0
        
        # Add current request
        self.rate_limits[identifier].append(current_time)
        remaining = max_requests - current_count - 1
        
        return True, remaining
    
    def track_failed_login(self, identifier: str) -> bool:
        """
        Track failed login attempts and implement lockout
        Returns: True if account should be locked
        """
        current_time = time.time()
        
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        
        # Clean old attempts
        cutoff_time = current_time - self.lockout_duration
        self.failed_attempts[identifier] = [
            timestamp for timestamp in self.failed_attempts[identifier]
            if timestamp > cutoff_time
        ]
        
        # Add current failed attempt
        self.failed_attempts[identifier].append(current_time)
        
        # Check if should be locked
        if len(self.failed_attempts[identifier]) >= self.max_login_attempts:
            security_logger.warning(f"Account locked due to failed attempts: {identifier}")
            self.log_security_event("account_locked", "high", {
                "identifier": identifier,
                "failed_attempts": len(self.failed_attempts[identifier])
            })
            return True
        
        return False
    
    def is_account_locked(self, identifier: str) -> bool:
        """Check if account is currently locked"""
        if identifier not in self.failed_attempts:
            return False
        
        current_time = time.time()
        cutoff_time = current_time - self.lockout_duration
        
        # Clean old attempts
        self.failed_attempts[identifier] = [
            timestamp for timestamp in self.failed_attempts[identifier]
            if timestamp > cutoff_time
        ]
        
        return len(self.failed_attempts[identifier]) >= self.max_login_attempts
    
    def clear_failed_attempts(self, identifier: str):
        """Clear failed login attempts (on successful login)"""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure token"""
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password: str, salt: str = None) -> tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                          password.encode('utf-8'), 
                                          salt.encode('utf-8'), 
                                          100000)
        return password_hash.hex(), salt
    
    def verify_password(self, password: str, hash_hex: str, salt: str) -> bool:
        """Verify password against hash"""
        try:
            calculated_hash = hashlib.pbkdf2_hmac('sha256',
                                                password.encode('utf-8'),
                                                salt.encode('utf-8'),
                                                100000)
            return calculated_hash.hex() == hash_hex
        except Exception:
            return False
    
    def create_session_token(self, user_id: str) -> str:
        """Create secure session token"""
        token = self.generate_secure_token()
        self.session_tokens[token] = {
            'user_id': user_id,
            'created_at': time.time(),
            'last_access': time.time()
        }
        return token
    
    def validate_session_token(self, token: str) -> Optional[str]:
        """Validate session token and return user_id"""
        if token not in self.session_tokens:
            return None
        
        session = self.session_tokens[token]
        current_time = time.time()
        
        # Check if session expired
        if current_time - session['last_access'] > self.session_timeout:
            del self.session_tokens[token]
            return None
        
        # Update last access
        session['last_access'] = current_time
        return session['user_id']
    
    def invalidate_session(self, token: str):
        """Invalidate session token"""
        if token in self.session_tokens:
            del self.session_tokens[token]
    
    def log_security_event(self, event_type: str, severity: str, details: Dict[str, Any]):
        """Log security event for audit trail"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'severity': severity,  # low, medium, high, critical
            'details': details,
            'session_id': st.session_state.get('session_id'),
            'user_id': st.session_state.get('current_user', {}).get('id')
        }
        
        self.audit_log.append(event)
        security_logger.info(f"Security event: {json.dumps(event)}")
        
        # Keep only last 1000 events in memory
        if len(self.audit_log) > 1000:
            self.audit_log = self.audit_log[-1000:]
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics for monitoring"""
        current_time = time.time()
        recent_events = [
            event for event in self.audit_log
            if (current_time - datetime.fromisoformat(event['timestamp']).timestamp()) < 3600
        ]
        
        metrics = {
            'total_events_last_hour': len(recent_events),
            'high_severity_events': len([e for e in recent_events if e['severity'] in ['high', 'critical']]),
            'failed_logins_last_hour': len([e for e in recent_events if e['event_type'] == 'failed_login']),
            'locked_accounts': len([k for k, v in self.failed_attempts.items() if len(v) >= self.max_login_attempts]),
            'active_sessions': len(self.session_tokens),
            'rate_limited_ips': len([k for k, v in self.rate_limits.items() if len(v) >= self.rate_limit_max_requests])
        }
        
        return metrics

class InputValidator:
    """Helper class for common input validation patterns"""
    
    @staticmethod
    def validate_exam_answer(answer_data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate exam answer submission"""
        try:
            required_fields = ['question_id', 'selected_index', 'time_spent']
            
            for field in required_fields:
                if field not in answer_data:
                    return False, f"Missing required field: {field}"
            
            # Validate question_id
            if not isinstance(answer_data['question_id'], (str, int)):
                return False, "Invalid question_id format"
            
            # Validate selected_index
            if not isinstance(answer_data['selected_index'], int) or answer_data['selected_index'] < 0 or answer_data['selected_index'] > 3:
                return False, "Invalid selected_index (must be 0-3)"
            
            # Validate time_spent
            if not isinstance(answer_data['time_spent'], (int, float)) or answer_data['time_spent'] < 0:
                return False, "Invalid time_spent (must be positive number)"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def validate_credit_purchase(purchase_data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate credit purchase data"""
        try:
            if 'amount' not in purchase_data:
                return False, "Missing amount field"
            
            amount = purchase_data['amount']
            valid_amounts = [5, 20, 50, 100]  # Valid credit amounts
            
            if amount not in valid_amounts:
                return False, f"Invalid amount. Must be one of: {valid_amounts}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"

def require_authentication(func: Callable) -> Callable:
    """Decorator to require user authentication"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'authenticated' not in st.session_state or not st.session_state.authenticated:
            st.error("🔒 Authentication required")
            st.info("Please log in to access this feature.")
            return None
        return func(*args, **kwargs)
    return wrapper

def require_admin(func: Callable) -> Callable:
    """Decorator to require admin access"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not verify_admin_access():
            st.error("🚫 Admin access required")
            st.info("Please log in with an admin account.")
            return None
        return func(*args, **kwargs)
    return wrapper

def log_admin_action(action: str, details: Dict[str, Any] = None):
    """Log admin action for audit trail"""
    if details is None:
        details = {}
    
    security_manager.log_security_event("admin_action", "medium", {
        "action": action,
        "details": details,
        "admin_user": st.session_state.get('current_user', {}).get('email')
    })

def verify_admin_access() -> bool:
    """Verify if current user has admin access"""
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        return False
    
    current_user = st.session_state.get('current_user', {})
    return current_user.get('role') == 'admin'

# Initialize global security manager
security_manager = SecurityManager()

# Initialize security logging
if 'security_initialized' not in st.session_state:
    st.session_state.security_initialized = True
    security_manager.log_security_event("system_startup", "low", {
        "version": "1.0.0"
    })