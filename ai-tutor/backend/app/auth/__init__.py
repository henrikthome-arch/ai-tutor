"""
Authentication and authorization utilities for the AI Tutor application.
"""

from app.auth.decorators import require_token_scope, token_or_session_auth