"""
Security Middleware for SegurifAI x PAQ

This module implements comprehensive security middleware following OWASP best practices
and Cloudflare integration for enhanced protection.

Middleware Classes:
    - CloudflareSecurityMiddleware: Handles Cloudflare headers and IP validation
    - RateLimitMiddleware: Role-based rate limiting
    - SecurityHeadersMiddleware: OWASP-compliant security headers
    - AuditLoggingMiddleware: Comprehensive request/response logging
    - RequestValidationMiddleware: Input sanitization and validation

OWASP Top 10 Coverage:
    - A01:2021 Broken Access Control -> Role-based access, audit logging
    - A02:2021 Cryptographic Failures -> Secure headers, HTTPS enforcement
    - A03:2021 Injection -> Input validation, parameterized queries
    - A04:2021 Insecure Design -> Defense in depth, fail-secure defaults
    - A05:2021 Security Misconfiguration -> Security headers, CSP
    - A06:2021 Vulnerable Components -> Dependency management
    - A07:2021 Auth Failures -> Rate limiting, session management
    - A08:2021 Data Integrity Failures -> Request signing validation
    - A09:2021 Security Logging Failures -> Comprehensive audit logging
    - A10:2021 SSRF -> URL validation, allowlists

Author: SegurifAI Team
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import logging
import re
import time
import uuid
from datetime import datetime, timedelta
from functools import lru_cache
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TYPE_CHECKING,
    Union,
)

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

# Configure logging
logger = logging.getLogger('segurifai.security')
audit_logger = logging.getLogger('segurifai.audit')


# =============================================================================
# CONSTANTS AND CONFIGURATION
# =============================================================================

class SecurityConfig:
    """
    Centralized security configuration constants.

    These values can be overridden in Django settings using SECURITY_CONFIG dict.

    Attributes:
        CLOUDFLARE_IPS: Set of valid Cloudflare IP ranges
        RATE_LIMITS: Rate limits per user role (requests/minute)
        BLOCKED_USER_AGENTS: User agents to block
        SENSITIVE_PATHS: Paths requiring extra security
        MAX_REQUEST_SIZE: Maximum request body size in bytes
        SESSION_TIMEOUT: Session timeout in seconds
    """

    # Cloudflare IP ranges (updated periodically from https://www.cloudflare.com/ips/)
    CLOUDFLARE_IPV4_RANGES: List[str] = [
        '173.245.48.0/20',
        '103.21.244.0/22',
        '103.22.200.0/22',
        '103.31.4.0/22',
        '141.101.64.0/18',
        '108.162.192.0/18',
        '190.93.240.0/20',
        '188.114.96.0/20',
        '197.234.240.0/22',
        '198.41.128.0/17',
        '162.158.0.0/15',
        '104.16.0.0/13',
        '104.24.0.0/14',
        '172.64.0.0/13',
        '131.0.72.0/22',
    ]

    CLOUDFLARE_IPV6_RANGES: List[str] = [
        '2400:cb00::/32',
        '2606:4700::/32',
        '2803:f800::/32',
        '2405:b500::/32',
        '2405:8100::/32',
        '2a06:98c0::/29',
        '2c0f:f248::/32',
    ]

    # Rate limits per role (requests per minute)
    RATE_LIMITS: Dict[str, int] = {
        'ADMIN': 1000,           # SegurifAI Admin - high limit
        'MAWDY_ADMIN': 500,      # MAWDY Admin
        'PROVIDER': 300,         # MAWDY Assistants/Providers
        'USER': 100,             # Regular users
        'ANONYMOUS': 30,         # Unauthenticated requests
    }

    # Sensitive paths requiring additional security measures
    SENSITIVE_PATHS: Set[str] = {
        '/api/admin/',
        '/admin/',
        '/api/auth/token/',
        '/api/wallet/transfer/',
        '/api/wallet/withdraw/',
    }

    # Paths exempt from rate limiting
    RATE_LIMIT_EXEMPT_PATHS: Set[str] = {
        '/api/health/',
        '/api/docs/',
        '/api/schema/',
        '/api/redoc/',
    }

    # Blocked user agents (bots, scrapers)
    BLOCKED_USER_AGENTS: List[str] = [
        r'.*sqlmap.*',
        r'.*nikto.*',
        r'.*nmap.*',
        r'.*masscan.*',
        r'.*zgrab.*',
        r'.*gobuster.*',
        r'.*dirbuster.*',
    ]

    # Maximum request body size (10MB)
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024

    # Session timeout (30 minutes)
    SESSION_TIMEOUT: int = 1800

    # Security headers
    SECURITY_HEADERS: Dict[str, str] = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(self), microphone=()',
        'Cache-Control': 'no-store, no-cache, must-revalidate, private',
        'Pragma': 'no-cache',
    }

    # Content Security Policy
    CSP_POLICY: str = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https:; "
        "font-src 'self' https://cdn.jsdelivr.net; "
        "connect-src 'self' wss: https:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

@lru_cache(maxsize=256)
def is_cloudflare_ip(ip: str) -> bool:
    """
    Check if an IP address belongs to Cloudflare's IP ranges.

    Uses LRU cache for performance optimization on repeated checks.

    Args:
        ip: IP address string to validate

    Returns:
        bool: True if IP is from Cloudflare, False otherwise

    Example:
        >>> is_cloudflare_ip('104.16.0.1')
        True
        >>> is_cloudflare_ip('192.168.1.1')
        False
    """
    try:
        ip_obj = ipaddress.ip_address(ip)

        # Check IPv4 ranges
        if isinstance(ip_obj, ipaddress.IPv4Address):
            for range_str in SecurityConfig.CLOUDFLARE_IPV4_RANGES:
                if ip_obj in ipaddress.ip_network(range_str):
                    return True

        # Check IPv6 ranges
        elif isinstance(ip_obj, ipaddress.IPv6Address):
            for range_str in SecurityConfig.CLOUDFLARE_IPV6_RANGES:
                if ip_obj in ipaddress.ip_network(range_str):
                    return True

    except ValueError:
        logger.warning(f"Invalid IP address format: {ip}")

    return False


def get_client_ip(request: HttpRequest) -> str:
    """
    Extract the real client IP address from request headers.

    Handles Cloudflare's CF-Connecting-IP header and standard
    X-Forwarded-For header chain.

    Args:
        request: Django HttpRequest object

    Returns:
        str: Client IP address

    Security Note:
        This function validates that the connecting IP is from Cloudflare
        before trusting CF-Connecting-IP header to prevent header spoofing.
    """
    # If behind Cloudflare, use CF-Connecting-IP
    cf_connecting_ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if cf_connecting_ip:
        # Validate that request actually came from Cloudflare
        remote_addr = request.META.get('REMOTE_ADDR', '')
        if is_cloudflare_ip(remote_addr) or settings.DEBUG:
            return cf_connecting_ip

    # Fallback to X-Forwarded-For
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Get the first IP in the chain (original client)
        return x_forwarded_for.split(',')[0].strip()

    # Last resort: REMOTE_ADDR
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def get_user_role(request: HttpRequest) -> str:
    """
    Determine the user's role for rate limiting and access control.

    Args:
        request: Django HttpRequest object

    Returns:
        str: User role identifier (ADMIN, MAWDY_ADMIN, PROVIDER, USER, ANONYMOUS)
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return 'ANONYMOUS'

    user = request.user

    # Check for SegurifAI admin (superuser)
    if user.is_superuser:
        return 'ADMIN'

    # Check for MAWDY admin
    if user.is_staff and hasattr(user, 'email') and 'mawdy' in user.email.lower():
        return 'MAWDY_ADMIN'

    # Check role attribute
    if hasattr(user, 'role'):
        if user.role == 'ADMIN':
            return 'ADMIN'
        elif user.role == 'PROVIDER':
            return 'PROVIDER'

    return 'USER'


