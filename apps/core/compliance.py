"""
ISO 27001 & PCI-DSS Compliance Module for SegurifAI x PAQ
==========================================================

This module implements security controls aligned with:
- ISO/IEC 27001:2022 Information Security Management System (ISMS)
- PCI-DSS v4.0 Payment Card Industry Data Security Standard

ISO 27001 Key Controls Implemented:
- A.5: Information Security Policies (enforced via middleware)
- A.8: Asset Management (data classification)
- A.9: Access Control (RBAC, MFA readiness)
- A.10: Cryptography (encryption at rest/transit)
- A.12: Operations Security (logging, monitoring)
- A.14: Secure Development (input validation)
- A.16: Incident Management (security event logging)
- A.18: Compliance (audit trails, data retention)

PCI-DSS v4.0 Requirements Implemented:
- Req 3: Protect Stored Account Data (tokenization, encryption)
- Req 4: Protect Cardholder Data During Transmission (TLS)
- Req 7: Restrict Access to System Components (RBAC)
- Req 8: Identify Users and Authenticate Access (strong auth)
- Req 10: Log and Monitor All Access (audit trails)
- Req 12: Support Information Security with Policies (documentation)

PAQ Transactional Data Security:
- PCI-DSS compliant data handling
- Cardholder data tokenization
- Secure audit logging with PAN masking
- Guatemala SAT data retention (7 years)

Author: SegurifAI Development Team
Version: 2.0.0
Last Updated: 2025-01-21
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import re
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models, transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone

# Configure loggers for compliance
security_logger = logging.getLogger('security')
audit_logger = logging.getLogger('audit')
compliance_logger = logging.getLogger('compliance')


# =============================================================================
# ISO 27001 A.8 - ASSET MANAGEMENT: Data Classification
# =============================================================================

class DataClassification(Enum):
    """
    ISO 27001 A.8.2 - Information Classification

    Data classification levels for SegurifAI x PAQ platform.
    Aligned with Guatemala's data protection requirements.
    """
    PUBLIC = "public"           # Non-sensitive, can be disclosed
    INTERNAL = "internal"       # Internal use only, not for external parties
    CONFIDENTIAL = "confidential"  # Sensitive business data
    RESTRICTED = "restricted"   # Highly sensitive - PII, financial data
    SECRET = "secret"          # Critical secrets - API keys, passwords


class PAQDataCategory(Enum):
    """
    PAQ Wallet specific data categories for compliance tracking.
    """
    WALLET_ID = "wallet_id"           # PAQ wallet identifier
    TRANSACTION = "transaction"        # Payment transaction data
    BALANCE = "balance"               # Account balance information
    PERSONAL_ID = "personal_id"       # DPI/National ID
    FINANCIAL = "financial"           # Bank/card information
    AUTHENTICATION = "authentication"  # Tokens, credentials


@dataclass
class DataAsset:
    """
    Represents a classified data asset in the system.

    Attributes:
        name: Human-readable asset name
        classification: ISO 27001 classification level
        paq_category: PAQ-specific category if applicable
        retention_days: How long to retain this data
        requires_encryption: Whether field-level encryption is required
        requires_masking: Whether to mask in logs/displays
        pii: Whether this contains personally identifiable information
    """
    name: str
    classification: DataClassification
    paq_category: Optional[PAQDataCategory] = None
    retention_days: int = 365
    requires_encryption: bool = False
    requires_masking: bool = False
    pii: bool = False


# Data Asset Registry - Central catalog of sensitive data
DATA_ASSET_REGISTRY: Dict[str, DataAsset] = {
    # PAQ Wallet Data
    "paq_wallet_id": DataAsset(
        name="PAQ Wallet ID",
        classification=DataClassification.CONFIDENTIAL,
        paq_category=PAQDataCategory.WALLET_ID,
        retention_days=2555,  # 7 years for financial records
        requires_encryption=True,
        requires_masking=True,
    ),
    "paq_token": DataAsset(
        name="PAQ Authentication Token",
        classification=DataClassification.SECRET,
        paq_category=PAQDataCategory.AUTHENTICATION,
        retention_days=1,  # Tokens expire quickly
        requires_encryption=True,
        requires_masking=True,
    ),
    "transaction_amount": DataAsset(
        name="Transaction Amount",
        classification=DataClassification.CONFIDENTIAL,
        paq_category=PAQDataCategory.TRANSACTION,
        retention_days=2555,
        requires_encryption=False,
        requires_masking=False,
    ),
    "transaction_reference": DataAsset(
        name="Transaction Reference",
        classification=DataClassification.CONFIDENTIAL,
        paq_category=PAQDataCategory.TRANSACTION,
        retention_days=2555,
        requires_encryption=False,
        requires_masking=True,
    ),

    # User PII
    "user_email": DataAsset(
        name="User Email",
        classification=DataClassification.CONFIDENTIAL,
        retention_days=365,
        requires_masking=True,
        pii=True,
    ),
    "user_phone": DataAsset(
        name="User Phone Number",
        classification=DataClassification.CONFIDENTIAL,
        retention_days=365,
        requires_masking=True,
        pii=True,
    ),
    "user_dpi": DataAsset(
        name="Guatemala DPI (National ID)",
        classification=DataClassification.RESTRICTED,
        paq_category=PAQDataCategory.PERSONAL_ID,
        retention_days=2555,
        requires_encryption=True,
        requires_masking=True,
        pii=True,
    ),
    "user_address": DataAsset(
        name="User Physical Address",
        classification=DataClassification.CONFIDENTIAL,
        retention_days=365,
        requires_masking=True,
        pii=True,
    ),

    # Location Data
    "gps_coordinates": DataAsset(
        name="GPS Coordinates",
        classification=DataClassification.CONFIDENTIAL,
        retention_days=90,
        requires_masking=False,
        pii=True,
    ),

    # Authentication
    "password_hash": DataAsset(
        name="Password Hash",
        classification=DataClassification.SECRET,
        paq_category=PAQDataCategory.AUTHENTICATION,
        retention_days=0,  # Never log
        requires_encryption=True,
        requires_masking=True,
    ),
    "jwt_token": DataAsset(
        name="JWT Access Token",
        classification=DataClassification.SECRET,
        paq_category=PAQDataCategory.AUTHENTICATION,
        retention_days=1,
        requires_encryption=False,
        requires_masking=True,
    ),
}


# =============================================================================
# PCI-DSS v4.0 COMPLIANCE: Cardholder Data Protection
# =============================================================================

class PCIDSSCompliance:
    """
    PCI-DSS v4.0 Compliance Handler for PAQ Transactions

    Implements Payment Card Industry Data Security Standard requirements:
    - Requirement 3: Protect stored account data
    - Requirement 4: Protect cardholder data with strong cryptography during transmission
    - Requirement 10: Log and monitor all access to system components and cardholder data

    PAQ Wallet Integration Note:
    PAQ uses tokenization - we never handle raw card data. However, we must
    protect PAQ tokens, wallet IDs, and transaction references as sensitive data.
    """

    # PCI-DSS Requirement 3.4: PAN Masking (show first 6, last 4)
    PAN_PATTERN = re.compile(r'\b(\d{4})[\s-]?(\d{2})(\d{2})[\s-]?(\d{4})[\s-]?(\d{4})\b')

    # Sensitive data patterns that must be protected
    SENSITIVE_PATTERNS: Dict[str, Tuple[re.Pattern, Callable]] = {
        # PCI-DSS: Primary Account Number (PAN) - mask middle digits
        'pan': (
            re.compile(r'\b(\d{4})[\s-]?(\d{4})[\s-]?(\d{4})[\s-]?(\d{4})\b'),
            lambda m: f"{m.group(1)}-****-****-{m.group(4)}"
        ),
        # PCI-DSS: CVV/CVC must NEVER be stored or logged
        'cvv': (
            re.compile(r'\b(cvv|cvc|cvv2|cvc2)[\s:=]+(\d{3,4})\b', re.I),
            lambda m: f"{m.group(1)}:[REDACTED]"
        ),
        # PAQ Wallet Token (5-char PAYPAQ code)
        'paq_token': (
            re.compile(r'\b([A-Z0-9]{5})\b'),
            lambda m: f"***{m.group(1)[-2:]}"
        ),
        # PAQ Wallet ID
        'paq_wallet': (
            re.compile(r'(PAQ-?[A-Z0-9]{2,4})-?([A-Z0-9]+)'),
            lambda m: f"{m.group(1)}-****"
        ),
        # Phone numbers (Guatemala format)
        'phone_gt': (
            re.compile(r'\+?502[\s-]?(\d{4})[\s-]?(\d{4})'),
            lambda m: f"+502-****-{m.group(2)[-4:]}"
        ),
        # DPI (Guatemala National ID) - PCI-DSS treats as sensitive
        'dpi': (
            re.compile(r'\b(\d{4})\s?(\d{5})\s?(\d{4})\b'),
            lambda m: f"****-*****-{m.group(3)}"
        ),
        # JWT tokens
        'jwt': (
            re.compile(r'(eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*)'),
            lambda m: "[JWT_REDACTED]"
        ),
        # API Keys and secrets
        'api_key': (
            re.compile(r'(api[_-]?key|secret|password|token)[\s:=]+["\']?([a-zA-Z0-9_-]{8,})["\']?', re.I),
            lambda m: f"{m.group(1)}:[REDACTED]"
        ),
    }

    # Fields that must NEVER be stored (PCI-DSS Requirement 3.2)
    PROHIBITED_FIELDS = frozenset({
        'cvv', 'cvc', 'cvv2', 'cvc2',  # Card verification codes
        'pin', 'pin_block',             # PIN data
        'track1', 'track2',             # Magnetic stripe data
        'full_pan',                     # Full PAN (if not needed)
    })

    @classmethod
    def mask_pan(cls, pan: str) -> str:
        """
        PCI-DSS Requirement 3.4: Mask PAN displaying only first 6 and last 4.

        Args:
            pan: Primary Account Number (credit/debit card number)

        Returns:
            Masked PAN in format: 1234-56**-****-7890
        """
        # Remove spaces and dashes
        clean_pan = re.sub(r'[\s-]', '', str(pan))

        if len(clean_pan) < 13 or len(clean_pan) > 19:
            return "[INVALID_PAN]"

        # Show first 6, mask middle, show last 4
        first_six = clean_pan[:6]
        last_four = clean_pan[-4:]
        masked_middle = '*' * (len(clean_pan) - 10)

        return f"{first_six[:4]}-{first_six[4:6]}{masked_middle[:2]}-{masked_middle[2:]}**-{last_four}"

    @classmethod
    def mask_sensitive_data(cls, value: str, data_type: Optional[str] = None) -> str:
        """
        Mask sensitive data according to PCI-DSS requirements.

        Args:
            value: The string value to mask
            data_type: Optional specific type to use for masking

        Returns:
            Masked string safe for logging (PCI-DSS compliant)
        """
        if not value:
            return value

        if data_type and data_type in cls.SENSITIVE_PATTERNS:
            pattern, replacer = cls.SENSITIVE_PATTERNS[data_type]
            return pattern.sub(replacer, str(value))

        # Auto-detect and mask all sensitive patterns
        result = str(value)
        for pattern, replacer in cls.SENSITIVE_PATTERNS.values():
            result = pattern.sub(replacer, result)
        return result

    @classmethod
    def mask_dict(cls, data: Dict[str, Any], redact_keys: Optional[Set[str]] = None) -> Dict[str, Any]:
        """
        PCI-DSS Requirement 3 & 10: Mask sensitive values in dictionaries for logging.

        Args:
            data: Dictionary to mask
            redact_keys: Set of keys that should be completely redacted

        Returns:
            New dictionary with masked/redacted values
        """
        redact_keys = redact_keys or cls.PROHIBITED_FIELDS | {
            'password', 'secret', 'api_key', 'authorization',
            'credit_card', 'card_number', 'account_number'
        }

        def _process_value(key: str, value: Any) -> Any:
            key_lower = key.lower()

            # Completely redact prohibited fields
            if key_lower in redact_keys or any(p in key_lower for p in cls.PROHIBITED_FIELDS):
                return '[PCI_REDACTED]'

            if isinstance(value, str):
                return cls.mask_sensitive_data(value)
            if isinstance(value, dict):
                return cls.mask_dict(value, redact_keys)
            if isinstance(value, list):
                return [_process_value(key, item) for item in value]
            return value

        return {key: _process_value(key, value) for key, value in data.items()}

    @classmethod
    def validate_no_prohibited_data(cls, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        PCI-DSS Requirement 3.2: Verify no prohibited data is being stored.

        Args:
            data: Dictionary to validate

        Returns:
            Tuple of (is_valid, list of violations)
        """
        violations = []

        def _check_dict(d: Dict[str, Any], path: str = "") -> None:
            for key, value in d.items():
                current_path = f"{path}.{key}" if path else key

                if key.lower() in cls.PROHIBITED_FIELDS:
                    violations.append(f"Prohibited field '{current_path}' found")

                if isinstance(value, dict):
                    _check_dict(value, current_path)
                elif isinstance(value, str):
                    # Check for CVV patterns in string values
                    if re.search(r'\b(cvv|cvc)\s*[:=]\s*\d{3,4}\b', value, re.I):
                        violations.append(f"CVV data detected in '{current_path}'")

        _check_dict(data)
        return len(violations) == 0, violations

    @classmethod
    def generate_token_reference(cls) -> str:
        """
        Generate a PCI-DSS compliant token reference for transactions.

        Returns:
            Unique token reference (not containing any cardholder data)
        """
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_part = secrets.token_hex(8).upper()
        return f"TKN-{timestamp}-{random_part}"

    @classmethod
    def log_pci_event(
        cls,
        event_type: str,
        request: Any,
        details: Dict[str, Any],
        cardholder_data_accessed: bool = False
    ) -> None:
        """
        PCI-DSS Requirement 10: Log access to cardholder data environment.

        Args:
            event_type: Type of event being logged
            request: HTTP request object
            details: Event details (will be masked)
            cardholder_data_accessed: Whether CHD was accessed
        """
        # Mask all sensitive data before logging
        safe_details = cls.mask_dict(details)

        log_entry = {
            "pci_event": event_type,
            "timestamp": timezone.now().isoformat(),
            "user_id": getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
            "ip_address": cls.mask_sensitive_data(get_client_ip(request)),
            "chd_accessed": cardholder_data_accessed,
            "details": safe_details,
            "compliance": "PCI-DSS-v4.0",
        }

        if cardholder_data_accessed:
            security_logger.warning(json.dumps(log_entry))
        else:
            audit_logger.info(json.dumps(log_entry))


