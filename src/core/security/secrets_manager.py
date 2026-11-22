"""
Encrypted Local Secrets Vault for Testing Agent Platform.
Provides authenticated encryption at rest (AES-256-GCM) for sensitive credentials
(Gemini API Key, OpenAI API Key, GitHub PAT, Jira API Token).
Raw secrets are NEVER written to .env, SQLite plaintext columns, or logs.
"""

import os
import json
import base64
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from src.core.logging import get_logger

logger = get_logger("secrets_manager")


class SecretsManager:
    """
    AES-256-GCM Encrypted Local Secret Store.
    Encrypted data is stored in data/.secrets_vault.enc.
    Master key is loaded from APP_MASTER_KEY or stored in data/.master.key.
    """

    SALT = b"TestingAgentPlatformVaultSalt_2026_Secure"

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            # testing-agent-platform/data
            self.data_dir = Path(__file__).resolve().parent.parent.parent.parent / "data"
        else:
            self.data_dir = Path(data_dir)

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.master_key_file = self.data_dir / ".master.key"
        self.vault_file = self.data_dir / ".secrets_vault.enc"
        self._lock = threading.Lock()
        self._cache: Dict[str, str] = {}
        self._key = self._initialize_key()
        self._load_vault()

    def _initialize_key(self) -> bytes:
        """Derives or retrieves a 256-bit AES-GCM encryption key."""
        env_master = os.environ.get("APP_MASTER_KEY")
        if env_master:
            return self._derive_key(env_master.encode("utf-8"))

        if self.master_key_file.exists():
            try:
                raw_bytes = self.master_key_file.read_bytes().strip()
                if len(raw_bytes) == 32:
                    return raw_bytes
                return self._derive_key(raw_bytes)
            except Exception as e:
                logger.error(f"Error reading master key: {e}. Generating new key.")

        # Generate a new 256-bit cryptographic key
        new_key = AESGCM.generate_key(bit_length=256)
        try:
            self.master_key_file.write_bytes(new_key)
            # Try to restrict file permissions if on POSIX
            try:
                os.chmod(self.master_key_file, 0o600)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Could not write master key file: {e}")

        return new_key

    def _derive_key(self, secret: bytes) -> bytes:
        """Derives 256-bit key using HKDF-SHA256."""
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.SALT,
            info=b"testing-agent-platform-vault-v1",
        )
        return hkdf.derive(secret)

    def _load_vault(self):
        """Loads and decrypts the secrets vault into memory."""
        if not self.vault_file.exists():
            self._cache = {}
            return

        try:
            encrypted_payload = json.loads(self.vault_file.read_text(encoding="utf-8"))
            nonce = base64.b64decode(encrypted_payload["nonce"])
            ciphertext = base64.b64decode(encrypted_payload["ciphertext"])

            aesgcm = AESGCM(self._key)
            decrypted = aesgcm.decrypt(nonce, ciphertext, None)
            self._cache = json.loads(decrypted.decode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to decrypt secrets vault: {e}. Vault may be corrupted or key changed.")
            self._cache = {}

    def _save_vault(self):
        """Encrypts in-memory cache and persists to disk atomically."""
        aesgcm = AESGCM(self._key)
        nonce = os.urandom(12)  # 96-bit standard nonce for GCM
        raw_json = json.dumps(self._cache).encode("utf-8")
        ciphertext = aesgcm.encrypt(nonce, raw_json, None)

        payload = {
            "nonce": base64.b64encode(nonce).decode("utf-8"),
            "ciphertext": base64.b64encode(ciphertext).decode("utf-8"),
        }

        # Write to temporary file first then replace atomically
        tmp_vault = self.vault_file.with_suffix(".tmp")
        tmp_vault.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp_vault.replace(self.vault_file)
        try:
            os.chmod(self.vault_file, 0o600)
        except Exception:
            pass

    def store_secret(self, key_name: str, secret_value: str):
        """Encrypts and securely stores a secret."""
        if not key_name or not secret_value:
            raise ValueError("Secret key and value must be non-empty strings.")

        with self._lock:
            self._cache[key_name.strip().lower()] = secret_value.strip()
            self._save_vault()
            logger.info(f"Securely stored secret for '{key_name}' in encrypted vault.")

    def get_secret(self, key_name: str) -> Optional[str]:
        """Retrieves and decrypts a secret from the vault."""
        with self._lock:
            return self._cache.get(key_name.strip().lower())

    def delete_secret(self, key_name: str) -> bool:
        """Removes a secret from the vault and persists."""
        norm_key = key_name.strip().lower()
        with self._lock:
            if norm_key in self._cache:
                del self._cache[norm_key]
                self._save_vault()
                logger.info(f"Deleted secret '{norm_key}' from encrypted vault.")
                return True
            return False

    def is_configured(self, key_name: str) -> bool:
        """Checks if a secret exists without decrypting or exposing it."""
        norm_key = key_name.strip().lower()
        with self._lock:
            val = self._cache.get(norm_key)
            return bool(val and len(val.strip()) > 0)

    @staticmethod
    def mask_secret(secret_value: Optional[str]) -> Optional[str]:
        """
        Safely masks secret for UI verification (e.g., 'AIzaSy...7x9Q').
        Never exposes the full key.
        """
        if not secret_value:
            return None
        secret_str = str(secret_value).strip()
        if len(secret_str) <= 8:
            return "****"
        if len(secret_str) <= 16:
            return f"{secret_str[:3]}...{secret_str[-3:]}"
        return f"{secret_str[:6]}...{secret_str[-4:]}"

    def get_status(self, key_name: str) -> Dict[str, Any]:
        """Returns safe status metadata for a credential (never the raw key)."""
        norm_key = key_name.strip().lower()
        with self._lock:
            val = self._cache.get(norm_key)
            is_set = bool(val and len(val.strip()) > 0)
            return {
                "key_name": norm_key,
                "is_configured": is_set,
                "masked": self.mask_secret(val) if is_set else None,
            }

    def list_status(self) -> Dict[str, Dict[str, Any]]:
        """Returns status for all known standard credentials."""
        known_keys = ["gemini", "openai", "github", "jira"]
        return {k: self.get_status(k) for k in known_keys}


# Global singleton instance
secrets_manager = SecretsManager()
