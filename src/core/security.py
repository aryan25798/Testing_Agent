"""
Security utilities for secret masking, path traversal prevention, and hashing.
"""

import hashlib
import re
from pathlib import Path
from src.core.exceptions import ValidationError


def mask_secret(secret: str, show_chars: int = 4) -> str:
    """Masks a secret string, leaving only the last few characters visible."""
    if not secret:
        return ""
    if len(secret) <= show_chars:
        return "*" * len(secret)
    return "*" * (len(secret) - show_chars) + secret[-show_chars:]


def sanitize_path(base_dir: Path, target_path: str) -> Path:
    """
    Prevents directory traversal attacks by resolving and validating
    that the target path remains strictly within base_dir.
    """
    resolved_base = base_dir.resolve()
    resolved_target = (resolved_base / target_path).resolve()

    try:
        resolved_target.relative_to(resolved_base)
    except ValueError:
        raise ValidationError(f"Security Alert: Path traversal attempt detected: {target_path}")

    return resolved_target


def calculate_content_hash(content: str) -> str:
    """Calculates SHA-256 hash of a text string for integrity verification."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
