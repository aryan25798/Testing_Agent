"""
Custom Platform Exceptions for Testing Agent Platform.
"""

from typing import Any, Optional, Dict


class TestingPlatformException(Exception):
    """Base exception for all platform errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ResourceNotFoundError(TestingPlatformException):
    """Raised when a requested resource is not found."""
    pass


class ValidationError(TestingPlatformException):
    """Raised when input validation fails."""
    pass


class AuthenticationError(TestingPlatformException):
    """Raised when authentication fails."""
    pass


class AuthorizationError(TestingPlatformException):
    """Raised when an operation is forbidden."""
    pass


class AgentExecutionError(TestingPlatformException):
    """Raised when an AI agent fails to complete its task."""
    pass


class IntegrationError(TestingPlatformException):
    """Raised when third-party integration (Jira, Git, MCP) fails."""
    pass


class ApprovalRequiredError(TestingPlatformException):
    """Raised when an action requires human approval before proceeding."""
    pass


class SandboxExecutionError(TestingPlatformException):
    """Raised when test automation execution in isolated sandbox fails."""
    pass


class ModelNotAvailableError(TestingPlatformException):
    """Raised when a requested AI model or provider is inaccessible."""
    pass


class ProviderUnavailableError(TestingPlatformException):
    """Raised when an LLM provider API is unreachable or returns a service error."""
    pass


class LLMGenerationError(TestingPlatformException):
    """Raised when an LLM provider fails to generate a response."""
    pass


class ProviderAuthenticationError(TestingPlatformException):
    """Raised when authentication with an LLM provider fails (invalid or missing API key)."""
    pass


class WorkflowExecutionTimeoutError(TestingPlatformException):
    """Raised when an automated testing workflow exceeds the allotted execution timeout."""
    pass


class CodeSafetyViolationError(TestingPlatformException):
    """Raised when generated test code violates safety rules or attempts prohibited operations."""
    pass