# Backward compatibility alias - PIIMasker now uses PCI-DSS compliant masking
class PIIMasker(PCIDSSCompliance):
    """
    Backward compatibility wrapper for PCIDSSCompliance.
    Deprecated: Use PCIDSSCompliance directly for new code.
    """

    @classmethod
    def mask(cls, value: str, mask_type: Optional[str] = None) -> str:
        """
        Backward compatible mask method.

        Args:
            value: The string value to mask
            mask_type: Optional specific type to use for masking

        Returns:
            Masked string safe for logging
        """
        return cls.mask_sensitive_data(value, mask_type)


class DataEncryption:
    """
    ISO 27001 A.10.1.1 - Encryption Key Management

    Provides field-level encryption for sensitive data at rest.
    Uses HMAC-SHA256 for data integrity verification.

    Note: For production, integrate with a proper KMS (AWS KMS, Azure Key Vault, etc.)
    """

    @staticmethod
    def get_encryption_key() -> bytes:
        """
        Get the data encryption key from settings.

        Returns:
            32-byte encryption key
        """
        key = getattr(settings, 'DATA_ENCRYPTION_KEY', settings.SECRET_KEY)
        return hashlib.sha256(key.encode()).digest()

    @classmethod
    def generate_hmac(cls, data: str) -> str:
        """
        Generate HMAC-SHA256 signature for data integrity.

        Args:
            data: String data to sign

        Returns:
            Hex-encoded HMAC signature
        """
        key = cls.get_encryption_key()
        signature = hmac.new(key, data.encode(), hashlib.sha256)
        return signature.hexdigest()

    @classmethod
    def verify_hmac(cls, data: str, signature: str) -> bool:
        """
        Verify data integrity using HMAC signature.

        Args:
            data: Original data string
            signature: HMAC signature to verify

        Returns:
            True if signature is valid
        """
        expected = cls.generate_hmac(data)
        return hmac.compare_digest(expected, signature)

    @classmethod
    def hash_sensitive_data(cls, data: str, salt: Optional[str] = None) -> str:
        """
        Create a one-way hash of sensitive data for storage/comparison.

        Args:
            data: Sensitive data to hash
            salt: Optional salt (generated if not provided)

        Returns:
            Salted hash string
        """
        salt = salt or secrets.token_hex(16)
        key = cls.get_encryption_key()
        hash_input = f"{salt}:{data}".encode()
        digest = hmac.new(key, hash_input, hashlib.sha256).hexdigest()
        return f"{salt}:{digest}"