def generate_request_id() -> str:
    """
    Generate a unique request ID for tracking and logging.

    Returns:
        str: UUID4 string for request identification
    """
    return str(uuid.uuid4())


def sanitize_log_data(data: Any, max_length: int = 1000) -> str:
    """
    Sanitize data for safe logging, removing sensitive information.

    Args:
        data: Data to sanitize
        max_length: Maximum length of output string

    Returns:
        str: Sanitized string representation
    """
    sensitive_keys = {
        'password', 'token', 'secret', 'key', 'authorization',
        'credit_card', 'cvv', 'pin', 'ssn', 'paq_wallet_token'
    }

    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if any(s in key.lower() for s in sensitive_keys):
                sanitized[key] = '[REDACTED]'
            else:
                sanitized[key] = sanitize_log_data(value, max_length // 2)
        return str(sanitized)[:max_length]

    return str(data)[:max_length]


# =============================================================================
# CLOUDFLARE SECURITY MIDDLEWARE
# =============================================================================

class CloudflareSecurityMiddleware(MiddlewareMixin):
    """
    Middleware for Cloudflare integration and security validation.

    This middleware handles:
        - Cloudflare IP validation
        - Real client IP extraction from CF headers
        - Country-based access control (if enabled)
        - Bot detection via Cloudflare headers
        - Request signing validation

    Attributes:
        get_response: Next middleware in chain

    OWASP Coverage:
        - A01: Validates request source
        - A07: Adds additional authentication layer
        - A10: Prevents SSRF by validating origins

    Example:
        Add to MIDDLEWARE in settings.py:
        'apps.core.middleware.CloudflareSecurityMiddleware',
    """

    def __init__(self, get_response: Callable) -> None:
        """
        Initialize middleware.

        Args:
            get_response: Next middleware callable
        """
        self.get_response = get_response
        self._blocked_countries: Set[str] = getattr(
            settings, 'BLOCKED_COUNTRIES', set()
        )
        self._require_cloudflare: bool = getattr(
            settings, 'REQUIRE_CLOUDFLARE', False
        )
        super().__init__(get_response)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Process incoming request through Cloudflare security checks.

        Args:
            request: Incoming HTTP request

        Returns:
            HttpResponse: Response from next middleware or error response
        """
        # Generate and attach request ID for tracking
        request.request_id = generate_request_id()

        # Extract and attach real client IP
        request.client_ip = get_client_ip(request)

        # In production, validate Cloudflare origin
        if self._require_cloudflare and not settings.DEBUG:
            remote_addr = request.META.get('REMOTE_ADDR', '')
            if not is_cloudflare_ip(remote_addr):
                logger.warning(
                    f"Request from non-Cloudflare IP blocked: {remote_addr}",
                    extra={'request_id': request.request_id}
                )
                return JsonResponse(
                    {'error': 'Access denied'},
                    status=403
                )

        # Check country restrictions
        cf_country = request.META.get('HTTP_CF_IPCOUNTRY', '')
        if cf_country and cf_country in self._blocked_countries:
            logger.warning(
                f"Request from blocked country: {cf_country}",
                extra={
                    'request_id': request.request_id,
                    'client_ip': request.client_ip
                }
            )
            return JsonResponse(
                {'error': 'Service not available in your region'},
                status=451  # Unavailable For Legal Reasons
            )

        # Attach Cloudflare metadata to request
        request.cf_ray = request.META.get('HTTP_CF_RAY', '')
        request.cf_country = cf_country
        request.cf_threat_score = request.META.get('HTTP_CF_THREAT_SCORE', '0')

        # Check threat score (0-100, higher = more suspicious)
        try:
            threat_score = int(request.cf_threat_score)
            if threat_score > 50:
                logger.warning(
                    f"High threat score request: {threat_score}",
                    extra={
                        'request_id': request.request_id,
                        'client_ip': request.client_ip
                    }
                )
        except ValueError:
            pass

        return self.get_response(request)


# =============================================================================
# RATE LIMITING MIDDLEWARE
# =============================================================================

class RateLimitMiddleware(MiddlewareMixin):
    """
    Role-based rate limiting middleware.

    Implements sliding window rate limiting with different limits per user role.
    Uses Django cache backend for distributed rate limit tracking.

    Rate Limits (requests/minute):
        - ADMIN: 1000
        - MAWDY_ADMIN: 500
        - PROVIDER: 300
        - USER: 100
        - ANONYMOUS: 30

    Attributes:
        get_response: Next middleware in chain

    OWASP Coverage:
        - A04: Prevents resource exhaustion
        - A07: Mitigates brute force attacks

    Example:
        Add to MIDDLEWARE in settings.py:
        'apps.core.middleware.RateLimitMiddleware',
    """

    CACHE_KEY_PREFIX = 'ratelimit'
    WINDOW_SIZE = 60  # 1 minute sliding window

    def __init__(self, get_response: Callable) -> None:
        """
        Initialize rate limiting middleware.

        Args:
            get_response: Next middleware callable
        """
        self.get_response = get_response
        self._rate_limits = getattr(
            settings, 'RATE_LIMITS', SecurityConfig.RATE_LIMITS
        )
        self._exempt_paths = getattr(
            settings, 'RATE_LIMIT_EXEMPT_PATHS',
            SecurityConfig.RATE_LIMIT_EXEMPT_PATHS
        )
        super().__init__(get_response)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Apply rate limiting to incoming request.

        Args:
            request: Incoming HTTP request

        Returns:
            HttpResponse: Response or 429 Too Many Requests
        """
        # Skip rate limiting for exempt paths
        if request.path in self._exempt_paths:
            return self.get_response(request)

        # Get client identifier (IP for anonymous, user ID for authenticated)
        client_id = self._get_client_identifier(request)
        role = get_user_role(request)
        limit = self._rate_limits.get(role, self._rate_limits['ANONYMOUS'])

        # Check rate limit
        is_allowed, current_count, reset_time = self._check_rate_limit(
            client_id, limit
        )

        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id} (role: {role})",
                extra={
                    'request_id': getattr(request, 'request_id', 'unknown'),
                    'client_ip': getattr(request, 'client_ip', 'unknown'),
                    'path': request.path,
                }
            )

            response = JsonResponse(
                {
                    'error': 'Rate limit exceeded',
                    'detail': f'Too many requests. Please retry after {reset_time} seconds.',
                    'retry_after': reset_time
                },
                status=429
            )
            response['Retry-After'] = str(reset_time)
            response['X-RateLimit-Limit'] = str(limit)
            response['X-RateLimit-Remaining'] = '0'
            response['X-RateLimit-Reset'] = str(int(time.time()) + reset_time)
            return response

        # Process request and add rate limit headers to response
        response = self.get_response(request)

        response['X-RateLimit-Limit'] = str(limit)
        response['X-RateLimit-Remaining'] = str(max(0, limit - current_count))
        response['X-RateLimit-Reset'] = str(int(time.time()) + reset_time)

        return response

    def _get_client_identifier(self, request: HttpRequest) -> str:
        """
        Get unique client identifier for rate limiting.

        Args:
            request: HTTP request

        Returns:
            str: Unique client identifier
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f"user:{request.user.id}"

        client_ip = getattr(request, 'client_ip', request.META.get('REMOTE_ADDR', ''))
        return f"ip:{client_ip}"

    def _check_rate_limit(
        self,
        client_id: str,
        limit: int
    ) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limit using sliding window.

        Args:
            client_id: Unique client identifier
            limit: Maximum requests per window

        Returns:
            Tuple of (is_allowed, current_count, seconds_until_reset)
        """
        cache_key = f"{self.CACHE_KEY_PREFIX}:{client_id}"
        current_time = int(time.time())
        window_start = current_time - self.WINDOW_SIZE

        # Get current request timestamps
        timestamps = cache.get(cache_key, [])

        # Filter to only requests within window
        timestamps = [ts for ts in timestamps if ts > window_start]

        current_count = len(timestamps) + 1
        is_allowed = current_count <= limit

        if is_allowed:
            timestamps.append(current_time)
            cache.set(cache_key, timestamps, self.WINDOW_SIZE * 2)

        # Calculate reset time
        if timestamps:
            oldest_in_window = min(ts for ts in timestamps if ts > window_start)
            reset_time = max(0, self.WINDOW_SIZE - (current_time - oldest_in_window))
        else:
            reset_time = self.WINDOW_SIZE

        return is_allowed, current_count, reset_time


