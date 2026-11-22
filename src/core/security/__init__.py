"""
Core Security Module for Testing Agent Platform.
Provides authenticated encryption, audit logging, and input sanitization.
"""

from src.core.security.secrets_manager import secrets_manager, SecretsManager
from src.core.security.audit_logger import audit_logger, SecurityAuditLogger
from src.core.security.sanitizer import prompt_sanitizer, PromptSanitizer

__all__ = [
    "secrets_manager",
    "SecretsManager",
    "audit_logger",
    "SecurityAuditLogger",
    "prompt_sanitizer",
    "PromptSanitizer",
]
