"""
Security Settings for SegurifAI x PAQ

This module contains all security-related Django settings following OWASP best practices.
Import this in your main settings.py file.

Usage:
    from .security_settings import *

OWASP Compliance:
    - A01: Broken Access Control - Role-based middleware, CORS configuration
    - A02: Cryptographic Failures - Strong password hashing, secure sessions
    - A03: Injection - Input validation middleware
    - A04: Insecure Design - Defense in depth approach
    - A05: Security Misconfiguration - Hardened default settings
    - A06: Vulnerable Components - Dependency management recommendations
    - A07: Auth Failures - Strong password policies, rate limiting
    - A08: Data Integrity - CSRF protection, signed cookies
    - A09: Security Logging - Comprehensive logging configuration
    - A10: SSRF - URL validation, Cloudflare protection

Author: SegurifAI Team
Version: 1.0.0
"""

import os
from typing import List, Dict, Any

# =============================================================================
# ENVIRONMENT DETECTION
# =============================================================================

# Detect environment (default to development)
ENVIRONMENT = os.environ.get('DJANGO_ENVIRONMENT', 'development')
IS_PRODUCTION = ENVIRONMENT == 'production'
IS_STAGING = ENVIRONMENT == 'staging'
IS_DEVELOPMENT = ENVIRONMENT in ('development', 'local')

# =============================================================================
# SECURITY MIDDLEWARE CONFIGURATION
# =============================================================================

# Security middleware to add to MIDDLEWARE setting
SECURITY_MIDDLEWARE: List[str] = [
    'apps.core.middleware.CloudflareSecurityMiddleware',
    'apps.core.middleware.RequestValidationMiddleware',
    'apps.core.middleware.RateLimitMiddleware',
    'apps.core.middleware.SecurityHeadersMiddleware',
    'apps.core.middleware.AuditLoggingMiddleware',
]

# Rate limits per role (requests per minute)
RATE_LIMITS: Dict[str, int] = {
    'ADMIN': 1000,           # SegurifAI Admin
    'MAWDY_ADMIN': 500,      # MAWDY Admin
    'PROVIDER': 300,         # MAWDY Assistants
    'USER': 100,             # Regular users
    'ANONYMOUS': 30,         # Unauthenticated
}

# Paths exempt from rate limiting
RATE_LIMIT_EXEMPT_PATHS = {
    '/api/health/',
    '/api/docs/',
    '/api/schema/',
    '/api/redoc/',
}

# Sensitive paths requiring extra logging
SENSITIVE_PATHS = {
    '/api/admin/',
    '/admin/',
    '/api/auth/token/',
    '/api/wallet/transfer/',
    '/api/wallet/withdraw/',
}

# Cloudflare settings
REQUIRE_CLOUDFLARE = IS_PRODUCTION  # Only require in production
BLOCKED_COUNTRIES: set = set()  # Add country codes to block (e.g., {'XX', 'YY'})

# Request validation
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB

# Blocked user agents (security scanners, bots)
BLOCKED_USER_AGENTS = [
    r'.*sqlmap.*',
    r'.*nikto.*',
    r'.*nmap.*',
    r'.*masscan.*',
    r'.*zgrab.*',
    r'.*gobuster.*',
    r'.*dirbuster.*',
]

# =============================================================================
# DJANGO SECURITY SETTINGS
# =============================================================================

# Session security
SESSION_COOKIE_SECURE = IS_PRODUCTION
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

# CSRF protection
CSRF_COOKIE_SECURE = IS_PRODUCTION
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = [
    'https://segurifai.gt',
    'https://www.segurifai.gt',
    'https://api.segurifai.gt',
]

# Security middleware settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# HTTPS settings (production only)
if IS_PRODUCTION:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# =============================================================================
# PASSWORD VALIDATION (OWASP Compliant)
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'max_similarity': 0.7,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # OWASP recommends minimum 12 characters
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Password hashing (use Argon2 - OWASP recommended)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# =============================================================================
# CORS CONFIGURATION
# =============================================================================

CORS_ALLOWED_ORIGINS = [
    'https://segurifai.gt',
    'https://www.segurifai.gt',
    'https://app.segurifai.gt',
]

if IS_DEVELOPMENT:
    CORS_ALLOWED_ORIGINS += [
        'http://localhost:3000',
        'http://localhost:8000',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:8000',
    ]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_EXPOSE_HEADERS = [
    'x-request-id',
    'x-ratelimit-limit',
    'x-ratelimit-remaining',
    'x-ratelimit-reset',
]

# =============================================================================
# SECURITY HEADERS (OWASP Compliant)
# =============================================================================

SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(self), microphone=()',
    'Cache-Control': 'no-store, no-cache, must-revalidate, private',
    'Pragma': 'no-cache',
}

# Content Security Policy
CSP_POLICY = (
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
# LOGGING CONFIGURATION (Security Audit)
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'security': {
            'format': '[{asctime}] [{levelname}] [{name}] {message}',
            'style': '{',
        },
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/security.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'security',
        },
        'audit_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/audit.log',
            'maxBytes': 52428800,  # 50MB
            'backupCount': 20,
            'formatter': 'json',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/error.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['console', 'security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'segurifai.security': {
            'handlers': ['console', 'security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'segurifai.audit': {
            'handlers': ['audit_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# =============================================================================
# JWT SETTINGS (Secure Defaults)
# =============================================================================

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': os.environ.get('JWT_SECRET_KEY', 'change-me-in-production'),
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': 'segurifai.gt',

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
}

# =============================================================================
# FILE UPLOAD SECURITY
# =============================================================================

# Maximum upload size (10MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# Allowed file types for uploads
ALLOWED_UPLOAD_EXTENSIONS = [
    '.jpg', '.jpeg', '.png', '.gif', '.webp',  # Images
    '.pdf',  # Documents
    '.doc', '.docx',  # Word documents
]

# Allowed MIME types
ALLOWED_UPLOAD_MIMETYPES = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
]

# =============================================================================
# EXPORT ALL SETTINGS
# =============================================================================

__all__ = [
    'SECURITY_MIDDLEWARE',
    'RATE_LIMITS',
    'RATE_LIMIT_EXEMPT_PATHS',
    'SENSITIVE_PATHS',
    'REQUIRE_CLOUDFLARE',
    'BLOCKED_COUNTRIES',
    'MAX_REQUEST_SIZE',
    'BLOCKED_USER_AGENTS',
    'SESSION_COOKIE_SECURE',
    'SESSION_COOKIE_HTTPONLY',
    'SESSION_COOKIE_SAMESITE',
    'SESSION_COOKIE_AGE',
    'SESSION_EXPIRE_AT_BROWSER_CLOSE',
    'CSRF_COOKIE_SECURE',
    'CSRF_COOKIE_HTTPONLY',
    'CSRF_COOKIE_SAMESITE',
    'CSRF_TRUSTED_ORIGINS',
    'AUTH_PASSWORD_VALIDATORS',
    'PASSWORD_HASHERS',
    'CORS_ALLOWED_ORIGINS',
    'CORS_ALLOW_CREDENTIALS',
    'CORS_ALLOW_HEADERS',
    'CORS_EXPOSE_HEADERS',
    'SECURITY_HEADERS',
    'CSP_POLICY',
    'LOGGING',
    'SIMPLE_JWT',
    'DATA_UPLOAD_MAX_MEMORY_SIZE',
    'FILE_UPLOAD_MAX_MEMORY_SIZE',
    'ALLOWED_UPLOAD_EXTENSIONS',
    'ALLOWED_UPLOAD_MIMETYPES',
]