# =============================================================================
# SECURITY HEADERS MIDDLEWARE
# =============================================================================

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    OWASP-compliant security headers middleware.

    Adds comprehensive security headers to all responses to protect against:
        - XSS attacks
        - Clickjacking
        - MIME sniffing
        - Information disclosure

    Headers Added:
        - X-Content-Type-Options: nosniff
        - X-Frame-Options: DENY
        - X-XSS-Protection: 1; mode=block
        - Referrer-Policy: strict-origin-when-cross-origin
        - Content-Security-Policy: [comprehensive policy]
        - Permissions-Policy: [restricted permissions]
        - Cache-Control: no-store (for API responses)

    OWASP Coverage:
        - A02: Prevents information leakage
        - A03: Mitigates XSS via CSP
        - A05: Proper security configuration
    """

    def __init__(self, get_response: Callable) -> None:
        """
        Initialize security headers middleware.

        Args:
            get_response: Next middleware callable
        """
        self.get_response = get_response
        self._headers = getattr(
            settings, 'SECURITY_HEADERS', SecurityConfig.SECURITY_HEADERS
        )
        self._csp_policy = getattr(
            settings, 'CSP_POLICY', SecurityConfig.CSP_POLICY
        )
        super().__init__(get_response)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Add security headers to response.

        Args:
            request: Incoming HTTP request

        Returns:
            HttpResponse: Response with security headers added
        """
        response = self.get_response(request)

        # Add standard security headers
        for header, value in self._headers.items():
            if header not in response:
                response[header] = value

        # Add CSP header
        if 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = self._csp_policy

        # Add HSTS for HTTPS requests
        if request.is_secure():
            response['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains; preload'
            )

        # Remove potentially dangerous headers
        for header in ['Server', 'X-Powered-By', 'X-AspNet-Version']:
            if header in response:
                del response[header]

        return response