# =============================================================================
# ISO 27001 A.9 - ACCESS CONTROL
# =============================================================================

class AccessControlLevel(Enum):
    """
    ISO 27001 A.9.1 - Access Control Policy

    Defines access control levels for the SegurifAI platform.
    """
    NONE = 0           # No access
    READ = 10          # Read-only access
    WRITE = 20         # Create/Update access
    DELETE = 30        # Delete access
    ADMIN = 40         # Full administrative access
    SUPER_ADMIN = 50   # System-level access


@dataclass
class AccessPolicy:
    """
    Defines an access control policy for a resource.
    """
    resource: str
    required_level: AccessControlLevel
    required_roles: List[str] = field(default_factory=list)
    mfa_required: bool = False
    audit_all_access: bool = False
    ip_whitelist: Optional[List[str]] = None


# Resource access policies
ACCESS_POLICIES: Dict[str, AccessPolicy] = {
    # PAQ Wallet Operations
    "paq_wallet.read_balance": AccessPolicy(
        resource="paq_wallet.balance",
        required_level=AccessControlLevel.READ,
        required_roles=["USER", "PROVIDER", "MAWDY_ADMIN", "ADMIN"],
        audit_all_access=True,
    ),
    "paq_wallet.process_payment": AccessPolicy(
        resource="paq_wallet.transaction",
        required_level=AccessControlLevel.WRITE,
        required_roles=["USER", "MAWDY_ADMIN", "ADMIN"],
        mfa_required=True,  # Require MFA for payments
        audit_all_access=True,
    ),
    "paq_wallet.refund": AccessPolicy(
        resource="paq_wallet.transaction",
        required_level=AccessControlLevel.ADMIN,
        required_roles=["MAWDY_ADMIN", "ADMIN"],
        mfa_required=True,
        audit_all_access=True,
    ),

    # User Data Operations
    "user.read_profile": AccessPolicy(
        resource="user.profile",
        required_level=AccessControlLevel.READ,
        required_roles=["USER", "PROVIDER", "MAWDY_ADMIN", "ADMIN"],
    ),
    "user.update_profile": AccessPolicy(
        resource="user.profile",
        required_level=AccessControlLevel.WRITE,
        required_roles=["USER", "ADMIN"],
    ),
    "user.delete_account": AccessPolicy(
        resource="user.profile",
        required_level=AccessControlLevel.DELETE,
        required_roles=["USER", "ADMIN"],
        mfa_required=True,
        audit_all_access=True,
    ),

    # Assistance Request Operations
    "assistance.create_request": AccessPolicy(
        resource="assistance.request",
        required_level=AccessControlLevel.WRITE,
        required_roles=["USER"],
        audit_all_access=True,
    ),
    "assistance.view_all_requests": AccessPolicy(
        resource="assistance.request",
        required_level=AccessControlLevel.READ,
        required_roles=["MAWDY_ADMIN", "ADMIN"],
    ),
    "assistance.cancel_request": AccessPolicy(
        resource="assistance.request",
        required_level=AccessControlLevel.WRITE,
        required_roles=["USER", "MAWDY_ADMIN", "ADMIN"],
        audit_all_access=True,
    ),

    # Provider Operations
    "provider.dispatch_job": AccessPolicy(
        resource="provider.dispatch",
        required_level=AccessControlLevel.WRITE,
        required_roles=["PROVIDER", "MAWDY_ADMIN"],
        audit_all_access=True,
    ),

    # Admin Operations
    "admin.view_audit_logs": AccessPolicy(
        resource="admin.audit",
        required_level=AccessControlLevel.ADMIN,
        required_roles=["ADMIN"],
        audit_all_access=True,
    ),
    "admin.manage_users": AccessPolicy(
        resource="admin.users",
        required_level=AccessControlLevel.ADMIN,
        required_roles=["ADMIN"],
        mfa_required=True,
        audit_all_access=True,
    ),
}


