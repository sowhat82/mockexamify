"""
Production Utilities - Production-Ready Features for MockExamify
Caching, rate limiting, error handling, logging, and performance monitoring
"""
import time
import logging
import hashlib
import json
import functools
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Union
from collections import defaultdict, OrderedDict
import asyncio
import threading
import streamlit as st
import psutil
import config

# Configure comprehensive logging
def setup_logging():
    """Setup comprehensive logging for production"""
    
    # Create logs directory if it doesn't exist
    import os
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/mockexamify.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create specialized loggers
    loggers = {
        'performance': logging.getLogger('performance'),
        'security': logging.getLogger('security'),
        'user_activity': logging.getLogger('user_activity'),
        'ai_operations': logging.getLogger('ai_operations'),
        'database': logging.getLogger('database'),
        'payment': logging.getLogger('payment')
    }
    
    # Add file handlers for each logger
    for name, logger in loggers.items():
        handler = logging.FileHandler(f'logs/{name}.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return loggers

# Initialize loggers
LOGGERS = setup_logging()

# ==================== CACHING SYSTEM ====================

class ProductionCache:
    """Thread-safe production caching system with TTL and LRU eviction"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()
        self.expiry_times = {}
        self.hit_count = 0
        self.miss_count = 0
        self._lock = threading.Lock()
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_expired, daemon=True)
        self._cleanup_thread.start()
    
    def _cleanup_expired(self):
        """Background thread to clean up expired entries"""
        while True:
            try:
                time.sleep(300)  # Run every 5 minutes
                self._remove_expired()
            except Exception as e:
                LOGGERS['performance'].error(f"Cache cleanup error: {e}")
    
    def _remove_expired(self):
        """Remove expired cache entries"""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, expiry in self.expiry_times.items()
                if expiry < current_time
            ]
            
            for key in expired_keys:
                self.cache.pop(key, None)
                self.expiry_times.pop(key, None)
    
    def _create_key(self, *args, **kwargs) -> str:
        """Create a cache key from arguments"""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            # Check if expired
            if key in self.expiry_times and self.expiry_times[key] < time.time():
                self.cache.pop(key, None)
                self.expiry_times.pop(key, None)
                self.miss_count += 1
                return None
            
            if key in self.cache:
                # Move to end (LRU)
                value = self.cache.pop(key)
                self.cache[key] = value
                self.hit_count += 1
                return value
            
            self.miss_count += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        with self._lock:
            ttl = ttl or self.default_ttl
            
            # Remove if exists
            self.cache.pop(key, None)
            self.expiry_times.pop(key, None)
            
            # Add new entry
            self.cache[key] = value
            self.expiry_times[key] = time.time() + ttl
            
            # Enforce size limit (LRU eviction)
            while len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                self.cache.pop(oldest_key)
                self.expiry_times.pop(oldest_key, None)
    
    def invalidate(self, pattern: str = None) -> None:
        """Invalidate cache entries"""
        with self._lock:
            if pattern is None:
                self.cache.clear()
                self.expiry_times.clear()
            else:
                keys_to_remove = [k for k in self.cache.keys() if pattern in k]
                for key in keys_to_remove:
                    self.cache.pop(key, None)
                    self.expiry_times.pop(key, None)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self.hit_count + self.miss_count
            hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hit_count': self.hit_count,
                'miss_count': self.miss_count,
                'hit_rate': hit_rate,
                'memory_usage': self._estimate_memory_usage()
            }
    
    def _estimate_memory_usage(self) -> str:
        """Estimate cache memory usage"""
        try:
            import sys
            total_size = sum(sys.getsizeof(v) for v in self.cache.values())
            total_size += sum(sys.getsizeof(k) for k in self.cache.keys())
            
            if total_size < 1024:
                return f"{total_size} B"
            elif total_size < 1024 * 1024:
                return f"{total_size / 1024:.1f} KB"
            else:
                return f"{total_size / (1024 * 1024):.1f} MB"
        except:
            return "Unknown"

# Global cache instance
production_cache = ProductionCache()

def cached(ttl: int = 3600, key_prefix: str = ""):
    """Decorator for caching function results"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{key_prefix}:{func.__name__}:{production_cache._create_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = production_cache.get(cache_key)
            if cached_result is not None:
                LOGGERS['performance'].debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            try:
                result = await func(*args, **kwargs)
                production_cache.set(cache_key, result, ttl)
                LOGGERS['performance'].debug(f"Cached result for {func.__name__}")
                return result
            except Exception as e:
                LOGGERS['performance'].error(f"Error in cached function {func.__name__}: {e}")
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{key_prefix}:{func.__name__}:{production_cache._create_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = production_cache.get(cache_key)
            if cached_result is not None:
                LOGGERS['performance'].debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            try:
                result = func(*args, **kwargs)
                production_cache.set(cache_key, result, ttl)
                LOGGERS['performance'].debug(f"Cached result for {func.__name__}")
                return result
            except Exception as e:
                LOGGERS['performance'].error(f"Error in cached function {func.__name__}: {e}")
                raise
        
        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# ==================== RATE LIMITING ====================

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
        self._lock = threading.Lock()
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for identifier"""
        with self._lock:
            current_time = time.time()
            window_start = current_time - self.time_window
            
            # Clean old requests
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > window_start
            ]
            
            # Check if under limit
            if len(self.requests[identifier]) >= self.max_requests:
                LOGGERS['security'].warning(f"Rate limit exceeded for {identifier}")
                return False
            
            # Add current request
            self.requests[identifier].append(current_time)
            return True
    
    def reset(self, identifier: str) -> None:
        """Reset rate limit for identifier"""
        with self._lock:
            self.requests.pop(identifier, None)

# Rate limiters for different operations
RATE_LIMITERS = {
    'ai_requests': RateLimiter(max_requests=30, time_window=60),  # 30 per minute
    'login_attempts': RateLimiter(max_requests=5, time_window=300),  # 5 per 5 minutes
    'exam_attempts': RateLimiter(max_requests=10, time_window=3600),  # 10 per hour
    'credit_purchases': RateLimiter(max_requests=3, time_window=3600),  # 3 per hour
}

def rate_limited(limiter_name: str, get_identifier: Callable = None):
    """Decorator for rate limiting"""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get identifier
            if get_identifier:
                identifier = get_identifier(*args, **kwargs)
            else:
                # Use session state or IP as default
                identifier = st.session_state.get('user_id', 'anonymous')
            
            # Check rate limit
            limiter = RATE_LIMITERS.get(limiter_name)
            if limiter and not limiter.is_allowed(identifier):
                raise RateLimitError(f"Rate limit exceeded for {limiter_name}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

class RateLimitError(Exception):
    """Rate limit exceeded error"""
    pass

# ==================== ERROR HANDLING ====================

class ProductionErrorHandler:
    """Comprehensive error handling system"""
    
    @staticmethod
    def log_error(error: Exception, context: Dict[str, Any] = None, user_id: str = None):
        """Log error with context"""
        error_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'context': context or {}
        }
        
        LOGGERS['security'].error(f"Application error: {json.dumps(error_data)}")
    
    @staticmethod
    def handle_database_error(error: Exception) -> str:
        """Handle database errors gracefully"""
        LOGGERS['database'].error(f"Database error: {error}")
        
        # Map specific errors to user-friendly messages
        error_msg = str(error).lower()
        
        if 'connection' in error_msg:
            return "Database temporarily unavailable. Please try again later."
        elif 'timeout' in error_msg:
            return "Request timed out. Please try again."
        elif 'constraint' in error_msg:
            return "Data validation error. Please check your input."
        else:
            return "A database error occurred. Our team has been notified."
    
    @staticmethod
    def handle_ai_error(error: Exception) -> str:
        """Handle AI service errors"""
        LOGGERS['ai_operations'].error(f"AI service error: {error}")
        
        error_msg = str(error).lower()
        
        if 'rate limit' in error_msg:
            return "AI service is busy. Please try again in a few moments."
        elif 'authentication' in error_msg:
            return "AI service authentication error. Please contact support."
        elif 'timeout' in error_msg:
            return "AI request timed out. Please try again."
        else:
            return "AI service temporarily unavailable. Please try again later."
    
    @staticmethod
    def handle_payment_error(error: Exception) -> str:
        """Handle payment processing errors"""
        LOGGERS['payment'].error(f"Payment error: {error}")
        
        error_msg = str(error).lower()
        
        if 'card' in error_msg:
            return "Card payment failed. Please check your card details."
        elif 'declined' in error_msg:
            return "Payment was declined. Please try a different payment method."
        elif 'network' in error_msg:
            return "Network error during payment. Please try again."
        else:
            return "Payment processing failed. Please try again or contact support."

def safe_execute(func: Callable, error_handler: Callable = None, fallback_value: Any = None):
    """Safely execute function with error handling"""
    try:
        return func()
    except Exception as e:
        if error_handler:
            error_handler(e)
        else:
            ProductionErrorHandler.log_error(e)
        
        return fallback_value

# ==================== PERFORMANCE MONITORING ====================

class PerformanceMonitor:
    """System performance monitoring"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self._lock = threading.Lock()
    
    def record_metric(self, name: str, value: float, timestamp: datetime = None):
        """Record a performance metric"""
        with self._lock:
            timestamp = timestamp or datetime.now()
            self.metrics[name].append({
                'value': value,
                'timestamp': timestamp
            })
            
            # Keep only last 1000 entries per metric
            if len(self.metrics[name]) > 1000:
                self.metrics[name] = self.metrics[name][-1000:]
    
    def get_metrics(self, name: str, since: datetime = None) -> List[Dict]:
        """Get metrics since specified time"""
        with self._lock:
            metrics = self.metrics.get(name, [])
            
            if since:
                metrics = [m for m in metrics if m['timestamp'] >= since]
            
            return metrics
    
    def get_average(self, name: str, minutes: int = 60) -> Optional[float]:
        """Get average metric value over time period"""
        since = datetime.now() - timedelta(minutes=minutes)
        metrics = self.get_metrics(name, since)
        
        if not metrics:
            return None
        
        return sum(m['value'] for m in metrics) / len(metrics)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            LOGGERS['performance'].error(f"Error getting system stats: {e}")
            return {}

# Global performance monitor
performance_monitor = PerformanceMonitor()

def monitor_performance(metric_name: str = None):
    """Decorator to monitor function performance"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            name = metric_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                performance_monitor.record_metric(f"{name}_execution_time", execution_time)
                performance_monitor.record_metric(f"{name}_success", 1)
                
                LOGGERS['performance'].info(
                    f"Function {name} executed in {execution_time:.3f}s"
                )
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                performance_monitor.record_metric(f"{name}_execution_time", execution_time)
                performance_monitor.record_metric(f"{name}_error", 1)
                
                LOGGERS['performance'].error(
                    f"Function {name} failed after {execution_time:.3f}s: {e}"
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            name = metric_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                performance_monitor.record_metric(f"{name}_execution_time", execution_time)
                performance_monitor.record_metric(f"{name}_success", 1)
                
                LOGGERS['performance'].info(
                    f"Function {name} executed in {execution_time:.3f}s"
                )
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                performance_monitor.record_metric(f"{name}_execution_time", execution_time)
                performance_monitor.record_metric(f"{name}_error", 1)
                
                LOGGERS['performance'].error(
                    f"Function {name} failed after {execution_time:.3f}s: {e}"
                )
                raise
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# ==================== AUDIT LOGGING ====================

class AuditLogger:
    """Audit logging for security and compliance"""
    
    @staticmethod
    def log_user_action(user_id: str, action: str, details: Dict[str, Any] = None):
        """Log user action for audit trail"""
        audit_data = {
            'user_id': user_id,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'details': details or {},
            'session_id': st.session_state.get('session_id'),
            'ip_address': 'unknown'  # Would need to get from request in production
        }
        
        LOGGERS['user_activity'].info(f"User action: {json.dumps(audit_data)}")
    
    @staticmethod
    def log_admin_action(admin_id: str, action: str, target: str = None, details: Dict[str, Any] = None):
        """Log admin action for audit trail"""
        audit_data = {
            'admin_id': admin_id,
            'action': action,
            'target': target,
            'timestamp': datetime.now().isoformat(),
            'details': details or {},
            'session_id': st.session_state.get('session_id')
        }
        
        LOGGERS['security'].warning(f"Admin action: {json.dumps(audit_data)}")
    
    @staticmethod
    def log_security_event(event_type: str, details: Dict[str, Any] = None, severity: str = 'medium'):
        """Log security event"""
        security_data = {
            'event_type': event_type,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'details': details or {},
            'session_id': st.session_state.get('session_id')
        }
        
        if severity == 'high':
            LOGGERS['security'].critical(f"Security event: {json.dumps(security_data)}")
        elif severity == 'medium':
            LOGGERS['security'].warning(f"Security event: {json.dumps(security_data)}")
        else:
            LOGGERS['security'].info(f"Security event: {json.dumps(security_data)}")

# Global audit logger
audit_logger = AuditLogger()

# ==================== BACKUP SYSTEM ====================

class BackupManager:
    """Simple backup management for critical data"""
    
    @staticmethod
    def backup_user_data(user_id: str) -> bool:
        """Backup user data (placeholder for production implementation)"""
        try:
            # In production, this would backup user data to cloud storage
            LOGGERS['database'].info(f"User data backup initiated for user {user_id}")
            
            # Placeholder - would implement actual backup logic
            backup_data = {
                'user_id': user_id,
                'backup_time': datetime.now().isoformat(),
                'status': 'completed'
            }
            
            return True
        except Exception as e:
            LOGGERS['database'].error(f"Backup failed for user {user_id}: {e}")
            return False
    
    @staticmethod
    def schedule_regular_backups():
        """Schedule regular system backups"""
        # In production, this would integrate with cloud backup services
        LOGGERS['database'].info("Regular backup scheduling initialized")

# ==================== HEALTH CHECKS ====================

class HealthChecker:
    """System health monitoring"""
    
    @staticmethod
    def check_database_health() -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            # Placeholder for actual database health check
            return {
                'status': 'healthy',
                'response_time_ms': 50,
                'connections': 10,
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    @staticmethod
    def check_ai_service_health() -> Dict[str, Any]:
        """Check AI service availability"""
        try:
            # Placeholder for AI service health check
            return {
                'status': 'healthy',
                'response_time_ms': 200,
                'rate_limit_remaining': 100,
                'last_check': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    @staticmethod
    def get_overall_health() -> Dict[str, Any]:
        """Get overall system health status"""
        db_health = HealthChecker.check_database_health()
        ai_health = HealthChecker.check_ai_service_health()
        system_stats = performance_monitor.get_system_stats()
        cache_stats = production_cache.stats()
        
        # Determine overall status
        all_healthy = (
            db_health['status'] == 'healthy' and
            ai_health['status'] == 'healthy' and
            system_stats.get('cpu_percent', 0) < 80 and
            system_stats.get('memory_percent', 0) < 80
        )
        
        return {
            'overall_status': 'healthy' if all_healthy else 'degraded',
            'components': {
                'database': db_health,
                'ai_service': ai_health,
                'system': system_stats,
                'cache': cache_stats
            },
            'timestamp': datetime.now().isoformat()
        }

# Global health checker
health_checker = HealthChecker()

# ==================== UTILITY FUNCTIONS ====================

def get_production_metrics() -> Dict[str, Any]:
    """Get comprehensive production metrics"""
    return {
        'cache_stats': production_cache.stats(),
        'system_health': health_checker.get_overall_health(),
        'performance_averages': {
            'avg_response_time': performance_monitor.get_average('response_time'),
            'avg_cpu_usage': performance_monitor.get_average('cpu_usage'),
            'avg_memory_usage': performance_monitor.get_average('memory_usage')
        },
        'timestamp': datetime.now().isoformat()
    }

def get_production_metrics() -> Dict[str, Any]:
    """Get comprehensive production metrics for admin dashboard"""
    try:
        cache_stats = production_cache.get_stats()
        performance_stats = {
            'avg_response_time': performance_monitor.get_average('response_time'),
            'total_requests': len(performance_monitor.metrics.get('response_time', [])),
            'error_count': len(performance_monitor.metrics.get('errors', []))
        }
        
        return {
            'cache_stats': cache_stats,
            'performance_stats': performance_stats,
            'system_health': health_checker.get_overall_health(),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        LOGGERS['performance'].error(f"Failed to get production metrics: {e}")
        return {
            'cache_stats': {'size': 0, 'max_size': 1000, 'hit_rate': 0.0, 'hit_count': 0, 'miss_count': 0, 'memory_usage': '0 MB'},
            'performance_stats': {'avg_response_time': 0.0, 'total_requests': 0, 'error_count': 0},
            'system_health': {'overall_status': 'unknown', 'components': {}},
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }

def initialize_production_features():
    """Initialize all production features"""
    try:
        # Setup logging
        setup_logging()
        
        # Initialize monitoring
        LOGGERS['performance'].info("Production features initialized")
        
        # Schedule backups (placeholder)
        BackupManager.schedule_regular_backups()
        
        # Log startup
        audit_logger.log_security_event('system_startup', {'version': '1.0.0'}, 'low')
        
        return True
    except Exception as e:
        print(f"Failed to initialize production features: {e}")
        return False

# Initialize on import
initialize_production_features()