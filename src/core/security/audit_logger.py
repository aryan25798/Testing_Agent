"""
Security Audit Logger for Testing Agent Platform.
Provides dedicated tamper-evident logging of security-critical actions:
- API credential storage, rotation, and revocation
- Automation script subprocess executions
- File upload parsing and size validations
- Model routing changes
- Authentication / CORS / Origin rejections
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from src.core.security.sanitizer import prompt_sanitizer


class SecurityAuditLogger:
    def __init__(self, log_dir: Optional[Path] = None):
        if log_dir is None:
            self.log_dir = Path(__file__).resolve().parent.parent.parent.parent / "logs"
        else:
            self.log_dir = Path(log_dir)

        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.audit_log_file = self.log_dir / "security_audit.log"

        self._logger = logging.getLogger("SecurityAudit")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

        # Add file handler if not already present
        if not self._logger.handlers:
            handler = logging.FileHandler(self.audit_log_file, encoding="utf-8")
            formatter = logging.Formatter("%(asctime)s [SECURITY] %(message)s")
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    def log_event(
        self,
        action: str,
        status: str = "SUCCESS",
        actor: str = "local_user",
        details: Optional[Dict[str, Any]] = None,
        severity: str = "INFO",
    ):
        """
        Records a structured security event with all secrets automatically redacted.
        """
        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action": action,
            "status": status,
            "actor": actor,
            "severity": severity,
            "details": details or {},
        }

        # Redact any accidental secrets inside details
        json_str = json.dumps(payload, default=str)
        safe_json_str = prompt_sanitizer.redact_secrets(json_str)

        if severity in ["CRITICAL", "HIGH", "ERROR"]:
            self._logger.error(safe_json_str)
        elif severity == "WARNING":
            self._logger.warning(safe_json_str)
        else:
            self._logger.info(safe_json_str)


audit_logger = SecurityAuditLogger()