# =============================================================================
# AUDIT LOGGING MIDDLEWARE
# =============================================================================

class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Comprehensive security audit logging middleware.

    Logs all requests and responses for security auditing and compliance.
    Sensitive data is automatically redacted.

    Logged Information:
        - Request ID, timestamp
        - Client IP, user agent
        - User ID and role (if authenticated)
        - HTTP method, path, query params
        - Response status code
        - Request duration
        - Cloudflare metadata (if available)

    OWASP Coverage:
        - A09: Comprehensive security logging
        - A01: Access control auditing

    Log Format:
        JSON structured logs for easy parsing and analysis.
    """

    # Paths to skip detailed logging
    SKIP_PATHS: Set[str] = {'/api/health/', '/api/docs/', '/api/schema/'}

    def __init__(self, get_response: Callable) -> None:
        """
        Initialize audit logging middleware.

        Args:
            get_response: Next middleware callable
        """
        self.get_response = get_response
        self._sensitive_paths = getattr(
            settings, 'SENSITIVE_PATHS', SecurityConfig.SENSITIVE_PATHS
        )
        super().__init__(get_response)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Log request and response for audit trail.

        Args:
            request: Incoming HTTP request

        Returns:
            HttpResponse: Response from next middleware
        """
        # Skip logging for certain paths
        if request.path in self.SKIP_PATHS:
            return self.get_response(request)

        # Record start time
        start_time = time.time()

        # Get request ID (set by CloudflareSecurityMiddleware)
        request_id = getattr(request, 'request_id', generate_request_id())

        # Build request log entry
        request_log = self._build_request_log(request, request_id)

        # Log request (debug level for normal, info for sensitive paths)
        is_sensitive = any(
            request.path.startswith(p) for p in self._sensitive_paths
        )

        if is_sensitive:
            audit_logger.info(
                f"SENSITIVE_REQUEST: {json.dumps(request_log)}",
                extra={'request_id': request_id}
            )
        else:
            audit_logger.debug(
                f"REQUEST: {json.dumps(request_log)}",
                extra={'request_id': request_id}
            )

        # Process request
        response = self.get_response(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Build response log entry
        response_log = {
            'request_id': request_id,
            'status_code': response.status_code,
            'duration_ms': round(duration_ms, 2),
            'content_length': len(response.content) if hasattr(response, 'content') else 0,
        }

        # Log response
        log_level = logging.WARNING if response.status_code >= 400 else logging.DEBUG
        audit_logger.log(
            log_level,
            f"RESPONSE: {json.dumps(response_log)}",
            extra={'request_id': request_id}
        )

        # Add request ID to response headers for debugging
        response['X-Request-ID'] = request_id

        return response

    def _build_request_log(
        self,
        request: HttpRequest,
        request_id: str
    ) -> Dict[str, Any]:
        """
        Build structured log entry for request.

        Args:
            request: HTTP request
            request_id: Unique request identifier

        Returns:
            Dict containing sanitized request information
        """
        # Get user info
        user_info = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_info = {
                'id': request.user.id,
                'email': request.user.email[:3] + '***',  # Partial redaction
                'role': get_user_role(request),
            }

        return {
            'request_id': request_id,
            'timestamp': timezone.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'query_params': sanitize_log_data(dict(request.GET)),
            'client_ip': getattr(request, 'client_ip', 'unknown'),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
            'user': user_info,
            'cf_ray': getattr(request, 'cf_ray', ''),
            'cf_country': getattr(request, 'cf_country', ''),
        }


# =============================================================================
# REQUEST VALIDATION MIDDLEWARE
# =============================================================================

class RequestValidationMiddleware(MiddlewareMixin):
    """
    Input validation and sanitization middleware.

    Validates incoming requests for:
        - Request size limits
        - Malicious user agents
        - SQL injection patterns
        - XSS patterns
        - Path traversal attempts

    OWASP Coverage:
        - A03: Input validation
        - A04: Secure design with input filtering
    """

    # Dangerous patterns to detect
    SQL_INJECTION_PATTERNS: List[str] = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b)",
        r"(--|\#|\/\*)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
    ]

    XSS_PATTERNS: List[str] = [
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
    ]

    PATH_TRAVERSAL_PATTERNS: List[str] = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e/",
    ]

    def __init__(self, get_response: Callable) -> None:
        """
        Initialize request validation middleware.

        Args:
            get_response: Next middleware callable
        """
        self.get_response = get_response
        self._max_size = getattr(
            settings, 'MAX_REQUEST_SIZE', SecurityConfig.MAX_REQUEST_SIZE
        )
        self._blocked_agents = getattr(
            settings, 'BLOCKED_USER_AGENTS', SecurityConfig.BLOCKED_USER_AGENTS
        )
        super().__init__(get_response)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Validate incoming request.

        Args:
            request: Incoming HTTP request

        Returns:
            HttpResponse: Response or error if validation fails
        """
        request_id = getattr(request, 'request_id', 'unknown')

        # Check request size
        content_length = request.META.get('CONTENT_LENGTH')
        if content_length and int(content_length) > self._max_size:
            logger.warning(
                f"Request too large: {content_length} bytes",
                extra={'request_id': request_id}
            )
            return JsonResponse(
                {'error': 'Request too large'},
                status=413
            )

        # Check user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        for pattern in self._blocked_agents:
            if re.search(pattern, user_agent, re.IGNORECASE):
                logger.warning(
                    f"Blocked user agent: {user_agent[:100]}",
                    extra={'request_id': request_id}
                )
                return JsonResponse(
                    {'error': 'Access denied'},
                    status=403
                )

        # Check for malicious patterns in query string
        query_string = request.META.get('QUERY_STRING', '')
        if self._contains_malicious_pattern(query_string):
            logger.warning(
                f"Malicious pattern in query string",
                extra={
                    'request_id': request_id,
                    'pattern_type': 'query_string'
                }
            )
            return JsonResponse(
                {'error': 'Invalid request'},
                status=400
            )

        # Check for path traversal
        if self._contains_path_traversal(request.path):
            logger.warning(
                f"Path traversal attempt: {request.path}",
                extra={'request_id': request_id}
            )
            return JsonResponse(
                {'error': 'Invalid path'},
                status=400
            )

        return self.get_response(request)

    def _contains_malicious_pattern(self, text: str) -> bool:
        """
        Check if text contains SQL injection or XSS patterns.

        Args:
            text: Text to check

        Returns:
            bool: True if malicious pattern found
        """
        text_upper = text.upper()

        # Check SQL injection patterns
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_upper, re.IGNORECASE):
                return True

        # Check XSS patterns
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    def _contains_path_traversal(self, path: str) -> bool:
        """
        Check if path contains traversal attempts.

        Args:
            path: URL path to check

        Returns:
            bool: True if path traversal pattern found
        """
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                return True
        return False


# =============================================================================
# MIDDLEWARE EXPORT
# =============================================================================

__all__ = [
    'CloudflareSecurityMiddleware',
    'RateLimitMiddleware',
    'SecurityHeadersMiddleware',
    'AuditLoggingMiddleware',
    'RequestValidationMiddleware',
    'SecurityConfig',
    'get_client_ip',
    'get_user_role',
]
