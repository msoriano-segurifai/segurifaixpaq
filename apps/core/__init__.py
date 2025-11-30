"""
Core Application Module for SegurifAI x PAQ

This module contains shared utilities, middleware, and security components
used across the entire application.

Components:
    - Security middleware (Cloudflare, rate limiting, audit logging)
    - Base models and mixins
    - Utility functions
    - Constants and enums

Security Features:
    - OWASP Top 10 compliance
    - Role-based access control
    - Audit logging
    - Rate limiting by user role
    - Cloudflare integration

Author: SegurifAI Team
Version: 1.0.0
"""

__version__ = '1.0.0'
__author__ = 'SegurifAI Team'