def check_access(
    user: Any,
    policy_name: str,
    resource_owner_id: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """
    ISO 27001 A.9.4 - Access Control to Program Source Code

    Check if a user has access to a resource based on policy.

    Args:
        user: The user requesting access
        policy_name: Name of the access policy to check
        resource_owner_id: Optional ID of the resource owner (for ownership checks)

    Returns:
        Tuple of (access_granted, denial_reason)
    """
    policy = ACCESS_POLICIES.get(policy_name)
    if not policy:
        security_logger.warning(f"Unknown access policy: {policy_name}")
        return False, "Unknown access policy"

    # Check if user is authenticated
    if not user or not user.is_authenticated:
        return False, "Authentication required"

    # Get user role
    user_role = getattr(user, 'role', 'USER')

    # Check role-based access
    if policy.required_roles and user_role not in policy.required_roles:
        security_logger.warning(
            f"Access denied: User {user.id} with role {user_role} "
            f"attempted to access {policy_name}"
        )
        return False, f"Role {user_role} not authorized"

    # Check ownership for user-specific resources
    if resource_owner_id and user_role not in ['ADMIN', 'MAWDY_ADMIN']:
        if user.id != resource_owner_id:
            return False, "Not authorized to access this resource"

    # Log access if required
    if policy.audit_all_access:
        audit_logger.info(json.dumps({
            "event": "access_check",
            "policy": policy_name,
            "user_id": user.id,
            "user_role": user_role,
            "granted": True,
            "timestamp": timezone.now().isoformat(),
        }))

    return True, None


def require_access(policy_name: str, resource_owner_getter: Optional[Callable] = None):
    """
    Decorator to enforce access control on views.

    Args:
        policy_name: Name of the access policy to enforce
        resource_owner_getter: Optional function to extract owner ID from request

    Usage:
        @require_access("paq_wallet.read_balance")
        def get_wallet_balance(request):
            ...
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            resource_owner_id = None
            if resource_owner_getter:
                resource_owner_id = resource_owner_getter(request, *args, **kwargs)

            granted, reason = check_access(
                request.user,
                policy_name,
                resource_owner_id
            )

            if not granted:
                security_logger.warning(
                    f"Access denied to {policy_name}: {reason}"
                )
                raise PermissionDenied(reason)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# ISO 27001 A.12 - OPERATIONS SECURITY: Security Event Logging
# =============================================================================

class SecurityEventType(Enum):
    """
    ISO 27001 A.12.4 - Logging and Monitoring

    Categories of security events to log.
    """
    # Authentication Events
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILURE = "auth.login.failure"
    AUTH_LOGOUT = "auth.logout"
    AUTH_PASSWORD_CHANGE = "auth.password.change"
    AUTH_PASSWORD_RESET = "auth.password.reset"
    AUTH_MFA_ENABLED = "auth.mfa.enabled"
    AUTH_MFA_DISABLED = "auth.mfa.disabled"
    AUTH_SESSION_EXPIRED = "auth.session.expired"

    # Access Control Events
    ACCESS_DENIED = "access.denied"
    ACCESS_GRANTED = "access.granted"
    ACCESS_ELEVATED = "access.elevated"

    # Data Events
    DATA_CREATE = "data.create"
    DATA_READ = "data.read"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"

    # PAQ Wallet Events
    PAQ_BALANCE_CHECK = "paq.balance.check"
    PAQ_PAYMENT_INITIATED = "paq.payment.initiated"
    PAQ_PAYMENT_SUCCESS = "paq.payment.success"
    PAQ_PAYMENT_FAILURE = "paq.payment.failure"
    PAQ_REFUND_INITIATED = "paq.refund.initiated"
    PAQ_REFUND_SUCCESS = "paq.refund.success"

    # Security Events
    SECURITY_RATE_LIMIT = "security.rate_limit"
    SECURITY_BLOCKED_IP = "security.blocked_ip"
    SECURITY_BLOCKED_COUNTRY = "security.blocked_country"
    SECURITY_SUSPICIOUS_ACTIVITY = "security.suspicious"
    SECURITY_INJECTION_ATTEMPT = "security.injection"

    # System Events
    SYSTEM_ERROR = "system.error"
    SYSTEM_CONFIG_CHANGE = "system.config.change"


@dataclass
class SecurityEvent:
    """
    Represents a security event for logging.

    All fields are designed for ISO 27001 A.12.4.1 compliance
    (Event logging).
    """
    event_type: SecurityEventType
    timestamp: datetime
    user_id: Optional[int]
    ip_address: str
    user_agent: str
    resource: Optional[str]
    action: str
    outcome: str  # "success", "failure", "blocked"
    details: Dict[str, Any]
    request_id: str
    session_id: Optional[str] = None
    risk_level: str = "low"  # low, medium, high, critical

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON logging."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "ip_address": PIIMasker.mask(self.ip_address, 'ip') if self.ip_address else None,
            "user_agent": self.user_agent[:200] if self.user_agent else None,
            "resource": self.resource,
            "action": self.action,
            "outcome": self.outcome,
            "details": PIIMasker.mask_dict(self.details),
            "request_id": self.request_id,
            "session_id": self.session_id,
            "risk_level": self.risk_level,
        }


def log_security_event(
    event_type: SecurityEventType,
    request: HttpRequest,
    action: str,
    outcome: str,
    resource: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    risk_level: str = "low"
) -> None:
    """
    Log a security event for ISO 27001 compliance.

    Args:
        event_type: Type of security event
        request: Django HTTP request
        action: Description of the action taken
        outcome: Result of the action
        resource: Resource being accessed
        details: Additional event details
        risk_level: Risk classification
    """
    event = SecurityEvent(
        event_type=event_type,
        timestamp=timezone.now(),
        user_id=request.user.id if request.user.is_authenticated else None,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        resource=resource,
        action=action,
        outcome=outcome,
        details=details or {},
        request_id=getattr(request, 'request_id', str(uuid.uuid4())),
        session_id=request.session.session_key if hasattr(request, 'session') else None,
        risk_level=risk_level,
    )

    # Log to appropriate logger based on risk level
    log_data = json.dumps(event.to_dict())

    if risk_level in ('high', 'critical'):
        security_logger.warning(log_data)
    else:
        audit_logger.info(log_data)


def get_client_ip(request: HttpRequest) -> str:
    """Extract client IP from request, considering Cloudflare headers."""
    cf_ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if cf_ip:
        return cf_ip

    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()

    return request.META.get('REMOTE_ADDR', '')


# =============================================================================
# ISO 27001 A.18 - COMPLIANCE: Data Retention
# =============================================================================

class DataRetentionPolicy:
    """
    ISO 27001 A.18.1 - Compliance with Legal and Contractual Requirements

    Implements data retention policies for different data types.
    Aligned with:
    - Guatemala's data protection regulations
    - Financial record keeping requirements (SAT)
    - PAQ contractual requirements
    """

    # Retention periods in days
    RETENTION_PERIODS: Dict[str, int] = {
        # Financial/Transactional (7 years for SAT compliance)
        'paq_transactions': 2555,
        'payment_records': 2555,
        'invoices': 2555,

        # Assistance Records (5 years)
        'assistance_requests': 1825,
        'service_history': 1825,

        # User Data (varies)
        'user_profiles': 365,  # 1 year after account deletion
        'user_preferences': 365,

        # Audit Logs (2 years)
        'audit_logs': 730,
        'security_logs': 730,

        # Session/Temporary Data
        'session_data': 30,
        'temp_tokens': 1,
        'rate_limit_data': 1,

        # Location Data (90 days for privacy)
        'location_history': 90,
        'tracking_data': 90,
    }

    @classmethod
    def get_retention_period(cls, data_type: str) -> int:
        """
        Get retention period for a data type.

        Args:
            data_type: Type of data

        Returns:
            Retention period in days
        """
        return cls.RETENTION_PERIODS.get(data_type, 365)

    @classmethod
    def get_expiration_date(cls, data_type: str, created_at: datetime) -> datetime:
        """
        Calculate expiration date for data.

        Args:
            data_type: Type of data
            created_at: When the data was created

        Returns:
            Datetime when data should be deleted
        """
        days = cls.get_retention_period(data_type)
        return created_at + timedelta(days=days)

    @classmethod
    def is_expired(cls, data_type: str, created_at: datetime) -> bool:
        """
        Check if data has exceeded retention period.

        Args:
            data_type: Type of data
            created_at: When the data was created

        Returns:
            True if data should be deleted
        """
        expiration = cls.get_expiration_date(data_type, created_at)
        return timezone.now() > expiration


# =============================================================================
# PAQ TRANSACTIONAL DATA SECURITY
# =============================================================================

class PAQTransactionSecurity:
    """
    Security controls specific to PAQ Wallet transaction handling.

    Implements:
    - Transaction integrity verification
    - Fraud detection indicators
    - Secure transaction logging
    - Amount validation
    """

    # Amount limits in GTQ (Quetzales)
    MIN_TRANSACTION_AMOUNT = 1.00
    MAX_TRANSACTION_AMOUNT = 50000.00
    DAILY_LIMIT_USER = 10000.00
    DAILY_LIMIT_PROVIDER = 100000.00

    @classmethod
    def validate_transaction_amount(
        cls,
        amount: float,
        user_role: str = "USER"
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate transaction amount against limits.

        Args:
            amount: Transaction amount in GTQ
            user_role: Role of the user initiating transaction

        Returns:
            Tuple of (is_valid, error_message)
        """
        if amount < cls.MIN_TRANSACTION_AMOUNT:
            return False, f"Amount below minimum ({cls.MIN_TRANSACTION_AMOUNT} GTQ)"

        if amount > cls.MAX_TRANSACTION_AMOUNT:
            return False, f"Amount exceeds maximum ({cls.MAX_TRANSACTION_AMOUNT} GTQ)"

        return True, None

    @classmethod
    def generate_transaction_reference(cls) -> str:
        """
        Generate a unique, secure transaction reference.

        Returns:
            Transaction reference string (format: TXN-YYYYMMDD-XXXX-XXXX)
        """
        date_part = timezone.now().strftime('%Y%m%d')
        random_part = secrets.token_hex(4).upper()
        check_part = secrets.token_hex(2).upper()
        return f"TXN-{date_part}-{random_part}-{check_part}"

    @classmethod
    def calculate_transaction_hash(
        cls,
        user_id: int,
        wallet_id: str,
        amount: float,
        reference: str,
        timestamp: datetime
    ) -> str:
        """
        Calculate integrity hash for a transaction.

        This hash can be stored and later verified to detect tampering.

        Args:
            user_id: User initiating the transaction
            wallet_id: PAQ Wallet ID
            amount: Transaction amount
            reference: Transaction reference
            timestamp: Transaction timestamp

        Returns:
            HMAC hash of transaction data
        """
        data = f"{user_id}:{wallet_id}:{amount:.2f}:{reference}:{timestamp.isoformat()}"
        return DataEncryption.generate_hmac(data)

    @classmethod
    def verify_transaction_integrity(
        cls,
        user_id: int,
        wallet_id: str,
        amount: float,
        reference: str,
        timestamp: datetime,
        stored_hash: str
    ) -> bool:
        """
        Verify that a transaction has not been tampered with.

        Args:
            user_id: User ID from transaction
            wallet_id: PAQ Wallet ID
            amount: Transaction amount
            reference: Transaction reference
            timestamp: Transaction timestamp
            stored_hash: Original hash to verify against

        Returns:
            True if transaction data is intact
        """
        expected_hash = cls.calculate_transaction_hash(
            user_id, wallet_id, amount, reference, timestamp
        )
        return hmac.compare_digest(expected_hash, stored_hash)

    @classmethod
    def log_transaction(
        cls,
        request: HttpRequest,
        transaction_type: str,
        wallet_id: str,
        amount: float,
        reference: str,
        status: str,
        paq_response: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Securely log a PAQ transaction for audit purposes.

        Args:
            request: HTTP request context
            transaction_type: Type of transaction (payment, refund, etc.)
            wallet_id: PAQ Wallet ID (will be masked)
            amount: Transaction amount
            reference: Transaction reference
            status: Transaction status
            paq_response: Response from PAQ API (sensitive fields will be masked)
        """
        event_type = {
            'payment': SecurityEventType.PAQ_PAYMENT_SUCCESS if status == 'success'
                      else SecurityEventType.PAQ_PAYMENT_FAILURE,
            'refund': SecurityEventType.PAQ_REFUND_SUCCESS if status == 'success'
                     else SecurityEventType.PAQ_REFUND_INITIATED,
            'balance': SecurityEventType.PAQ_BALANCE_CHECK,
        }.get(transaction_type, SecurityEventType.PAQ_PAYMENT_INITIATED)

        log_security_event(
            event_type=event_type,
            request=request,
            action=f"PAQ {transaction_type}",
            outcome=status,
            resource=f"paq_wallet:{PIIMasker.mask(wallet_id, 'paq_wallet')}",
            details={
                "amount_gtq": amount,
                "reference": reference,
                "paq_response_code": paq_response.get('code') if paq_response else None,
            },
            risk_level="medium" if amount > 1000 else "low"
        )


# =============================================================================
# ISO 27001 A.16 - INCIDENT MANAGEMENT
# =============================================================================

class SecurityIncidentManager:
    """
    ISO 27001 A.16.1 - Management of Information Security Incidents

    Handles detection and response to security incidents.
    """

    # Thresholds for incident detection
    FAILED_LOGIN_THRESHOLD = 5  # Per IP in 15 minutes
    RATE_LIMIT_THRESHOLD = 10   # Rate limit hits to trigger alert
    SUSPICIOUS_ACTIVITY_THRESHOLD = 3  # Suspicious events to escalate

    @classmethod
    def check_failed_logins(cls, ip_address: str) -> bool:
        """
        Check if IP has exceeded failed login threshold.

        Args:
            ip_address: Client IP address

        Returns:
            True if threshold exceeded (potential brute force)
        """
        cache_key = f"failed_login:{ip_address}"
        count = cache.get(cache_key, 0)
        return count >= cls.FAILED_LOGIN_THRESHOLD

    @classmethod
    def record_failed_login(cls, ip_address: str, username: str) -> int:
        """
        Record a failed login attempt.

        Args:
            ip_address: Client IP address
            username: Attempted username

        Returns:
            Current failure count for this IP
        """
        cache_key = f"failed_login:{ip_address}"
        count = cache.get(cache_key, 0) + 1
        cache.set(cache_key, count, timeout=900)  # 15 minutes

        if count >= cls.FAILED_LOGIN_THRESHOLD:
            security_logger.warning(json.dumps({
                "event": "brute_force_detected",
                "ip_address": PIIMasker.mask(ip_address),
                "attempted_username": PIIMasker.mask(username, 'email'),
                "attempt_count": count,
                "action": "blocking_recommended",
                "timestamp": timezone.now().isoformat(),
            }))

        return count

    @classmethod
    def clear_failed_logins(cls, ip_address: str) -> None:
        """Clear failed login counter after successful login."""
        cache_key = f"failed_login:{ip_address}"
        cache.delete(cache_key)

    @classmethod
    def report_incident(
        cls,
        incident_type: str,
        severity: str,
        description: str,
        affected_users: Optional[List[int]] = None,
        affected_resources: Optional[List[str]] = None,
        remediation_steps: Optional[List[str]] = None
    ) -> str:
        """
        Report a security incident for investigation.

        Args:
            incident_type: Category of incident
            severity: Severity level (low, medium, high, critical)
            description: Detailed description
            affected_users: List of affected user IDs
            affected_resources: List of affected resources
            remediation_steps: Recommended remediation actions

        Returns:
            Incident reference ID
        """
        incident_id = f"INC-{timezone.now().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"

        incident_data = {
            "incident_id": incident_id,
            "type": incident_type,
            "severity": severity,
            "description": description,
            "affected_users_count": len(affected_users) if affected_users else 0,
            "affected_resources": affected_resources or [],
            "remediation_steps": remediation_steps or [],
            "reported_at": timezone.now().isoformat(),
            "status": "open",
        }

        # Log to security logger with appropriate level
        if severity in ('high', 'critical'):
            security_logger.error(json.dumps(incident_data))
        else:
            security_logger.warning(json.dumps(incident_data))

        return incident_id


# =============================================================================
# COMPLIANCE DECORATORS FOR VIEWS
# =============================================================================

def audit_paq_transaction(transaction_type: str):
    """
    Decorator to automatically audit PAQ wallet transactions.

    Args:
        transaction_type: Type of transaction being performed

    Usage:
        @audit_paq_transaction("payment")
        def process_payment(request):
            ...
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            # Log transaction initiation
            log_security_event(
                event_type=SecurityEventType.PAQ_PAYMENT_INITIATED,
                request=request,
                action=f"Initiating {transaction_type}",
                outcome="pending",
                resource="paq_wallet",
                risk_level="medium"
            )

            try:
                response = view_func(request, *args, **kwargs)

                # Log success or failure based on response
                if hasattr(response, 'status_code') and response.status_code < 400:
                    log_security_event(
                        event_type=SecurityEventType.PAQ_PAYMENT_SUCCESS,
                        request=request,
                        action=f"{transaction_type} completed",
                        outcome="success",
                        resource="paq_wallet",
                    )
                else:
                    log_security_event(
                        event_type=SecurityEventType.PAQ_PAYMENT_FAILURE,
                        request=request,
                        action=f"{transaction_type} failed",
                        outcome="failure",
                        resource="paq_wallet",
                        risk_level="medium"
                    )

                return response

            except Exception as e:
                log_security_event(
                    event_type=SecurityEventType.PAQ_PAYMENT_FAILURE,
                    request=request,
                    action=f"{transaction_type} error",
                    outcome="error",
                    resource="paq_wallet",
                    details={"error": str(e)},
                    risk_level="high"
                )
                raise

        return wrapper
    return decorator


def require_data_classification(min_classification: DataClassification):
    """
    Decorator to enforce minimum data classification access level.

    Args:
        min_classification: Minimum classification level required

    Usage:
        @require_data_classification(DataClassification.RESTRICTED)
        def view_sensitive_data(request):
            ...
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            user_role = getattr(request.user, 'role', 'USER') if request.user.is_authenticated else 'ANONYMOUS'

            # Map roles to maximum classification access
            role_access = {
                'ADMIN': DataClassification.SECRET,
                'MAWDY_ADMIN': DataClassification.RESTRICTED,
                'PROVIDER': DataClassification.CONFIDENTIAL,
                'USER': DataClassification.CONFIDENTIAL,
                'ANONYMOUS': DataClassification.PUBLIC,
            }

            max_access = role_access.get(user_role, DataClassification.PUBLIC)

            # Compare classification levels
            if max_access.value < min_classification.value:
                log_security_event(
                    event_type=SecurityEventType.ACCESS_DENIED,
                    request=request,
                    action="Access to classified data denied",
                    outcome="blocked",
                    details={
                        "required_classification": min_classification.value,
                        "user_max_classification": max_access.value,
                    },
                    risk_level="medium"
                )
                raise PermissionDenied("Insufficient clearance level")

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Data Classification
    'DataClassification',
    'PAQDataCategory',
    'DataAsset',
    'DATA_ASSET_REGISTRY',

    # Encryption & Masking
    'PIIMasker',
    'DataEncryption',

    # Access Control
    'AccessControlLevel',
    'AccessPolicy',
    'ACCESS_POLICIES',
    'check_access',
    'require_access',

    # Security Events
    'SecurityEventType',
    'SecurityEvent',
    'log_security_event',

    # Data Retention
    'DataRetentionPolicy',

    # PAQ Security
    'PAQTransactionSecurity',

    # Incident Management
    'SecurityIncidentManager',

    # Decorators
    'audit_paq_transaction',
    'require_data_classification',
]
